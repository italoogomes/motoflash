"""
Serviço de Dispatch - O CORAÇÃO do MotoFlash

Algoritmo inteligente que:
1. PRIMEIRO: Agrupa pedidos do MESMO endereço (nunca separa!)
2. SEGUNDO: SEMPRE agrupa pedidos próximos (até 3km) - otimiza rotas!
3. TERCEIRO: Calcula distância REAL por rota (não linha reta) de cada pedido
4. QUARTO: Ordena pelo mais perto POR ROTA primeiro
5. QUINTO: Pedidos órfãos vão pra rota mais próxima (NUNCA fica parado!)
6. NOVO: Retorna polyline da rota para desenhar no mapa!

Versão V0.9 - Adiciona polyline da rota real (Google)
"""
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict
from sqlmodel import Session, select
from math import radians, sin, cos, sqrt, atan2
import httpx
import os

from models import (
    Order, Courier, Batch, 
    OrderStatus, CourierStatus, BatchStatus,
    DispatchResult
)
from services.push_service import notify_new_batch


# ============ CONFIGURAÇÕES DO DISPATCH V0.9 ============

# API Key do Google Maps (carregada de variável de ambiente)
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

if not GOOGLE_MAPS_API_KEY:
    raise ValueError(
        "⚠️ GOOGLE_MAPS_API_KEY não configurada!\n"
        "Configure a variável de ambiente GOOGLE_MAPS_API_KEY com sua chave do Google Maps.\n"
        "Obtenha em: https://console.cloud.google.com/apis/credentials"
    )

# Distância para considerar MESMO endereço (em km)
# 0.05 km = 50 metros - praticamente o mesmo lugar
SAME_ADDRESS_THRESHOLD_KM = 0.05

# Raio máximo para agrupar pedidos PRÓXIMOS no mesmo lote (km)
# 3 km = pedidos nesse raio VÃO JUNTOS pro mesmo motoboy
MAX_CLUSTER_RADIUS_KM = 3.0

# Quantidade IDEAL de pedidos por motoboy
# O algoritmo tenta agrupar até esse limite
PREFERRED_ORDERS_PER_COURIER = 4

# Limite ABSOLUTO de pedidos por motoboy (segurança)
MAX_ABSOLUTE_ORDERS = 6


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


def distance_order_to_route(order: Order, route_orders: List[Order]) -> float:
    """
    Calcula a menor distância de um pedido até qualquer ponto de uma rota
    Retorna a distância até o ponto mais próximo da rota
    """
    if not route_orders:
        return float('inf')
    
    min_distance = float('inf')
    for route_order in route_orders:
        dist = haversine_distance(order.lat, order.lng, route_order.lat, route_order.lng)
        if dist < min_distance:
            min_distance = dist
    
    return min_distance


def sort_orders_by_distance(orders: List[Order], start_lat: float, start_lng: float) -> List[Order]:
    """
    FALLBACK: Ordena pedidos pela distância do ponto inicial (rota mais curta)
    Usa algoritmo guloso: sempre vai pro mais perto
    
    Usado quando a API do Google falha
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


# ============ DETECÇÃO DE MESMA RUA ============

def extract_street_name(address: str) -> str:
    """
    Extrai o nome da rua de um endereço
    Ex: "Rua General Osório, 634 - Centro" -> "rua general osorio"
    """
    if not address:
        return ""
    
    # Pega a parte antes da vírgula (nome da rua)
    parts = address.split(",")
    street = parts[0].strip().lower()
    
    # Remove acentos para comparação
    import unicodedata
    street = unicodedata.normalize('NFD', street)
    street = ''.join(c for c in street if unicodedata.category(c) != 'Mn')
    
    return street


def are_same_street(orders: List[Order]) -> bool:
    """
    Verifica se todos os pedidos estão na mesma rua
    """
    if len(orders) <= 1:
        return True
    
    streets = [extract_street_name(o.address_text) for o in orders]
    return len(set(streets)) == 1


def get_driving_distance(start_lat: float, start_lng: float, end_lat: float, end_lng: float) -> float:
    """
    Calcula a distância REAL por rota (não linha reta) usando Google Directions API
    Retorna a distância em metros
    """
    try:
        url = "https://maps.googleapis.com/maps/api/directions/json"
        params = {
            "origin": f"{start_lat},{start_lng}",
            "destination": f"{end_lat},{end_lng}",
            "mode": "driving",
            "key": GOOGLE_MAPS_API_KEY
        }
        
        with httpx.Client(timeout=5.0) as client:
            response = client.get(url, params=params)
            data = response.json()
        
        if data.get("status") == "OK":
            # Pega a distância da primeira rota
            distance = data["routes"][0]["legs"][0]["distance"]["value"]  # em metros
            return distance
        else:
            # Fallback: distância em linha reta * 1.4 (fator de correção)
            return haversine_distance(start_lat, start_lng, end_lat, end_lng) * 1000 * 1.4
    except:
        return haversine_distance(start_lat, start_lng, end_lat, end_lng) * 1000 * 1.4


# ============ POLYLINE DA ROTA (NOVO V0.9) ============

def get_route_polyline(
    orders: List[Order], 
    start_lat: float, 
    start_lng: float,
    include_return: bool = False
) -> Optional[str]:
    """
    NOVO V0.9: Obtém a polyline encoded da rota completa
    
    Chama o Google Directions API UMA vez com todos os waypoints
    e retorna a polyline que pode ser desenhada no mapa.
    
    Args:
        orders: Lista de pedidos ordenados
        start_lat, start_lng: Coordenadas do restaurante
        include_return: Se deve incluir volta ao restaurante
    
    Returns:
        String da polyline encoded ou None se falhar
    """
    if not orders:
        return None
    
    try:
        # Origem: restaurante
        origin = f"{start_lat},{start_lng}"
        
        # Destino: último pedido (ou restaurante se include_return)
        if include_return:
            destination = origin
            # Todos os pedidos são waypoints
            waypoint_coords = [f"{o.lat},{o.lng}" for o in orders]
        else:
            # Último pedido é o destino
            destination = f"{orders[-1].lat},{orders[-1].lng}"
            # Pedidos intermediários são waypoints
            waypoint_coords = [f"{o.lat},{o.lng}" for o in orders[:-1]]
        
        url = "https://maps.googleapis.com/maps/api/directions/json"
        params = {
            "origin": origin,
            "destination": destination,
            "mode": "driving",
            "key": GOOGLE_MAPS_API_KEY
        }
        
        # Adiciona waypoints se houver
        if waypoint_coords:
            # SEM optimize:true para manter a ordem que já calculamos
            params["waypoints"] = "|".join(waypoint_coords)
        
        print(f"🗺️ Buscando polyline da rota...")
        print(f"   Origin: {origin}")
        print(f"   Destination: {destination}")
        if waypoint_coords:
            print(f"   Waypoints: {len(waypoint_coords)}")
        
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, params=params)
            data = response.json()
        
        if data.get("status") == "OK":
            polyline = data["routes"][0]["overview_polyline"]["points"]
            print(f"✅ Polyline obtida! ({len(polyline)} chars)")
            return polyline
        else:
            print(f"⚠️ Google API retornou: {data.get('status')}")
            return None
            
    except Exception as e:
        print(f"❌ Erro ao buscar polyline: {e}")
        return None


def get_batch_route_polyline(session: Session, batch_id: str) -> Optional[dict]:
    """
    NOVO V0.9: Endpoint helper para obter a polyline de um batch
    
    Retorna dict com:
        - polyline: string encoded
        - start: {lat, lng} do restaurante
        - orders: lista de {lat, lng, address} na ordem
    """
    # Busca o batch para pegar o restaurant_id
    from models import Batch, Restaurant
    batch = session.get(Batch, batch_id)
    
    if not batch:
        return None
    
    # Busca os pedidos do batch ordenados
    orders = session.exec(
        select(Order)
        .where(Order.batch_id == batch_id)
        .order_by(Order.stop_order)
    ).all()
    
    if not orders:
        return None
    
    # Busca coordenadas do restaurante vinculado ao batch
    restaurant = session.get(Restaurant, batch.restaurant_id) if batch.restaurant_id else None
    
    if restaurant and restaurant.lat and restaurant.lng:
        start_lat = restaurant.lat
        start_lng = restaurant.lng
    else:
        # Fallback: busca primeiro restaurante (compatibilidade)
        restaurant = session.exec(select(Restaurant)).first()
        if restaurant and restaurant.lat and restaurant.lng:
            start_lat = restaurant.lat
            start_lng = restaurant.lng
        else:
            # Último fallback: coordenadas hardcoded
            print("⚠️ Usando coordenadas hardcoded - configure o restaurante!")
            start_lat = -21.2020
            start_lng = -47.8130
    
    print(f"🏪 Coordenadas do restaurante: {start_lat}, {start_lng}")
    
    # Obtém a polyline
    polyline = get_route_polyline(list(orders), start_lat, start_lng)
    
    return {
        "polyline": polyline,
        "start": {"lat": start_lat, "lng": start_lng},
        "orders": [
            {"lat": o.lat, "lng": o.lng, "address": o.address_text}
            for o in orders
        ]
    }


# ============ OTIMIZAÇÃO VIA GOOGLE DIRECTIONS API ============

def optimize_route_with_google(
    orders: List[Order], 
    start_lat: float, 
    start_lng: float
) -> List[Order]:
    """
    USA A API DO GOOGLE PARA OTIMIZAR A ORDEM DAS ENTREGAS!
    
    VERSÃO V0.8: 
    - Calcula distância REAL por rota (não linha reta) de cada pedido
    - Ordena pelo mais perto POR ROTA primeiro
    - Não usa optimize:true do Google (que inverte a ordem)
    
    Isso resolve o problema do Google inverter pedidos na mesma rua.
    """
    if len(orders) <= 1:
        return orders
    
    try:
        print(f"🗺️ === OTIMIZAÇÃO DE ROTA V0.8 ===")
        print(f"   Restaurante: {start_lat}, {start_lng}")
        print(f"   Pedidos recebidos ({len(orders)}):")
        
        # Calcula a distância REAL por rota de cada pedido até o restaurante
        orders_with_distance = []
        for o in orders:
            # Distância em linha reta (para log)
            straight_dist = haversine_distance(start_lat, start_lng, o.lat, o.lng)
            
            # Distância REAL por rota
            driving_dist = get_driving_distance(start_lat, start_lng, o.lat, o.lng)
            
            orders_with_distance.append({
                'order': o,
                'straight_km': straight_dist,
                'driving_m': driving_dist
            })
            print(f"      {o.address_text[:40]}")
            print(f"         Linha reta: {straight_dist:.2f}km | Por rota: {driving_dist/1000:.2f}km")
        
        # Ordena pela distância REAL por rota (mais perto primeiro)
        orders_with_distance.sort(key=lambda x: x['driving_m'])
        
        optimized_orders = [item['order'] for item in orders_with_distance]
        
        print(f"   === RESULTADO ===")
        print(f"   Ordem final (por distância de rota):")
        for i, item in enumerate(orders_with_distance):
            print(f"      {i+1}. {item['order'].address_text[:40]} ({item['driving_m']/1000:.2f}km)")
        print(f"🗺️ === FIM ===")
        
        return optimized_orders
        
    except Exception as e:
        print(f"❌ Erro ao chamar Google API: {e} - usando fallback")
        return sort_orders_by_distance(orders, start_lat, start_lng)


def insert_order_in_best_position(order: Order, route: List[Order], start_lat: float, start_lng: float) -> List[Order]:
    """
    Insere um pedido na melhor posição da rota (menor desvio)
    """
    if not route:
        return [order]
    
    # Testa inserir em cada posição e calcula a distância total
    best_route = None
    best_distance = float('inf')
    
    for i in range(len(route) + 1):
        test_route = route[:i] + [order] + route[i:]
        
        # Calcula distância total dessa rota
        total_dist = 0
        prev_lat, prev_lng = start_lat, start_lng
        for o in test_route:
            total_dist += haversine_distance(prev_lat, prev_lng, o.lat, o.lng)
            prev_lat, prev_lng = o.lat, o.lng
        
        if total_dist < best_distance:
            best_distance = total_dist
            best_route = test_route
    
    return best_route


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
    
    PRIORIDADE MÁXIMA: Agrupar pedidos próximos para otimizar rotas!
    Isso é o CORAÇÃO do MotoFlash - nunca desperdiçar rota.
    
    1. Agrupa pedidos do MESMO endereço (nunca separa)
    2. SEMPRE junta grupos próximos (otimização de rota)
    3. Respeita o limite por motoboy
    """
    if not orders:
        return []
    
    # PASSO 1: Agrupa por mesmo endereço (ex: 2 pizzas pro mesmo cliente)
    address_groups = group_by_same_address(orders)
    
    # PASSO 2: SEMPRE agrupa pedidos próximos - isso é a inteligência do app!
    # Não importa quantos motoboys tem, pedidos próximos = mesma rota
    merged_groups = merge_nearby_groups(address_groups, max_radius_km, max_per_courier)
    
    # PASSO 3: Verifica se algum grupo excede o limite e divide se necessário
    final_groups = []
    for group in merged_groups:
        if len(group) <= max_per_courier:
            final_groups.append(group)
        else:
            # Grupo grande demais, precisa dividir em múltiplas viagens
            # Ordena por proximidade antes de dividir
            center = calculate_cluster_center(group)
            sorted_group = sorted(group, key=lambda o: haversine_distance(o.lat, o.lng, center[0], center[1]))
            for i in range(0, len(sorted_group), max_per_courier):
                final_groups.append(sorted_group[i:i + max_per_courier])
    
    return final_groups


def run_dispatch(session: Session, restaurant_id: str = None) -> DispatchResult:
    """
    Executa o algoritmo de dispatch INTELIGENTE
    
    🔒 PROTEÇÃO MULTI-TENANT:
    - Filtra pedidos por restaurant_id
    - Filtra motoboys por restaurant_id
    - Busca coordenadas do restaurante correto
    
    Regras:
    1. Pedidos do MESMO endereço SEMPRE vão juntos
    2. Pedidos PRÓXIMOS são agrupados quando faz sentido
    3. Distribui de forma justa entre motoboys
    4. NENHUM PEDIDO FICA PARADO se tem motoboy disponível!
    """
    # 🔒 Busca coordenadas do restaurante
    from models import Restaurant
    
    if restaurant_id:
        restaurant = session.get(Restaurant, restaurant_id)
    else:
        # Fallback: primeiro restaurante (compatibilidade)
        restaurant = session.exec(select(Restaurant)).first()
    
    if restaurant and restaurant.lat and restaurant.lng:
        start_lat = restaurant.lat
        start_lng = restaurant.lng
    else:
        # Último fallback: coordenadas hardcoded
        print("⚠️ AVISO: Usando coordenadas hardcoded - configure o restaurante!")
        start_lat = -21.2020
        start_lng = -47.8130
    
    # 1. Busca TODOS os pedidos READY que ainda não foram atribuídos
    query = select(Order).where(
        Order.status == OrderStatus.READY,
        Order.batch_id == None
    ).order_by(Order.ready_at)
    
    # 🔒 Filtra por restaurante se informado
    if restaurant_id:
        query = query.where(Order.restaurant_id == restaurant_id)
    
    ready_orders = session.exec(query).all()
    
    if not ready_orders:
        return DispatchResult(
            batches_created=0,
            orders_assigned=0,
            message="Nenhum pedido pronto aguardando"
        )
    
    # 2. Busca motoqueiros disponíveis
    courier_query = select(Courier).where(
        Courier.status == CourierStatus.AVAILABLE
    ).order_by(Courier.available_since)
    
    # 🔒 Filtra por restaurante se informado
    if restaurant_id:
        courier_query = courier_query.where(Courier.restaurant_id == restaurant_id)
    
    available_couriers = session.exec(courier_query).all()
    
    if not available_couriers:
        return DispatchResult(
            batches_created=0,
            orders_assigned=0,
            message=f"{len(ready_orders)} pedido(s) pronto(s), mas nenhum motoqueiro disponível"
        )
    
    # 3. Agrupa pedidos de forma INTELIGENTE (primeira passada)
    clusters = smart_cluster_orders(
        list(ready_orders),
        MAX_CLUSTER_RADIUS_KM,
        PREFERRED_ORDERS_PER_COURIER,
        len(available_couriers)
    )
    
    # 4. Atribui clusters aos motoqueiros
    batches_created = 0
    orders_assigned = 0
    batch_orders_map = {}  # batch_id -> lista de orders
    courier_batch_map = {}  # courier_id -> batch
    
    for i, cluster in enumerate(clusters):
        if i >= len(available_couriers):
            break  # Acabaram os motoqueiros
        
        courier = available_couriers[i]
        
        # 🔒 Cria o lote vinculado ao restaurante
        batch = Batch(
            courier_id=courier.id,
            restaurant_id=restaurant_id  # 🔒 PROTEÇÃO
        )
        session.add(batch)
        session.commit()
        session.refresh(batch)
        
        # Ordena pedidos do cluster pela ROTA REAL (Google Directions API)
        # Considera sentido das vias, mão única, etc.
        # SEMPRE usa o restaurante como ponto de partida (não a posição do motoboy)
        # O motoboy sai do restaurante com os pedidos, então a rota começa de lá
        
        # USA GOOGLE PARA OTIMIZAR! (SEM considerar volta ao restaurante)
        sorted_cluster = optimize_route_with_google(cluster, start_lat, start_lng)
        
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
        
        # 🔔 ENVIA PUSH NOTIFICATION para o motoboy!
        if courier.push_token:
            notify_new_batch(
                token=courier.push_token,
                order_count=len(cluster),
                batch_id=batch.id
            )
        
        # Guarda referência para possível adição de pedidos órfãos
        batch_orders_map[batch.id] = sorted_cluster.copy()
        courier_batch_map[courier.id] = {
            'batch': batch,
            'courier': courier,
            'start_lat': start_lat,
            'start_lng': start_lng
        }
        
        batches_created += 1
        orders_assigned += len(cluster)
    
    session.commit()
    
    # 5. NOVO! Verifica se ficou pedido órfão e adiciona na rota mais próxima
    orphan_orders = [o for o in ready_orders if o.batch_id is None]
    orphans_assigned = 0
    
    if orphan_orders and batch_orders_map:
        for orphan in orphan_orders:
            # Encontra a rota mais próxima que ainda pode receber pedidos
            best_batch_id = None
            best_distance = float('inf')
            
            for batch_id, route_orders in batch_orders_map.items():
                # Verifica se ainda pode adicionar (limite absoluto)
                if len(route_orders) >= MAX_ABSOLUTE_ORDERS:
                    continue
                
                # Calcula distância até essa rota
                distance = distance_order_to_route(orphan, route_orders)
                
                if distance < best_distance:
                    best_distance = distance
                    best_batch_id = batch_id
            
            # Adiciona na melhor rota encontrada
            if best_batch_id:
                batch_info = None
                for cid, info in courier_batch_map.items():
                    if info['batch'].id == best_batch_id:
                        batch_info = info
                        break
                
                if batch_info:
                    # Recalcula a rota com o novo pedido na melhor posição
                    current_route = batch_orders_map[best_batch_id]
                    new_route = insert_order_in_best_position(
                        orphan, 
                        current_route, 
                        batch_info['start_lat'], 
                        batch_info['start_lng']
                    )
                    
                    # Atualiza os stop_order de todos os pedidos dessa rota
                    for stop_num, order in enumerate(new_route, 1):
                        order.batch_id = best_batch_id
                        order.stop_order = stop_num
                        order.status = OrderStatus.ASSIGNED
                        session.add(order)
                    
                    # Atualiza o mapa
                    batch_orders_map[best_batch_id] = new_route
                    orphans_assigned += 1
        
        session.commit()
    
    # Conta pedidos que ainda ficaram sem atribuição (não deveria acontecer!)
    final_remaining = len(ready_orders) - orders_assigned - orphans_assigned
    
    message = f"{batches_created} lote(s) criado(s), {orders_assigned + orphans_assigned} pedido(s) atribuído(s)"
    if orphans_assigned > 0:
        message += f" ({orphans_assigned} adicionado(s) em rotas existentes)"
    if final_remaining > 0:
        message += f", {final_remaining} pedido(s) aguardando motoqueiro"
    
    return DispatchResult(
        batches_created=batches_created,
        orders_assigned=orders_assigned + orphans_assigned,
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
