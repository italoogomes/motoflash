"""
Rotas de Autenticação

Endpoints para:
- Cadastro de restaurante (self-service)
- Login
- Verificar token
- Dados do usuário logado
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel import Session, select
from slowapi import Limiter
from slowapi.util import get_remote_address

from database import get_session
from models import (
    Restaurant, User, PlanType, UserRole,
    RestaurantCreate, RestaurantResponse,
    UserResponse, LoginRequest, LoginResponse
)
from services.auth_service import (
    hash_password, authenticate_user, create_access_token,
    generate_unique_slug, get_current_user, get_current_restaurant
)
from services.geocoding_service import geocode_address_detailed


router = APIRouter(prefix="/auth", tags=["Autenticação"])

# Rate Limiter
limiter = Limiter(key_func=get_remote_address)


# ============ CADASTRO ============

@router.post("/register", response_model=LoginResponse)
@limiter.limit("5/minute")  # Máximo 5 cadastros por minuto
def register_restaurant(
    request: Request,
    data: RestaurantCreate,
    session: Session = Depends(get_session)
):
    """
    Cadastra um novo restaurante
    
    Fluxo:
    1. Valida email único
    2. Faz geocoding do endereço → lat/lng
    3. Cria Restaurant com trial de 14 dias
    4. Cria User (owner) com senha hasheada
    5. Retorna token JWT para login automático
    """
    
    # 1. Verifica se email já existe
    existing_user = session.exec(
        select(User).where(User.email == data.email.lower())
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este email já está cadastrado"
        )
    
    existing_restaurant = session.exec(
        select(Restaurant).where(Restaurant.email == data.email.lower())
    ).first()
    
    if existing_restaurant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este email já está cadastrado"
        )
    
    # 2. Geocoding do endereço
    lat, lng = None, None
    if data.address:
        geo_result = geocode_address_detailed(data.address)
        if geo_result.get("lat") and geo_result.get("lng"):
            lat = geo_result["lat"]
            lng = geo_result["lng"]
    
    # 3. Gera slug único
    slug = generate_unique_slug(session, data.name)
    
    # 4. Cria o restaurante
    restaurant = Restaurant(
        slug=slug,
        name=data.name,
        email=data.email.lower(),
        phone=data.phone,
        cnpj=data.cnpj,
        address=data.address,
        lat=lat,
        lng=lng,
        plan=PlanType.TRIAL,
        blocked=False
    )
    
    session.add(restaurant)
    session.commit()
    session.refresh(restaurant)
    
    # 5. Cria o usuário (dono)
    user = User(
        name=data.name,  # Usa nome do restaurante como nome do dono inicialmente
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        restaurant_id=restaurant.id,
        role=UserRole.OWNER,
        active=True
    )
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    # 6. Gera token JWT
    token = create_access_token({
        "user_id": user.id,
        "restaurant_id": restaurant.id,
        "email": user.email,
        "role": user.role.value
    })
    
    # 7. Retorna resposta completa
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            restaurant_id=user.restaurant_id,
            role=user.role,
            active=user.active,
            created_at=user.created_at,
            last_login=user.last_login
        ),
        restaurant=RestaurantResponse(
            id=restaurant.id,
            slug=restaurant.slug,
            name=restaurant.name,
            email=restaurant.email,
            phone=restaurant.phone,
            cnpj=restaurant.cnpj,
            logo_url=restaurant.logo_url,
            address=restaurant.address,
            lat=restaurant.lat,
            lng=restaurant.lng,
            plan=restaurant.plan,
            trial_ends_at=restaurant.trial_ends_at,
            blocked=restaurant.blocked,
            days_remaining=restaurant.days_remaining(),
            created_at=restaurant.created_at
        )
    )


# ============ LOGIN ============

@router.post("/login", response_model=LoginResponse)
@limiter.limit("10/minute")  # Máximo 10 tentativas de login por minuto
def login(
    request: Request,
    data: LoginRequest,
    session: Session = Depends(get_session)
):
    """
    Faz login e retorna token JWT
    """
    
    # 1. Autentica
    user = authenticate_user(session, data.email, data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos"
        )
    
    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário desativado"
        )
    
    # 2. Busca restaurante
    restaurant = session.get(Restaurant, user.restaurant_id)
    
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurante não encontrado"
        )
    
    # 3. Verifica se trial expirou
    if restaurant.is_trial_expired() and not restaurant.blocked:
        restaurant.blocked = True
        session.add(restaurant)
        session.commit()
    
    # 4. Atualiza último login
    user.last_login = datetime.now()
    session.add(user)
    session.commit()
    
    # 5. Gera token
    token = create_access_token({
        "user_id": user.id,
        "restaurant_id": restaurant.id,
        "email": user.email,
        "role": user.role.value
    })
    
    # 6. Retorna (mesmo que bloqueado - o frontend decide o que fazer)
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            restaurant_id=user.restaurant_id,
            role=user.role,
            active=user.active,
            created_at=user.created_at,
            last_login=user.last_login
        ),
        restaurant=RestaurantResponse(
            id=restaurant.id,
            slug=restaurant.slug,
            name=restaurant.name,
            email=restaurant.email,
            phone=restaurant.phone,
            cnpj=restaurant.cnpj,
            logo_url=restaurant.logo_url,
            address=restaurant.address,
            lat=restaurant.lat,
            lng=restaurant.lng,
            plan=restaurant.plan,
            trial_ends_at=restaurant.trial_ends_at,
            blocked=restaurant.blocked,
            days_remaining=restaurant.days_remaining(),
            created_at=restaurant.created_at
        )
    )


# ============ VERIFICAR TOKEN ============

@router.get("/me", response_model=LoginResponse)
def get_me(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Retorna dados do usuário logado
    
    Útil para:
    - Verificar se token ainda é válido
    - Obter dados atualizados do usuário/restaurante
    """
    restaurant = session.get(Restaurant, user.restaurant_id)
    
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurante não encontrado"
        )
    
    # Atualiza status de bloqueio se necessário
    if restaurant.is_trial_expired() and not restaurant.blocked:
        restaurant.blocked = True
        session.add(restaurant)
        session.commit()
    
    # Gera novo token (refresh)
    token = create_access_token({
        "user_id": user.id,
        "restaurant_id": restaurant.id,
        "email": user.email,
        "role": user.role.value
    })
    
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            restaurant_id=user.restaurant_id,
            role=user.role,
            active=user.active,
            created_at=user.created_at,
            last_login=user.last_login
        ),
        restaurant=RestaurantResponse(
            id=restaurant.id,
            slug=restaurant.slug,
            name=restaurant.name,
            email=restaurant.email,
            phone=restaurant.phone,
            cnpj=restaurant.cnpj,
            logo_url=restaurant.logo_url,
            address=restaurant.address,
            lat=restaurant.lat,
            lng=restaurant.lng,
            plan=restaurant.plan,
            trial_ends_at=restaurant.trial_ends_at,
            blocked=restaurant.blocked,
            days_remaining=restaurant.days_remaining(),
            created_at=restaurant.created_at
        )
    )


# ============ VERIFICAR EMAIL DISPONÍVEL ============

@router.get("/check-email")
def check_email(email: str, session: Session = Depends(get_session)):
    """
    Verifica se email está disponível para cadastro
    
    Útil para validação em tempo real no formulário.
    """
    existing = session.exec(
        select(User).where(User.email == email.lower())
    ).first()
    
    return {
        "email": email,
        "available": existing is None
    }
