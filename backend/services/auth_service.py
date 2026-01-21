"""
Serviço de Autenticação

JWT (JSON Web Token) + bcrypt para hash de senhas

EXPLICAÇÃO SIMPLES:
- bcrypt: Transforma "senha123" em "$2b$12$xyz..." (impossível reverter)
- JWT: Cria um "crachá digital" que expira em X horas
"""
import os
from datetime import datetime, timedelta
from typing import Optional
import re
import unicodedata

import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select

from database import get_session
from models import User, Restaurant


# ============ CONFIGURAÇÕES ============

# Chave secreta para assinar os tokens (MUDAR EM PRODUÇÃO!)
SECRET_KEY = os.environ.get("SECRET_KEY", "motoflash-super-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24  # Token válido por 24 horas


# ============ HASH DE SENHA (bcrypt) ============

def hash_password(password: str) -> str:
    """
    Transforma senha em hash seguro
    
    "senha123" → "$2b$12$LQv3c1yqBw..."
    
    Mesmo se alguém roubar o banco, não consegue
    descobrir a senha original!
    """
    # Converte string para bytes
    password_bytes = password.encode('utf-8')
    # Gera o salt e faz o hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    # Retorna como string
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se a senha digitada bate com o hash salvo
    
    verify_password("senha123", "$2b$12$LQv3c1yqBw...") → True ou False
    """
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


# ============ JWT (Token) ============

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Cria um token JWT
    
    O token é como um "crachá digital" que contém:
    - ID do usuário
    - ID do restaurante
    - Data de expiração
    
    É assinado com nossa chave secreta, então não dá pra falsificar.
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """
    Decodifica e valida um token JWT
    
    Retorna os dados do token ou levanta exceção se inválido/expirado.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ============ DEPENDÊNCIAS FASTAPI ============

# Extrator de token do header Authorization
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session)
) -> User:
    """
    Dependência que extrai o usuário do token
    
    Uso nas rotas:
    @app.get("/rota-protegida")
    def rota(user: User = Depends(get_current_user)):
        # user é o usuário logado!
    """
    token = credentials.credentials
    payload = decode_token(token)
    
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )
    
    user = session.get(User, user_id)
    if not user or not user.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado ou inativo"
        )
    
    return user


def get_current_restaurant(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Restaurant:
    """
    Dependência que extrai o restaurante do usuário logado
    
    Também verifica se o restaurante está bloqueado!
    """
    restaurant = session.get(Restaurant, user.restaurant_id)
    
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurante não encontrado"
        )
    
    # Verifica se trial expirou e atualiza status de bloqueio
    if restaurant.is_trial_expired() and not restaurant.blocked:
        restaurant.blocked = True
        session.add(restaurant)
        session.commit()
    
    # Se está bloqueado, retorna erro especial
    if restaurant.blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Período de teste expirado. Assine um plano para continuar usando.",
            headers={"X-Blocked-Reason": "trial_expired"}
        )
    
    return restaurant


# ============ FUNÇÕES AUXILIARES ============

def generate_slug(name: str) -> str:
    """
    Gera slug a partir do nome
    
    "Pizzaria do Zé" → "pizzaria-do-ze"
    """
    # Remove acentos
    normalized = unicodedata.normalize('NFD', name)
    without_accents = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    
    # Converte para minúsculo e substitui espaços por hífen
    slug = without_accents.lower().strip()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)  # Remove caracteres especiais
    slug = re.sub(r'-+', '-', slug)           # Remove hífens duplicados
    slug = slug.strip('-')                    # Remove hífens no início/fim
    
    return slug


def generate_unique_slug(session: Session, name: str) -> str:
    """
    Gera slug único (adiciona número se já existir)
    
    "Pizzaria do Zé" → "pizzaria-do-ze"
    Se já existe → "pizzaria-do-ze-2"
    """
    base_slug = generate_slug(name)
    slug = base_slug
    counter = 1
    
    while True:
        existing = session.exec(
            select(Restaurant).where(Restaurant.slug == slug)
        ).first()
        
        if not existing:
            return slug
        
        counter += 1
        slug = f"{base_slug}-{counter}"


def authenticate_user(session: Session, email: str, password: str) -> Optional[User]:
    """
    Autentica usuário por email e senha
    
    Retorna o User se credenciais corretas, None se incorretas.
    """
    user = session.exec(
        select(User).where(User.email == email.lower())
    ).first()
    
    if not user:
        return None
    
    if not verify_password(password, user.password_hash):
        return None
    
    return user