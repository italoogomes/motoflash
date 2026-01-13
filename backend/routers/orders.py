"""
Rotas de Pedidos (Orders)
"""
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlmodel import Session, select

from database import get_session
from models import (
    Order, OrderCreate, OrderResponse, OrderStatus
)
from services.qrcode_service import generate_qrcode_base64, generate_qrcode_bytes

router = APIRouter(prefix="/orders", tags=["Pedidos"])


@router.post("", response_model=OrderResponse)
def create_order(order_data: OrderCreate, session: Session = Depends(get_session)):
    """
    Cria um novo pedido
    
    O pedido começa com status CREATED.
    Um QR Code é gerado automaticamente com o ID do pedido.
    """
    order = Order(
        customer_name=order_data.customer_name,
        address_text=order_data.address_text,
        lat=order_data.lat,
        lng=order_data.lng,
        prep_type=order_data.prep_type,
        status=OrderStatus.CREATED
    )
    
    session.add(order)
    session.commit()
    session.refresh(order)
    
    return order


@router.get("", response_model=List[OrderResponse])
def list_orders(
    status: OrderStatus = None,
    limit: int = 50,
    session: Session = Depends(get_session)
):
    """
    Lista pedidos, opcionalmente filtrados por status
    """
    query = select(Order).order_by(Order.created_at.desc()).limit(limit)
    
    if status:
        query = query.where(Order.status == status)
    
    orders = session.exec(query).all()
    return orders


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: str, session: Session = Depends(get_session)):
    """
    Busca um pedido pelo ID
    """
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    return order


@router.get("/{order_id}/qrcode")
def get_order_qrcode(order_id: str, session: Session = Depends(get_session)):
    """
    Retorna o QR Code do pedido como base64
    
    Use isso para exibir na tela / imprimir
    """
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    
    qr_base64 = generate_qrcode_base64(order_id)
    
    return {
        "order_id": order_id,
        "qrcode": qr_base64
    }


@router.get("/{order_id}/qrcode.png")
def download_order_qrcode(order_id: str, session: Session = Depends(get_session)):
    """
    Download do QR Code como imagem PNG
    """
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    
    qr_bytes = generate_qrcode_bytes(order_id)
    
    return Response(
        content=qr_bytes,
        media_type="image/png",
        headers={"Content-Disposition": f"attachment; filename=pedido-{order_id[:8]}.png"}
    )


@router.post("/{order_id}/scan", response_model=OrderResponse)
def scan_order(order_id: str, session: Session = Depends(get_session)):
    """
    Marca o pedido como PRONTO (QR Code foi bipado)
    
    Este endpoint é chamado quando a cozinha/embalagem bipa o QR Code.
    O pedido entra na fila de despacho.
    """
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    
    # Só pode bipar se estiver em preparo ou criado
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
def start_preparing(order_id: str, session: Session = Depends(get_session)):
    """
    Marca o pedido como EM PREPARO
    
    Opcional - pode ir direto de CREATED para READY
    """
    order = session.get(Order, order_id)
    if not order:
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
def pickup_order(order_id: str, session: Session = Depends(get_session)):
    """
    Marca o pedido como COLETADO pelo motoqueiro
    """
    order = session.get(Order, order_id)
    if not order:
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
def deliver_order(order_id: str, session: Session = Depends(get_session)):
    """
    Marca o pedido como ENTREGUE
    """
    order = session.get(Order, order_id)
    if not order:
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
