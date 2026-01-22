"""
Rotas de Convites para Motoboys

Fluxo:
1. POST /invites → Dono cria convite (autenticado)
2. GET /invites/{code}/validate → Verifica se código é válido
3. POST /invites/{code}/use → Motoboy usa convite (cria conta)
4. GET /invites → Lista convites do restaurante (autenticado)
"""
import secrets
import string
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select

from database import get_session
from models import (
    Invite, Restaurant, Courier, CourierStatus,
    InviteResponse, InviteUse, InviteValidation
)
from services.auth_service import get_current_user, get_current_restaurant
from models import User


router = APIRouter(prefix="/invites", tags=["Convites"])


def generate_invite_code(length: int = 8) -> str:
    """
    Gera código único para convite
    
    Formato: 8 caracteres alfanuméricos (ex: "abc12def")
    Evita caracteres confusos: 0, O, l, 1, I
    """
    # Caracteres permitidos (sem confusos)
    alphabet = string.ascii_lowercase + string.digits
    alphabet = alphabet.replace('0', '').replace('o', '').replace('l', '').replace('1', '')
    
    return ''.join(secrets.choice(alphabet) for _ in range(length))


# ============ ROTAS AUTENTICADAS (DONO) ============

@router.post("", response_model=InviteResponse)
def create_invite(
    request: Request,
    user: User = Depends(get_current_user),
    restaurant: Restaurant = Depends(get_current_restaurant),
    session: Session = Depends(get_session)
):
    """
    Cria um novo convite para motoboy
    
    - Gera código único
    - Válido por 24 horas
    - Só pode ser usado 1 vez
    """
    
    # Gera código único
    while True:
        code = generate_invite_code()
        existing = session.exec(
            select(Invite).where(Invite.code == code)
        ).first()
        if not existing:
            break
    
    # Cria o convite
    invite = Invite(
        code=code,
        restaurant_id=restaurant.id
    )
    
    session.add(invite)
    session.commit()
    session.refresh(invite)
    
    # Monta URL do convite
    base_url = str(request.base_url).rstrip('/')
    invite_url = f"{base_url}/convite/{invite.code}"
    
    return InviteResponse(
        id=invite.id,
        code=invite.code,
        restaurant_id=invite.restaurant_id,
        restaurant_name=restaurant.name,
        expires_at=invite.expires_at,
        used=invite.used,
        time_remaining=invite.time_remaining(),
        invite_url=invite_url,
        created_at=invite.created_at
    )


@router.get("", response_model=List[InviteResponse])
def list_invites(
    request: Request,
    user: User = Depends(get_current_user),
    restaurant: Restaurant = Depends(get_current_restaurant),
    session: Session = Depends(get_session)
):
    """
    Lista todos os convites do restaurante
    """
    invites = session.exec(
        select(Invite)
        .where(Invite.restaurant_id == restaurant.id)
        .order_by(Invite.created_at.desc())
    ).all()
    
    base_url = str(request.base_url).rstrip('/')
    
    return [
        InviteResponse(
            id=inv.id,
            code=inv.code,
            restaurant_id=inv.restaurant_id,
            restaurant_name=restaurant.name,
            expires_at=inv.expires_at,
            used=inv.used,
            time_remaining=inv.time_remaining(),
            invite_url=f"{base_url}/convite/{inv.code}",
            created_at=inv.created_at
        )
        for inv in invites
    ]


@router.delete("/{invite_id}")
def delete_invite(
    invite_id: str,
    user: User = Depends(get_current_user),
    restaurant: Restaurant = Depends(get_current_restaurant),
    session: Session = Depends(get_session)
):
    """
    Deleta um convite (só se não foi usado)
    """
    invite = session.get(Invite, invite_id)
    
    if not invite:
        raise HTTPException(status_code=404, detail="Convite não encontrado")
    
    if invite.restaurant_id != restaurant.id:
        raise HTTPException(status_code=403, detail="Convite não pertence ao seu restaurante")
    
    if invite.used:
        raise HTTPException(status_code=400, detail="Não é possível deletar convite já utilizado")
    
    session.delete(invite)
    session.commit()
    
    return {"message": "Convite deletado"}


# ============ ROTAS PÚBLICAS (MOTOBOY) ============

@router.get("/{code}/validate", response_model=InviteValidation)
def validate_invite(code: str, session: Session = Depends(get_session)):
    """
    Valida um código de convite (público)
    
    Motoboy acessa essa rota para verificar se o convite é válido
    antes de preencher o formulário.
    """
    invite = session.exec(
        select(Invite).where(Invite.code == code)
    ).first()
    
    if not invite:
        return InviteValidation(
            valid=False,
            message="Código de convite inválido"
        )
    
    if invite.used:
        return InviteValidation(
            valid=False,
            message="Este convite já foi utilizado"
        )
    
    if datetime.now() > invite.expires_at:
        return InviteValidation(
            valid=False,
            message="Este convite expirou"
        )
    
    # Busca nome do restaurante
    restaurant = session.get(Restaurant, invite.restaurant_id)
    restaurant_name = restaurant.name if restaurant else "Restaurante"
    
    return InviteValidation(
        valid=True,
        restaurant_name=restaurant_name,
        expires_at=invite.expires_at,
        time_remaining=invite.time_remaining(),
        message=f"Convite válido para {restaurant_name}"
    )


@router.post("/{code}/use")
def use_invite(
    code: str,
    data: InviteUse,
    session: Session = Depends(get_session)
):
    """
    Usa um convite para criar conta de motoboy (público)
    
    1. Valida o convite
    2. Cria o Courier vinculado ao restaurante
    3. Marca convite como usado
    4. Retorna dados do motoboy criado
    """
    
    # 1. Busca o convite
    invite = session.exec(
        select(Invite).where(Invite.code == code)
    ).first()
    
    if not invite:
        raise HTTPException(status_code=404, detail="Código de convite inválido")
    
    if invite.used:
        raise HTTPException(status_code=400, detail="Este convite já foi utilizado")
    
    if datetime.now() > invite.expires_at:
        raise HTTPException(status_code=400, detail="Este convite expirou")
    
    # 2. Valida dados
    if not data.name or not data.name.strip():
        raise HTTPException(status_code=400, detail="Nome é obrigatório")
    
    # 3. Cria o motoboy
    courier = Courier(
        name=data.name.strip(),
        phone=data.phone,
        restaurant_id=invite.restaurant_id,
        status=CourierStatus.OFFLINE
    )
    
    session.add(courier)
    session.commit()
    session.refresh(courier)
    
    # 4. Marca convite como usado
    invite.used = True
    invite.used_at = datetime.now()
    invite.used_by_courier_id = courier.id
    
    session.add(invite)
    session.commit()
    
    # 5. Busca nome do restaurante para retorno
    restaurant = session.get(Restaurant, invite.restaurant_id)
    
    return {
        "success": True,
        "message": f"Bem-vindo à equipe, {courier.name}!",
        "courier": {
            "id": courier.id,
            "name": courier.name,
            "phone": courier.phone,
            "restaurant_id": courier.restaurant_id,
            "restaurant_name": restaurant.name if restaurant else "Restaurante"
        }
    }
