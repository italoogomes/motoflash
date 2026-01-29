"""
Rotas de Pedidos (Orders)

🔒 PROTEÇÃO MULTI-TENANT:
- Todos os pedidos são vinculados ao restaurant_id do usuário logado
- Listagem filtra apenas pedidos do restaurante do usuário
"""
from datetime import datetime
from typing import List, Optional
import unicodedata
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlmodel import Session, select

from database import get_session
from models import (
    Order, OrderCreate, OrderResponse, OrderTrackingResponse, OrderStatus, User, Restaurant, Customer,
    Batch, Courier, OrderTrackingDetails, BatchInfo, CourierInfo, RouteInfo, SimpleOrder, Waypoint
)
from services.qrcode_service import generate_qrcode_base64, generate_qrcode_bytes
from services.geocoding_service import geocode_address
from services.auth_service import get_current_user
from services.order_service import generate_short_id, ensure_unique_tracking_code
from services.dispatch_service import get_batch_route_polyline

router = APIRouter(prefix="/orders", tags=["Pedidos"])


def normalize_text(text: str) -> str:
    """Remove acentos e converte para minúsculas para busca"""
    if not text:
        return ""
    # NFD decompõe caracteres acentuados (é -> e + acento)
    # Filtra apenas caracteres que não são "combining marks" (acentos)
    normalized = unicodedata.normalize('NFD', text)
    without_accents = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    return without_accents.lower()


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
    
    # Gera IDs amigáveis
    short_id = generate_short_id(current_user.restaurant_id, session)
    tracking_code = ensure_unique_tracking_code(session)

    order = Order(
        customer_name=order_data.customer_name,
        address_text=order_data.address_text,
        lat=lat,
        lng=lng,
        prep_type=order_data.prep_type,
        status=OrderStatus.CREATED,
        created_at=created_at,
        restaurant_id=current_user.restaurant_id,  # 🔒 PROTEÇÃO: vincula ao restaurante
        short_id=short_id,
        tracking_code=tracking_code
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


@router.get("/track/{tracking_code}", response_model=OrderTrackingResponse)
def track_order(tracking_code: str, session: Session = Depends(get_session)):
    """
    🌐 Endpoint PÚBLICO de rastreamento de pedido (sem autenticação)

    Permite que o cliente rastreie seu pedido usando o código de rastreio.
    Exemplo: GET /orders/track/MF-A3B7K9

    Args:
        tracking_code: Código de rastreio do pedido (ex: MF-A3B7K9)

    Returns:
        OrderTrackingResponse: Informações básicas do pedido (status, timestamps)

    Raises:
        404: Se o código de rastreio não for encontrado
    """
    # Busca o pedido pelo tracking_code
    statement = select(Order).where(Order.tracking_code == tracking_code)
    order = session.exec(statement).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Código de rastreio não encontrado. Verifique se digitou corretamente."
        )

    # Retorna informações básicas (sem dados sensíveis)
    return OrderTrackingResponse(
        short_id=order.short_id,
        tracking_code=order.tracking_code,
        status=order.status,
        created_at=order.created_at,
        ready_at=order.ready_at,
        delivered_at=order.delivered_at,
        customer_name=order.customer_name,
        address_text=order.address_text
    )


@router.get("/search", response_model=List[OrderResponse])
def search_orders(
    q: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    🔍 Busca pedidos para rastreamento (atendente)

    Busca por:
    - Nome do cliente (ignora acentos e case)
    - Telefone do cliente (busca exata)
    - Short ID (ex: "1234" ou "#1234")
    - Tracking code (ex: "MF-ABC123")

    Filtra:
    - Por restaurant_id (multi-tenant seguro)
    - Apenas pedidos ATIVOS (exclui delivered)
    - Limita a 10 resultados

    🔒 PROTEÇÃO: Retorna apenas pedidos do restaurante do usuário logado
    """
    if not current_user.restaurant_id:
        return []

    # Normalizar query para busca
    q_normalized = normalize_text(q)
    q_clean = q.strip().upper()

    # Lista para armazenar pedidos encontrados (usaremos set para evitar duplicatas)
    found_orders = set()

    # 1. Buscar por short_id (se for número)
    # Aceita "1234" ou "#1234"
    if q.replace("#", "").isdigit():
        short_id_search = int(q.replace("#", ""))
        statement = select(Order).where(
            Order.restaurant_id == current_user.restaurant_id,
            Order.short_id == short_id_search,
            Order.status != OrderStatus.DELIVERED
        )
        order = session.exec(statement).first()
        if order:
            found_orders.add(order.id)

    # 2. Buscar por tracking_code (se começar com "MF-")
    if q_clean.startswith("MF-"):
        statement = select(Order).where(
            Order.restaurant_id == current_user.restaurant_id,
            Order.tracking_code == q_clean,
            Order.status != OrderStatus.DELIVERED
        )
        order = session.exec(statement).first()
        if order:
            found_orders.add(order.id)

    # 3. Buscar por nome do cliente DIRETO no pedido (sem precisar de Customer cadastrado)
    # Busca no campo customer_name do Order
    orders_by_name = session.exec(
        select(Order).where(
            Order.restaurant_id == current_user.restaurant_id,
            Order.status != OrderStatus.DELIVERED
        )
    ).all()

    # Filtra localmente por nome normalizado
    for order in orders_by_name:
        if q_normalized in normalize_text(order.customer_name or ''):
            found_orders.add(order.id)

    # 4. Buscar TAMBÉM por telefone via Customer (se houver Customer cadastrado)
    customer_statement = select(Customer).where(
        Customer.restaurant_id == current_user.restaurant_id
    )
    customers = session.exec(customer_statement).all()

    # Filtrar clientes por telefone
    matching_customer_names = []
    for customer in customers:
        if q in (customer.phone or ''):  # Telefone: busca exata
            matching_customer_names.append(customer.name)

    # Se encontrou clientes por telefone, buscar pedidos desses clientes
    if matching_customer_names:
        for customer_name in matching_customer_names:
            orders_statement = select(Order).where(
                Order.restaurant_id == current_user.restaurant_id,
                Order.customer_name == customer_name,
                Order.status != OrderStatus.DELIVERED
            ).order_by(Order.created_at.desc())

            orders = session.exec(orders_statement).all()
            for order in orders:
                found_orders.add(order.id)

    # Buscar os objetos Order completos dos IDs encontrados
    if not found_orders:
        return []

    result_orders = []
    for order_id in found_orders:
        order = session.get(Order, order_id)
        if order:
            result_orders.append(order)

    # Ordenar por data de criação (mais recente primeiro) e limitar a 10
    result_orders.sort(key=lambda o: o.created_at, reverse=True)
    return result_orders[:10]


@router.get("/{order_id}/tracking-details", response_model=OrderTrackingDetails)
def get_order_tracking_details(
    order_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    🗺️ Retorna detalhes completos de rastreamento do pedido

    Inclui:
    - Dados completos do pedido
    - Informações do lote (se atribuído)
    - Posição na fila (ex: 2º de 3 entregas)
    - Dados do motoboy (nome, GPS)
    - Polyline da rota completa

    🔒 PROTEÇÃO: Retorna apenas pedidos do restaurante do usuário logado
    """
    # Buscar pedido
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    # 🔒 PROTEÇÃO: verifica se pedido é do restaurante do usuário
    if order.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    # Dados básicos do pedido
    order_response = OrderResponse(
        id=order.id,
        short_id=order.short_id,
        tracking_code=order.tracking_code,
        customer_name=order.customer_name,
        address_text=order.address_text,
        lat=order.lat,
        lng=order.lng,
        prep_type=order.prep_type,
        status=order.status,
        created_at=order.created_at,
        ready_at=order.ready_at,
        batch_id=order.batch_id,
        stop_order=order.stop_order
    )

    # Inicializar objetos opcionais
    batch_info = None
    courier_info = None
    route_info = None

    # Se pedido tem lote, buscar informações do lote
    if order.batch_id:
        batch = session.get(Batch, order.batch_id)

        if batch:
            # Buscar todos os pedidos do lote ordenados
            batch_orders_statement = select(Order).where(
                Order.batch_id == order.batch_id
            ).order_by(Order.stop_order)
            batch_orders = session.exec(batch_orders_statement).all()

            # Criar lista de SimpleOrder
            simple_orders = [
                SimpleOrder(
                    id=o.id,
                    short_id=o.short_id,
                    customer_name=o.customer_name,
                    address_text=o.address_text,
                    lat=o.lat,
                    lng=o.lng,
                    status=o.status,
                    stop_order=o.stop_order
                )
                for o in batch_orders
            ]

            # Criar BatchInfo
            batch_info = BatchInfo(
                id=batch.id,
                status=batch.status,
                position=order.stop_order if order.stop_order else 0,
                total=len(batch_orders),
                orders=simple_orders
            )

            # Buscar informações do motoboy
            if batch.courier_id:
                courier = session.get(Courier, batch.courier_id)
                if courier:
                    courier_info = CourierInfo(
                        id=courier.id,
                        name=courier.name if not courier.last_name else f"{courier.name} {courier.last_name}",
                        phone=courier.phone,
                        current_lat=courier.last_lat,
                        current_lng=courier.last_lng,
                        status=courier.status
                    )

            # Buscar rota do lote
            route_data = get_batch_route_polyline(session, order.batch_id)
            if route_data:
                # Converter waypoints para o schema Waypoint
                waypoints = []
                if "orders" in route_data:
                    for i, waypoint_data in enumerate(route_data["orders"]):
                        # Buscar o pedido correspondente para obter mais informações
                        if i < len(batch_orders):
                            corresponding_order = batch_orders[i]
                            waypoints.append(Waypoint(
                                lat=waypoint_data["lat"],
                                lng=waypoint_data["lng"],
                                address=waypoint_data.get("address", ""),
                                order_id=corresponding_order.id,
                                customer_name=corresponding_order.customer_name
                            ))
                        else:
                            waypoints.append(Waypoint(
                                lat=waypoint_data["lat"],
                                lng=waypoint_data["lng"],
                                address=waypoint_data.get("address", "")
                            ))

                route_info = RouteInfo(
                    polyline=route_data.get("polyline", ""),
                    start=route_data.get("start", {}),
                    waypoints=waypoints
                )

    # Retornar resposta completa
    return OrderTrackingDetails(
        order=order_response,
        batch=batch_info,
        courier=courier_info,
        route=route_info
    )
