"""
Rotas de Pedidos (Orders)

🔒 PROTEÇÃO MULTI-TENANT:
- Todos os pedidos são vinculados ao restaurant_id do usuário logado
- Listagem filtra apenas pedidos do restaurante do usuário
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlmodel import Session, select

from database import get_session
from models import (
    Order, OrderCreate, OrderResponse, OrderStatus, User, Restaurant
)
from services.qrcode_service import generate_qrcode_base64, generate_qrcode_bytes
from services.geocoding_service import geocode_address
from services.auth_service import get_current_user

router = APIRouter(prefix="/orders", tags=["Pedidos"])


@router.post("", response_model=OrderResponse)
def create_order(
    order_data: OrderCreate, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Cria um novo pedido
    
    🔒 O pedido é vinculado automaticamente ao restaurante do usuário logado.
    Se lat/lng não forem informados, usa geocoding automático.
    """
    # Verifica se usuário tem restaurante
    if not current_user.restaurant_id:
        raise HTTPException(
            status_code=400,
            detail="Usuário não está vinculado a nenhum restaurante"
        )
    
    # Define a data de criação (simulada ou real)
    if order_data.simulated_date:
        try:
            sim_date = datetime.strptime(order_data.simulated_date, "%Y-%m-%d")
            now = datetime.now()
            created_at = sim_date.replace(hour=now.hour, minute=now.minute, second=now.second)
        except:
            created_at = datetime.now()
    else:
        created_at = datetime.now()
    
    # Geocoding automático se lat/lng não informados
    lat = order_data.lat
    lng = order_data.lng
    
    if lat is None or lng is None:
        coords = geocode_address(order_data.address_text)
        if coords:
            lat, lng = coords
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Não foi possível encontrar o endereço: {order_data.address_text}"
            )
    
    order = Order(
        customer_name=order_data.customer_name,
        address_text=order_data.address_text,
        lat=lat,
        lng=lng,
        prep_type=order_data.prep_type,
        status=OrderStatus.CREATED,
        created_at=created_at,
        restaurant_id=current_user.restaurant_id  # 🔒 PROTEÇÃO: vincula ao restaurante
    )
    
    session.add(order)
    session.commit()
    session.refresh(order)
    
    return order


@router.get("", response_model=List[OrderResponse])
def list_orders(
    status: OrderStatus = None,
    limit: int = 50,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Lista pedidos do restaurante do usuário logado
    
    🔒 Filtra automaticamente pelo restaurant_id
    """
    if not current_user.restaurant_id:
        return []
    
    # 🔒 PROTEÇÃO: filtra por restaurant_id
    query = select(Order).where(
        Order.restaurant_id == current_user.restaurant_id
    ).order_by(Order.created_at.desc()).limit(limit)
    
    if status:
        query = query.where(Order.status == status)
    
    orders = session.exec(query).all()
    return orders


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: str, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Busca um pedido pelo ID (apenas do próprio restaurante)
    """
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    
    # 🔒 PROTEÇÃO: verifica se pedido é do restaurante do usuário
    if order.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    
    return order


@router.get("/{order_id}/qrcode")
def get_order_qrcode(
    order_id: str, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Retorna o QR Code do pedido como base64
    """
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    
    # 🔒 PROTEÇÃO
    if order.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    
    qr_base64 = generate_qrcode_base64(order_id)
    
    return {
        "order_id": order_id,
        "qrcode": qr_base64
    }


@router.get("/{order_id}/qrcode.png")
def download_order_qrcode(
    order_id: str, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Download do QR Code como imagem PNG
    """
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    
    # 🔒 PROTEÇÃO
    if order.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    
    qr_bytes = generate_qrcode_bytes(order_id)
    
    return Response(
        content=qr_bytes,
        media_type="image/png",
        headers={"Content-Disposition": f"attachment; filename=pedido-{order_id[:8]}.png"}
    )


@router.post("/{order_id}/scan", response_model=OrderResponse)
def scan_order(
    order_id: str, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Marca o pedido como PRONTO (QR Code foi bipado)
    """
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    
    # 🔒 PROTEÇÃO
    if order.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    
    if order.status not in [OrderStatus.CREATED, OrderStatus.PREPARING]:
        raise HTTPException(
            status_code=400, 
            detail=f"Pedido não pode ser bipado (status atual: {order.status})"
        )
    
    order.status = OrderStatus.READY
    order.ready_at = datetime.now()
    
    session.add(order)
    session.commit()
    session.refresh(order)
    
    return order


@router.post("/{order_id}/preparing", response_model=OrderResponse)
def start_preparing(
    order_id: str, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Marca o pedido como EM PREPARO
    """
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    
    # 🔒 PROTEÇÃO
    if order.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    
    if order.status != OrderStatus.CREATED:
        raise HTTPException(
            status_code=400,
            detail=f"Pedido não pode iniciar preparo (status atual: {order.status})"
        )
    
    order.status = OrderStatus.PREPARING
    
    session.add(order)
    session.commit()
    session.refresh(order)
    
    return order


@router.post("/{order_id}/pickup", response_model=OrderResponse)
def pickup_order(
    order_id: str, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Marca o pedido como COLETADO pelo motoqueiro
    """
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    
    # 🔒 PROTEÇÃO
    if order.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    
    if order.status != OrderStatus.ASSIGNED:
        raise HTTPException(
            status_code=400,
            detail=f"Pedido não pode ser coletado (status atual: {order.status})"
        )
    
    order.status = OrderStatus.PICKED_UP
    
    session.add(order)
    session.commit()
    session.refresh(order)
    
    return order


@router.post("/{order_id}/deliver", response_model=OrderResponse)
def deliver_order(
    order_id: str, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Marca o pedido como ENTREGUE
    """
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    
    # 🔒 PROTEÇÃO
    if order.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    
    if order.status != OrderStatus.PICKED_UP:
        raise HTTPException(
            status_code=400,
            detail=f"Pedido não pode ser entregue (status atual: {order.status})"
        )
    
    order.status = OrderStatus.DELIVERED
    order.delivered_at = datetime.now()
    
    session.add(order)
    session.commit()
    session.refresh(order)
    
    return order
