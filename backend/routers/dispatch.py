"""
Rotas de Dispatch (Despacho/Distribuição)

🔒 PROTEÇÃO MULTI-TENANT:
- Dispatch roda apenas para pedidos/motoboys do restaurante logado
- Stats, Alerts, Metrics filtram por restaurant_id
- Batches são vinculados ao restaurant_id
"""
from typing import List
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from database import get_session
from models import (
    Batch, BatchResponse, BatchStatus, Order, Courier, DispatchResult,
    User, OrderStatus, CourierStatus
)
from services.dispatch_service import run_dispatch, get_batch_orders
from services.auth_service import get_current_user

router = APIRouter(prefix="/dispatch", tags=["Despacho"])


@router.post("/run", response_model=DispatchResult)
def execute_dispatch(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Executa o algoritmo de dispatch
    
    🔒 Roda apenas para pedidos e motoboys do restaurante logado
    """
    result = run_dispatch(session, restaurant_id=current_user.restaurant_id)
    return result


@router.get("/batches", response_model=List[BatchResponse])
def list_active_batches(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Lista todos os lotes ativos do restaurante
    
    🔒 Filtra por restaurant_id
    """
    # 🔒 PROTEÇÃO: filtra batches pelo restaurant_id
    batches = session.exec(
        select(Batch)
        .where(Batch.status.in_([BatchStatus.ASSIGNED, BatchStatus.IN_PROGRESS]))
        .where(Batch.restaurant_id == current_user.restaurant_id)
        .order_by(Batch.created_at.desc())
    ).all()
    
    result = []
    for batch in batches:
        courier = session.get(Courier, batch.courier_id)
        orders = get_batch_orders(session, batch.id)
        
        result.append(BatchResponse(
            id=batch.id,
            courier_id=batch.courier_id,
            courier_name=courier.full_name if courier else None,
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
        ))
    
    return result


@router.get("/stats")
def get_dispatch_stats(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Retorna estatísticas do sistema
    
    🔒 Filtra por restaurant_id
    """
    restaurant_id = current_user.restaurant_id
    
    # Conta pedidos por status (do restaurante)
    orders_by_status = {}
    for status in OrderStatus:
        count = session.exec(
            select(Order)
            .where(Order.status == status)
            .where(Order.restaurant_id == restaurant_id)  # 🔒
        ).all()
        orders_by_status[status.value] = len(count)
    
    # Conta motoqueiros por status (do restaurante)
    couriers_by_status = {}
    for status in CourierStatus:
        count = session.exec(
            select(Courier)
            .where(Courier.status == status)
            .where(Courier.restaurant_id == restaurant_id)  # 🔒
        ).all()
        couriers_by_status[status.value] = len(count)
    
    # Lotes ativos (do restaurante)
    active_batches = session.exec(
        select(Batch)
        .where(Batch.status.in_([BatchStatus.ASSIGNED, BatchStatus.IN_PROGRESS]))
        .where(Batch.restaurant_id == restaurant_id)  # 🔒
    ).all()
    
    return {
        "orders": orders_by_status,
        "couriers": couriers_by_status,
        "active_batches": len(active_batches),
        "pending_orders": orders_by_status.get("ready", 0),
        "available_couriers": couriers_by_status.get("available", 0)
    }


@router.get("/alerts")
def get_alerts(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    🚨 Retorna alertas em tempo real
    
    🔒 Filtra por restaurant_id
    """
    from services.alerts_service import gerar_alertas
    
    resultado = gerar_alertas(session, restaurant_id=current_user.restaurant_id)
    
    return {
        "status_geral": resultado.status_geral.value,
        "motoboys_sugeridos": resultado.motoboys_sugeridos,
        "alertas": [
            {
                "tipo": a.tipo.value,
                "titulo": a.titulo,
                "mensagem": a.mensagem,
                "icone": a.icone,
                "acao_sugerida": a.acao_sugerida,
                "valor": a.valor
            }
            for a in resultado.alertas
        ],
        "timestamp": resultado.timestamp.isoformat()
    }


@router.get("/metrics")
def get_metrics(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    📊 Retorna métricas detalhadas do sistema
    
    🔒 Filtra por restaurant_id
    """
    from services.metrics_service import obter_metricas_completas
    
    metricas = obter_metricas_completas(session, restaurant_id=current_user.restaurant_id)
    
    return {
        "preparo": {
            "media_short_min": round(metricas.preparo.media_short, 1) if metricas.preparo.media_short else None,
            "media_long_min": round(metricas.preparo.media_long, 1) if metricas.preparo.media_long else None,
            "media_geral_min": round(metricas.preparo.media_geral, 1) if metricas.preparo.media_geral else None,
            "amostras_short": metricas.preparo.amostras_short,
            "amostras_long": metricas.preparo.amostras_long,
        },
        "rota": {
            "media_minutos": round(metricas.rota.media_minutos, 1) if metricas.rota.media_minutos else None,
            "amostras": metricas.rota.amostras,
        },
        "capacidade": {
            "pedidos_ultima_hora": metricas.capacidade.pedidos_ultima_hora,
            "pedidos_por_hora": metricas.capacidade.pedidos_por_hora,
            "motoboys_disponiveis": metricas.capacidade.motoboys_disponiveis,
            "motoboys_ocupados": metricas.capacidade.motoboys_ocupados,
            "motoboys_total_ativos": metricas.capacidade.motoboys_total_ativos,
            "capacidade_por_motoboy": round(metricas.capacidade.capacidade_por_motoboy, 1),
            "motoboys_necessarios": metricas.capacidade.motoboys_necessarios,
            "deficit_motoboys": metricas.capacidade.deficit_motoboys,
        },
        "pedidos_aguardando": metricas.pedidos_aguardando,
        "timestamp": metricas.timestamp.isoformat()
    }


@router.get("/recommendation")
def get_motoboy_recommendation(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    💡 Retorna recomendação de quantos motoboys são necessários
    
    🔒 Filtra por restaurant_id
    """
    from services.alerts_service import calcular_previsao_motoboys
    
    return calcular_previsao_motoboys(session, restaurant_id=current_user.restaurant_id)


@router.get("/test-google-optimization")
def test_google_optimization():
    """
    🧪 Testa a otimização de rota via Google Directions API
    
    Não precisa de autenticação (é só um teste)
    """
    from services.dispatch_service import optimize_route_with_google, GOOGLE_MAPS_API_KEY
    import httpx
    
    # Coordenadas de teste - Rua General Osório em Ribeirão Preto
    test_points = [
        {"name": "General Osório 750", "lat": -21.1770, "lng": -47.8073},
        {"name": "General Osório 450", "lat": -21.1775, "lng": -47.8080},
        {"name": "General Osório 300", "lat": -21.1780, "lng": -47.8087},
    ]
    
    # Restaurante (origem)
    start_lat = -21.1645
    start_lng = -47.8224
    
    # Chama a API diretamente para teste
    origin = f"{start_lat},{start_lng}"
    waypoints = "|".join([f"{p['lat']},{p['lng']}" for p in test_points])
    
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": origin,
        "destination": origin,
        "waypoints": f"optimize:true|{waypoints}",
        "mode": "driving",
        "language": "pt-BR",
        "key": GOOGLE_MAPS_API_KEY
    }
    
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, params=params)
            data = response.json()
        
        status = data.get("status")
        waypoint_order = data.get("routes", [{}])[0].get("waypoint_order", [])
        
        # Interpreta a ordem
        if waypoint_order:
            optimized = [test_points[i]["name"] for i in waypoint_order]
        else:
            optimized = []
        
        return {
            "api_status": status,
            "api_key_used": GOOGLE_MAPS_API_KEY[:20] + "...",
            "original_order": [p["name"] for p in test_points],
            "waypoint_order_from_google": waypoint_order,
            "optimized_order": optimized,
            "expected_order": ["General Osório 300", "General Osório 450", "General Osório 750"],
            "is_correct": optimized == ["General Osório 300", "General Osório 450", "General Osório 750"],
            "raw_response_status": status,
            "error_message": data.get("error_message"),
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "api_key_used": GOOGLE_MAPS_API_KEY[:20] + "...",
        }
