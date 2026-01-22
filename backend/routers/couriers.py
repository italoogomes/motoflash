"""
Rotas de Motoqueiros (Couriers)
"""
import secrets
import string
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select

from database import get_session
from models import (
    Courier, CourierCreate, CourierResponse, CourierStatus,
    Batch, BatchStatus, BatchResponse, Order, OrderStatus,
    Restaurant, CourierLoginRequest, CourierLoginResponse,
    PasswordReset
)
from services.dispatch_service import get_courier_current_batch, get_batch_orders
from services.auth_service import hash_password, verify_password

router = APIRouter(prefix="/couriers", tags=["Motoqueiros"])


# ============ AUTENTICAÇÃO DO MOTOBOY ============

@router.post("/login", response_model=CourierLoginResponse)
def courier_login(
    data: CourierLoginRequest,
    session: Session = Depends(get_session)
):
    """
    Login do motoboy
    
    Busca pelo celular e valida a senha.
    Retorna dados do motoboy e do restaurante.
    """
    
    # Normaliza telefone (só números)
    phone_clean = ''.join(filter(str.isdigit, data.phone))
    
    if len(phone_clean) < 10:
        return CourierLoginResponse(
            success=False,
            message="Celular inválido"
        )
    
    # Busca motoboy pelo telefone
    courier = session.exec(
        select(Courier).where(Courier.phone == phone_clean)
    ).first()
    
    if not courier:
        return CourierLoginResponse(
            success=False,
            message="Celular não cadastrado"
        )
    
    # Valida senha
    if not courier.password_hash:
        return CourierLoginResponse(
            success=False,
            message="Conta sem senha. Entre em contato com o restaurante."
        )
    
    if not verify_password(data.password, courier.password_hash):
        return CourierLoginResponse(
            success=False,
            message="Senha incorreta"
        )
    
    # Atualiza último login
    courier.last_login = datetime.now()
    session.add(courier)
    session.commit()
    session.refresh(courier)
    
    # Busca nome do restaurante
    restaurant = session.get(Restaurant, courier.restaurant_id) if courier.restaurant_id else None
    
    return CourierLoginResponse(
        success=True,
        message=f"Bem-vindo, {courier.name}!",
        courier=CourierResponse(
            id=courier.id,
            name=courier.name,
            phone=courier.phone,
            status=courier.status,
            available_since=courier.available_since,
            restaurant_id=courier.restaurant_id
        ),
        restaurant_name=restaurant.name if restaurant else None
    )


# ============ CRUD DE MOTOQUEIROS ============


@router.post("", response_model=CourierResponse)
def create_courier(courier_data: CourierCreate, session: Session = Depends(get_session)):
    """
    Cadastra um novo motoqueiro
    
    O motoqueiro começa OFFLINE por padrão.
    """
    courier = Courier(
        name=courier_data.name,
        phone=courier_data.phone,
        status=CourierStatus.OFFLINE
    )
    
    session.add(courier)
    session.commit()
    session.refresh(courier)
    
    return courier


@router.get("", response_model=List[CourierResponse])
def list_couriers(
    status: CourierStatus = None,
    session: Session = Depends(get_session)
):
    """
    Lista todos os motoqueiros, opcionalmente filtrados por status
    """
    query = select(Courier).order_by(Courier.name)
    
    if status:
        query = query.where(Courier.status == status)
    
    couriers = session.exec(query).all()
    return couriers


@router.get("/{courier_id}", response_model=CourierResponse)
def get_courier(courier_id: str, session: Session = Depends(get_session)):
    """
    Busca um motoqueiro pelo ID
    """
    courier = session.get(Courier, courier_id)
    if not courier:
        raise HTTPException(status_code=404, detail="Motoqueiro não encontrado")
    return courier


@router.post("/{courier_id}/available", response_model=CourierResponse)
def set_courier_available(courier_id: str, session: Session = Depends(get_session)):
    """
    Marca o motoqueiro como DISPONÍVEL
    
    Ele entra na fila para receber pedidos.
    """
    courier = session.get(Courier, courier_id)
    if not courier:
        raise HTTPException(status_code=404, detail="Motoqueiro não encontrado")
    
    courier.status = CourierStatus.AVAILABLE
    courier.available_since = datetime.now()
    courier.updated_at = datetime.now()
    
    session.add(courier)
    session.commit()
    session.refresh(courier)
    
    return courier


@router.post("/{courier_id}/offline", response_model=CourierResponse)
def set_courier_offline(courier_id: str, session: Session = Depends(get_session)):
    """
    Marca o motoqueiro como OFFLINE (fora de serviço)
    """
    courier = session.get(Courier, courier_id)
    if not courier:
        raise HTTPException(status_code=404, detail="Motoqueiro não encontrado")
    
    # Não pode ficar offline se tiver entrega em andamento
    current_batch = get_courier_current_batch(session, courier_id)
    if current_batch:
        raise HTTPException(
            status_code=400,
            detail="Motoqueiro tem entregas pendentes. Finalize antes de sair."
        )
    
    courier.status = CourierStatus.OFFLINE
    courier.available_since = None
    courier.updated_at = datetime.now()
    
    session.add(courier)
    session.commit()
    session.refresh(courier)
    
    return courier


@router.get("/{courier_id}/current-batch", response_model=Optional[BatchResponse])
def get_current_batch(courier_id: str, session: Session = Depends(get_session)):
    """
    Retorna o lote atual do motoqueiro (entregas pendentes)
    
    Se não tiver entregas, retorna null.
    """
    courier = session.get(Courier, courier_id)
    if not courier:
        raise HTTPException(status_code=404, detail="Motoqueiro não encontrado")
    
    batch = get_courier_current_batch(session, courier_id)
    
    if not batch:
        return None
    
    # Busca os pedidos do lote
    orders = get_batch_orders(session, batch.id)
    
    return BatchResponse(
        id=batch.id,
        courier_id=batch.courier_id,
        courier_name=courier.name,
        status=batch.status,
        created_at=batch.created_at,
        orders=[
            {
                "id": o.id,
                "customer_name": o.customer_name,
                "address_text": o.address_text,
                "lat": o.lat,
                "lng": o.lng,
                "prep_type": o.prep_type,
                "status": o.status,
                "created_at": o.created_at,
                "ready_at": o.ready_at,
                "batch_id": o.batch_id,
                "stop_order": o.stop_order
            }
            for o in orders
        ]
    )


@router.post("/{courier_id}/complete-batch", response_model=CourierResponse)
def complete_current_batch(courier_id: str, session: Session = Depends(get_session)):
    """
    Finaliza o lote atual do motoqueiro
    
    Marca todas as entregas como ENTREGUES e libera o motoqueiro.
    """
    courier = session.get(Courier, courier_id)
    if not courier:
        raise HTTPException(status_code=404, detail="Motoqueiro não encontrado")
    
    batch = get_courier_current_batch(session, courier_id)
    
    if not batch:
        raise HTTPException(
            status_code=400,
            detail="Motoqueiro não tem lote ativo"
        )
    
    # Marca TODOS os pedidos do lote como ENTREGUES
    orders = get_batch_orders(session, batch.id)
    for order in orders:
        order.status = OrderStatus.DELIVERED
        order.delivered_at = datetime.now()
        session.add(order)
    
    # Marca o lote como concluído
    batch.status = BatchStatus.DONE
    batch.completed_at = datetime.now()
    session.add(batch)
    
    # Libera o motoqueiro
    courier.status = CourierStatus.AVAILABLE
    courier.available_since = datetime.now()
    courier.updated_at = datetime.now()
    session.add(courier)
    
    session.commit()
    session.refresh(courier)
    
    return courier


@router.put("/{courier_id}/location")
def update_location(
    courier_id: str,
    lat: float,
    lng: float,
    session: Session = Depends(get_session)
):
    """
    Atualiza a localização do motoqueiro
    
    Usado para cálculos de proximidade.
    """
    courier = session.get(Courier, courier_id)
    if not courier:
        raise HTTPException(status_code=404, detail="Motoqueiro não encontrado")
    
    courier.last_lat = lat
    courier.last_lng = lng
    courier.updated_at = datetime.now()
    
    session.add(courier)
    session.commit()
    
    return {"message": "Localização atualizada"}


@router.put("/{courier_id}/push-token")
def update_push_token(
    courier_id: str,
    token: str,
    session: Session = Depends(get_session)
):
    """
    Salva o token de Push Notification do motoboy
    
    O app do motoboy chama isso quando:
    1. Usuário dá permissão para notificações
    2. Firebase gera o token único do dispositivo
    3. App envia o token pra cá → salva no banco
    
    Depois, o backend usa esse token para enviar notificações!
    """
    courier = session.get(Courier, courier_id)
    if not courier:
        raise HTTPException(status_code=404, detail="Motoqueiro não encontrado")
    
    courier.push_token = token
    courier.updated_at = datetime.now()
    
    session.add(courier)
    session.commit()
    
    print(f"✅ Push token salvo para {courier.name}")
    
    return {"message": "Token salvo com sucesso"}


@router.get("/{courier_id}/restaurant")
def get_courier_restaurant(courier_id: str, session: Session = Depends(get_session)):
    """
    Retorna os dados do restaurante associado ao motoboy
    
    O app do motoboy usa isso para:
    - Saber onde fica o restaurante (lat/lng)
    - Mostrar nome do restaurante
    - Calcular rota de volta
    
    NÃO chama Geocoding! Usa lat/lng já salvos = R$ 0,00
    """
    courier = session.get(Courier, courier_id)
    if not courier:
        raise HTTPException(status_code=404, detail="Motoqueiro não encontrado")
    
    # Se o courier não tem restaurant_id, tenta buscar qualquer restaurante
    # (compatibilidade com dados antigos)
    if courier.restaurant_id:
        restaurant = session.get(Restaurant, courier.restaurant_id)
    else:
        # Fallback: pega o primeiro restaurante (dados legados)
        restaurant = session.exec(select(Restaurant)).first()
    
    if not restaurant:
        raise HTTPException(
            status_code=404, 
            detail="Restaurante não encontrado. Configure o restaurante primeiro."
        )
    
    return {
        "id": restaurant.id,
        "name": restaurant.name,
        "address": restaurant.address,
        "lat": restaurant.lat,
        "lng": restaurant.lng,
        "phone": restaurant.phone
    }


# ============ RECUPERAÇÃO DE SENHA ============

def generate_reset_code(length: int = 12) -> str:
    """Gera código único para recuperação de senha"""
    alphabet = string.ascii_lowercase + string.digits
    alphabet = alphabet.replace('0', '').replace('o', '').replace('l', '').replace('1', '')
    return ''.join(secrets.choice(alphabet) for _ in range(length))


@router.post("/{courier_id}/password-reset")
def create_password_reset(
    courier_id: str,
    request: Request,
    session: Session = Depends(get_session)
):
    """
    Gera link de recuperação de senha para o motoboy
    
    Chamado pelo DONO no dashboard.
    O link é válido por 1 hora.
    """
    courier = session.get(Courier, courier_id)
    if not courier:
        raise HTTPException(status_code=404, detail="Motoqueiro não encontrado")
    
    # Gera código único
    while True:
        code = generate_reset_code()
        existing = session.exec(
            select(PasswordReset).where(PasswordReset.code == code)
        ).first()
        if not existing:
            break
    
    # Cria o reset
    reset = PasswordReset(
        code=code,
        courier_id=courier_id
    )
    
    session.add(reset)
    session.commit()
    session.refresh(reset)
    
    # Monta URL
    base_url = str(request.base_url).rstrip('/')
    reset_url = f"{base_url}/recuperar-senha/{reset.code}"
    
    return {
        "success": True,
        "courier_name": courier.name,
        "reset_url": reset_url,
        "expires_in": "1 hora"
    }


@router.get("/password-reset/{code}/validate")
def validate_password_reset(code: str, session: Session = Depends(get_session)):
    """
    Valida um código de recuperação de senha (público)
    """
    reset = session.exec(
        select(PasswordReset).where(PasswordReset.code == code)
    ).first()
    
    if not reset:
        return {"valid": False, "message": "Link inválido"}
    
    if reset.used:
        return {"valid": False, "message": "Este link já foi utilizado"}
    
    if datetime.now() > reset.expires_at:
        return {"valid": False, "message": "Este link expirou"}
    
    # Busca nome do motoboy
    courier = session.get(Courier, reset.courier_id)
    
    return {
        "valid": True,
        "courier_name": courier.name if courier else "Motoboy",
        "message": "Link válido"
    }


@router.post("/password-reset/{code}/use")
def use_password_reset(
    code: str,
    new_password: str,
    session: Session = Depends(get_session)
):
    """
    Usa o link para redefinir a senha (público)
    """
    reset = session.exec(
        select(PasswordReset).where(PasswordReset.code == code)
    ).first()
    
    if not reset:
        raise HTTPException(status_code=404, detail="Link inválido")
    
    if reset.used:
        raise HTTPException(status_code=400, detail="Este link já foi utilizado")
    
    if datetime.now() > reset.expires_at:
        raise HTTPException(status_code=400, detail="Este link expirou")
    
    if not new_password or len(new_password) < 4:
        raise HTTPException(status_code=400, detail="Senha deve ter pelo menos 4 caracteres")
    
    # Busca o motoboy
    courier = session.get(Courier, reset.courier_id)
    if not courier:
        raise HTTPException(status_code=404, detail="Motoboy não encontrado")
    
    # Atualiza a senha
    courier.password_hash = hash_password(new_password)
    courier.updated_at = datetime.now()
    session.add(courier)
    
    # Marca o link como usado
    reset.used = True
    reset.used_at = datetime.now()
    session.add(reset)
    
    session.commit()
    
    return {
        "success": True,
        "message": f"Senha atualizada com sucesso, {courier.name}!"
    }