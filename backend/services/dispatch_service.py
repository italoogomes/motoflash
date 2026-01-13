"""
Serviço de Dispatch - O CORAÇÃO do MotoFlash

Algoritmo inteligente que:
1. PRIMEIRO: Agrupa pedidos do MESMO endereço (nunca separa!)
2. SEGUNDO: Agrupa clusters próximos geograficamente
3. TERCEIRO: Distribui para motoqueiros de forma otimizada

Versão V0.2 - Inteligência Real
"""
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict
from sqlmodel import Session, select
from math import radians, sin, cos, sqrt, atan2

from models import (
    Order, Courier, Batch, 
    OrderStatus, CourierStatus, BatchStatus,
    DispatchResult
)


# ============ CONFIGURAÇÕES DO DISPATCH V0.2 ============

# Distância para considerar MESMO endereço (em km)
# 0.05 km = 50 metros - praticamente o mesmo lugar
SAME_ADDRESS_THRESHOLD_KM = 0.05

# Raio máximo para agrupar pedidos PRÓXIMOS no mesmo lote (km)
MAX_CLUSTER_RADIUS_KM = 3.0

# Máximo de pedidos por motoqueiro
MAX_ORDERS_PER_COURIER = 3

# Se tem motoqueiros sobrando, prefere distribuir
# MAS nunca separa pedidos do mesmo endereço!
PREFER_DISTRIBUTION = False


# ============ FUNÇÕES AUXILIARES ============

def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calcula distância entre dois pontos em km usando fórmula de Haversine
    """
    R = 6371  # Raio da Terra em km
    
    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
    
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c


def is_same_address(order1: Order, order2: Order) -> bool:
    """
    Verifica se dois pedidos são do MESMO endereço
    Usa coordenadas porque o texto pode ter variações
    """
    distance = haversine_distance(order1.lat, order1.lng, order2.lat, order2.lng)
    return distance <= SAME_ADDRESS_THRESHOLD_KM


def calculate_cluster_center(orders: List[Order]) -> Tuple[float, float]:
    """Calcula o centro geográfico de um grupo de pedidos"""
    if not orders:
        return (0, 0)
    
    avg_lat = sum(o.lat for o in orders) / len(orders)
    avg_lng = sum(o.lng for o in orders) / len(orders)
    
    return (avg_lat, avg_lng)


def distance_to_cluster(order: Order, cluster: List[Order]) -> float:
    """Calcula distância de um pedido até o centro do cluster"""
    if not cluster:
        return 0
    center_lat, center_lng = calculate_cluster_center(cluster)
    return haversine_distance(order.lat, order.lng, center_lat, center_lng)


def sort_orders_by_distance(orders: List[Order], start_lat: float, start_lng: float) -> List[Order]:
    """
    Ordena pedidos pela distância do ponto inicial (rota mais curta)
    Usa algoritmo guloso: sempre vai pro mais perto
    """
    if len(orders) <= 1:
        return orders
    
    sorted_orders = []
    remaining = orders.copy()
    current_lat, current_lng = start_lat, start_lng
    
    while remaining:
        # Encontra o pedido mais próximo
        closest = min(
            remaining,
            key=lambda o: haversine_distance(current_lat, current_lng, o.lat, o.lng)
        )
        sorted_orders.append(closest)
        remaining.remove(closest)
        current_lat, current_lng = closest.lat, closest.lng
    
    return sorted_orders


# ============ ALGORITMO INTELIGENTE ============

def group_by_same_address(orders: List[Order]) -> List[List[Order]]:
    """
    PASSO 1: Agrupa pedidos que são do MESMO endereço
    
    Isso NUNCA pode ser separado - é a mesma entrega!
    Ex: 2 pizzas pro mesmo cliente = 1 parada só
    """
    if not orders:
        return []
    
    groups = []
    used = set()
    
    for i, order in enumerate(orders):
        if i in used:
            continue
            
        # Começa novo grupo com este pedido
        group = [order]
        used.add(i)
        
        # Procura outros pedidos no MESMO endereço
        for j, other in enumerate(orders):
            if j in used:
                continue
            if is_same_address(order, other):
                group.append(other)
                used.add(j)
        
        groups.append(group)
    
    return groups


def merge_nearby_groups(
    groups: List[List[Order]], 
    max_radius_km: float, 
    max_orders: int
) -> List[List[Order]]:
    """
    PASSO 2: Junta grupos próximos se couber no limite
    
    Ex: Grupo A (1 pedido) + Grupo B (1 pedido) próximos = 1 lote de 2
    """
    if len(groups) <= 1:
        return groups
    
    merged = []
    used = set()
    
    for i, group in enumerate(groups):
        if i in used:
            continue
        
        current_group = group.copy()
        used.add(i)
        
        # Tenta juntar com outros grupos próximos
        for j, other_group in enumerate(groups):
            if j in used:
                continue
            
            # Verifica se caberia no limite
            if len(current_group) + len(other_group) > max_orders:
                continue
            
            # Calcula distância entre os centros dos grupos
            center1 = calculate_cluster_center(current_group)
            center2 = calculate_cluster_center(other_group)
            distance = haversine_distance(center1[0], center1[1], center2[0], center2[1])
            
            if distance <= max_radius_km:
                current_group.extend(other_group)
                used.add(j)
        
        merged.append(current_group)
    
    return merged


def smart_cluster_orders(
    orders: List[Order], 
    max_radius_km: float, 
    max_per_courier: int,
    num_couriers: int
) -> List[List[Order]]:
    """
    Algoritmo inteligente de agrupamento
    
    1. Agrupa pedidos do MESMO endereço (nunca separa)
    2. Junta grupos próximos se fizer sentido
    3. Respeita o limite por motoboy
    """
    if not orders:
        return []
    
    # PASSO 1: Agrupa por mesmo endereço
    address_groups = group_by_same_address(orders)
    
    # PASSO 2: Se temos mais motoboys que grupos E queremos distribuir,
    # não precisa juntar - cada grupo vai pra um motoboy
    if PREFER_DISTRIBUTION and num_couriers >= len(address_groups):
        # Mas ainda precisamos verificar se algum grupo excede o limite
        final_groups = []
        for group in address_groups:
            if len(group) <= max_per_courier:
                final_groups.append(group)
            else:
                # Grupo grande demais, precisa dividir (mesmo endereço, múltiplas viagens)
                for i in range(0, len(group), max_per_courier):
                    final_groups.append(group[i:i + max_per_courier])
        return final_groups
    
    # PASSO 3: Precisa otimizar - junta grupos próximos
    merged_groups = merge_nearby_groups(address_groups, max_radius_km, max_per_courier)
    
    return merged_groups


def run_dispatch(session: Session) -> DispatchResult:
    """
    Executa o algoritmo de dispatch INTELIGENTE
    
    Regras:
    1. Pedidos do MESMO endereço SEMPRE vão juntos
    2. Pedidos PRÓXIMOS são agrupados quando faz sentido
    3. Distribui de forma justa entre motoboys
    """
    # 1. Busca TODOS os pedidos READY que ainda não foram atribuídos
    ready_orders = session.exec(
        select(Order)
        .where(Order.status == OrderStatus.READY)
        .where(Order.batch_id == None)
        .order_by(Order.ready_at)
    ).all()
    
    if not ready_orders:
        return DispatchResult(
            batches_created=0,
            orders_assigned=0,
            message="Nenhum pedido pronto aguardando"
        )
    
    # 2. Busca motoqueiros disponíveis
    available_couriers = session.exec(
        select(Courier)
        .where(Courier.status == CourierStatus.AVAILABLE)
        .order_by(Courier.available_since)  # Quem está esperando há mais tempo
    ).all()
    
    if not available_couriers:
        return DispatchResult(
            batches_created=0,
            orders_assigned=0,
            message=f"{len(ready_orders)} pedido(s) pronto(s), mas nenhum motoqueiro disponível"
        )
    
    # 3. Agrupa pedidos de forma INTELIGENTE
    clusters = smart_cluster_orders(
        list(ready_orders),
        MAX_CLUSTER_RADIUS_KM,
        MAX_ORDERS_PER_COURIER,
        len(available_couriers)
    )
    
    # 4. Atribui clusters aos motoqueiros
    batches_created = 0
    orders_assigned = 0
    
    for i, cluster in enumerate(clusters):
        if i >= len(available_couriers):
            break  # Acabaram os motoqueiros
        
        courier = available_couriers[i]
        
        # Cria o lote
        batch = Batch(courier_id=courier.id)
        session.add(batch)
        session.commit()
        session.refresh(batch)
        
        # Ordena pedidos do cluster pela rota mais curta
        start_lat = courier.last_lat or -21.17  # Default: Ribeirão Preto
        start_lng = courier.last_lng or -47.81
        
        sorted_cluster = sort_orders_by_distance(cluster, start_lat, start_lng)
        
        # Atribui pedidos ao lote
        for stop_num, order in enumerate(sorted_cluster, 1):
            order.batch_id = batch.id
            order.stop_order = stop_num
            order.status = OrderStatus.ASSIGNED
            session.add(order)
        
        # Atualiza status do motoqueiro
        courier.status = CourierStatus.BUSY
        courier.updated_at = datetime.now()
        session.add(courier)
        
        batches_created += 1
        orders_assigned += len(cluster)
    
    session.commit()
    
    # Conta pedidos que ficaram sem atribuição
    remaining = len(ready_orders) - orders_assigned
    
    message = f"{batches_created} lote(s) criado(s), {orders_assigned} pedido(s) atribuído(s)"
    if remaining > 0:
        message += f", {remaining} pedido(s) aguardando motoqueiro"
    
    return DispatchResult(
        batches_created=batches_created,
        orders_assigned=orders_assigned,
        message=message
    )


def get_courier_current_batch(session: Session, courier_id: str) -> Optional[Batch]:
    """Retorna o lote atual do motoqueiro (se houver)"""
    batch = session.exec(
        select(Batch)
        .where(Batch.courier_id == courier_id)
        .where(Batch.status.in_([BatchStatus.ASSIGNED, BatchStatus.IN_PROGRESS]))
        .order_by(Batch.created_at.desc())
    ).first()
    
    return batch


def get_batch_orders(session: Session, batch_id: str) -> List[Order]:
    """Retorna os pedidos de um lote, ordenados pela rota"""
    orders = session.exec(
        select(Order)
        .where(Order.batch_id == batch_id)
        .order_by(Order.stop_order)
    ).all()
    
    return list(orders)