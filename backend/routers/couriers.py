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
    PasswordReset, User
)
from services.dispatch_service import get_courier_current_batch, get_batch_orders
from services.auth_service import hash_password, verify_password, get_current_user

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
        message=f"Bem-vindo, {courier.full_name}!",
        courier=CourierResponse(
            id=courier.id,
            name=courier.name,
            last_name=courier.last_name,
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
        last_name=courier_data.last_name,
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
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Lista motoqueiros do restaurante do usuário logado
    
    🔒 PROTEÇÃO: Filtra por restaurant_id
    """
    # 🔒 Filtra por restaurante do usuário logado
    query = select(Courier).where(
        Courier.restaurant_id == current_user.restaurant_id
    ).order_by(Courier.name)
    
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


@router.delete("/{courier_id}")
def delete_courier(
    courier_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Exclui um motoqueiro
    
    🔒 PROTEÇÃO:
    - Só pode excluir motoboy do próprio restaurante
    - Não pode excluir se tiver entrega em andamento
    """
    courier = session.get(Courier, courier_id)
    if not courier:
        raise HTTPException(status_code=404, detail="Motoqueiro não encontrado")
    
    # 🔒 Verifica se pertence ao restaurante do usuário
    if courier.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=403, detail="Sem permissão para excluir este motoboy")
    
    # 🔒 Verifica se tem entrega em andamento
    current_batch = get_courier_current_batch(session, courier_id)
    if current_batch:
        raise HTTPException(
            status_code=400,
            detail="Não é possível excluir. Motoboy tem entregas pendentes."
        )
    
    # 🔒 Verifica se está ocupado
    if courier.status == CourierStatus.BUSY:
        raise HTTPException(
            status_code=400,
            detail="Não é possível excluir. Motoboy está em entrega."
        )
    
    # Exclui PasswordResets associados (se houver)
    resets = session.exec(
        select(PasswordReset).where(PasswordReset.courier_id == courier_id)
    ).all()
    for reset in resets:
        session.delete(reset)
    
    # Exclui o motoboy
    session.delete(courier)
    session.commit()
    
    return {"success": True, "message": f"Motoboy {courier.full_name} excluído com sucesso"}


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
        courier_name=courier.full_name,
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
        "courier_name": courier.full_name,
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
        "courier_name": courier.full_name if courier else "Motoboy",
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
        "message": f"Senha atualizada com sucesso, {courier.full_name}!"
    }

# ============ ROTAS DE ENTREGA PARA O MOTOBOY ============
# Essas rotas NÃO exigem JWT - são usadas pelo app do motoboy
# A validação é feita pelo courier_id + verificação do batch

@router.post("/{courier_id}/orders/{order_id}/pickup")
def courier_pickup_order(
    courier_id: str,
    order_id: str,
    session: Session = Depends(get_session)
):
    """
    Motoboy marca pedido como COLETADO
    
    Rota pública (sem JWT) - valida pelo courier_id
    """
    # Valida courier
    courier = session.get(Courier, courier_id)
    if not courier:
        raise HTTPException(status_code=404, detail="Motoqueiro não encontrado")
    
    # Valida que o courier tem um batch ativo
    batch = get_courier_current_batch(session, courier_id)
    if not batch:
        raise HTTPException(status_code=400, detail="Você não tem entregas ativas")
    
    # Valida que o pedido existe
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    
    # Valida que o pedido pertence ao batch do courier
    if order.batch_id != batch.id:
        raise HTTPException(status_code=403, detail="Este pedido não pertence à sua rota")
    
    # Valida status - ASSIGNED -> PICKED_UP
    if order.status == OrderStatus.PICKED_UP:
        # Já está coletado, ignora silenciosamente
        return {"success": True, "message": "Pedido já estava coletado", "order_id": order_id}
    
    if order.status != OrderStatus.ASSIGNED:
        raise HTTPException(
            status_code=400,
            detail=f"Pedido não pode ser coletado (status atual: {order.status})"
        )
    
    order.status = OrderStatus.PICKED_UP
    session.add(order)
    session.commit()
    
    return {"success": True, "message": "Pedido coletado", "order_id": order_id}


@router.post("/{courier_id}/orders/{order_id}/deliver")
def courier_deliver_order(
    courier_id: str,
    order_id: str,
    session: Session = Depends(get_session)
):
    """
    Motoboy marca pedido como ENTREGUE
    
    Rota pública (sem JWT) - valida pelo courier_id
    """
    # Valida courier
    courier = session.get(Courier, courier_id)
    if not courier:
        raise HTTPException(status_code=404, detail="Motoqueiro não encontrado")
    
    # Valida que o courier tem um batch ativo
    batch = get_courier_current_batch(session, courier_id)
    if not batch:
        raise HTTPException(status_code=400, detail="Você não tem entregas ativas")
    
    # Valida que o pedido existe
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    
    # Valida que o pedido pertence ao batch do courier
    if order.batch_id != batch.id:
        raise HTTPException(status_code=403, detail="Este pedido não pertence à sua rota")
    
    # Valida status - permite ASSIGNED ou PICKED_UP -> DELIVERED
    if order.status == OrderStatus.DELIVERED:
        # Já está entregue, ignora silenciosamente
        return {"success": True, "message": "Pedido já estava entregue", "order_id": order_id}
    
    if order.status not in [OrderStatus.ASSIGNED, OrderStatus.PICKED_UP]:
        raise HTTPException(
            status_code=400,
            detail=f"Pedido não pode ser entregue (status atual: {order.status})"
        )
    
    order.status = OrderStatus.DELIVERED
    order.delivered_at = datetime.now()
    session.add(order)
    session.commit()
    
    return {"success": True, "message": "Pedido entregue!", "order_id": order_id}