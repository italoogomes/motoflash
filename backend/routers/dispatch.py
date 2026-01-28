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
    User, OrderStatus, CourierStatus, get_courier_full_name
)
from services.dispatch_service import run_dispatch, get_batch_orders
from services.auth_service import get_current_user
from services.prediction_service import (
    calcular_previsao_hibrida,
    atualizar_padroes_historicos,
    obter_padrao_atual
)

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
            courier_name=get_courier_full_name(courier) if courier else None,
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


# ============ PREVISÃO HÍBRIDA ============

@router.get("/previsao")
def get_previsao_hibrida(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    🔮 Previsão Híbrida de Motoboys

    Combina dados históricos (padrão do dia/hora) com situação em tempo real
    para fornecer recomendação inteligente de quantos motoboys ativar.

    🔒 Filtra por restaurant_id

    RETORNO:
    - Dados históricos (se disponíveis)
    - Dados em tempo real
    - Balanceamento de fluxo (taxa preparo vs taxa entrega)
    - Comparação histórico vs atual (variação %)
    - Recomendação final de motoboys
    - Status (adequado/atencao/critico)
    - Mensagem explicativa
    """
    previsao = calcular_previsao_hibrida(session, restaurant_id=current_user.restaurant_id)

    return {
        # Dados históricos
        "historico": {
            "pedidos_hora": previsao.historico_pedidos_hora,
            "tempo_preparo_min": previsao.historico_tempo_preparo,
            "tempo_rota_min": previsao.historico_tempo_rota,
            "motoboys_recomendados": previsao.historico_motoboys,
            "amostras": previsao.historico_amostras,
            "disponivel": previsao.dados_historicos_disponiveis
        },

        # Dados em tempo real
        "atual": {
            "pedidos_hora": previsao.atual_pedidos_hora,
            "tempo_preparo_min": previsao.atual_tempo_preparo,
            "tempo_rota_min": previsao.atual_tempo_rota,
            "motoboys_ativos": previsao.atual_motoboys_ativos,
            "motoboys_disponiveis": previsao.atual_motoboys_disponiveis,
            "pedidos_fila": previsao.atual_pedidos_fila,
            "pedidos_em_rota": previsao.atual_pedidos_em_rota
        },

        # Balanceamento de fluxo
        "balanceamento": {
            "taxa_saida_pedidos": previsao.taxa_saida_pedidos,
            "capacidade_entrega": previsao.capacidade_entrega,
            "balanco_fluxo": previsao.balanco_fluxo,
            "tempo_acumulo_min": previsao.tempo_acumulo_estimado
        },

        # Comparação
        "comparacao": {
            "variacao_demanda_pct": previsao.variacao_demanda_pct
        },

        # Recomendação final
        "recomendacao": {
            "motoboys": previsao.motoboys_recomendados,
            "status": previsao.status,
            "mensagem": previsao.mensagem,
            "sugestao_acao": previsao.sugestao_acao
        },

        # Metadata
        "dia_semana": previsao.dia_semana,
        "hora_atual": previsao.hora_atual,
        "timestamp": previsao.timestamp.isoformat()
    }


@router.post("/atualizar-padroes")
def atualizar_padroes(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    📚 Atualiza Padrões Históricos

    Analisa os pedidos das últimas 4 semanas e atualiza os padrões
    de demanda por dia da semana e hora.

    🔒 Filtra por restaurant_id

    USE QUANDO:
    - Após período inicial de coleta de dados
    - Semanalmente para manter padrões atualizados
    - Após mudanças significativas na operação

    RETORNO:
    - Quantidade de padrões atualizados
    - Quantidade de pedidos analisados
    """
    resultado = atualizar_padroes_historicos(session, restaurant_id=current_user.restaurant_id)

    return {
        "sucesso": True,
        "padroes_atualizados": resultado["padroes_atualizados"],
        "pedidos_analisados": resultado["amostras_analisadas"],
        "mensagem": f"Padrões atualizados! {resultado['padroes_atualizados']} slots de dia/hora processados."
    }


@router.get("/padroes")
def listar_padroes(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    📊 Lista Padrões Históricos

    Retorna todos os padrões de demanda aprendidos para o restaurante.

    🔒 Filtra por restaurant_id

    Útil para visualizar:
    - Quais dias/horas são mais movimentados
    - Tempo médio de preparo e rota por período
    - Quantidade de motoboys recomendada por período
    """
    from models import PadraoDemanda

    padroes = session.exec(
        select(PadraoDemanda)
        .where(PadraoDemanda.restaurant_id == current_user.restaurant_id)
        .order_by(PadraoDemanda.dia_semana, PadraoDemanda.hora)
    ).all()

    dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]

    return {
        "total_padroes": len(padroes),
        "padroes": [
            {
                "dia_semana": p.dia_semana,
                "dia_nome": dias[p.dia_semana] if 0 <= p.dia_semana <= 6 else str(p.dia_semana),
                "hora": p.hora,
                "media_pedidos_hora": round(p.media_pedidos_hora, 1),
                "media_tempo_preparo_min": round(p.media_tempo_preparo, 1),
                "media_tempo_rota_min": round(p.media_tempo_rota, 1),
                "motoboys_recomendados": p.motoboys_recomendados,
                "amostras": p.amostras,
                "ultima_atualizacao": p.ultima_atualizacao.isoformat()
            }
            for p in padroes
        ]
    }
