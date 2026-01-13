"""
Rotas de Dispatch (Despacho/Distribuição)
"""
from typing import List
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from database import get_session
from models import (
    Batch, BatchResponse, BatchStatus, Order, Courier, DispatchResult
)
from services.dispatch_service import run_dispatch, get_batch_orders
from services.metrics_service import obter_metricas_completas
from services.alerts_service import gerar_alertas, calcular_previsao_motoboys

router = APIRouter(prefix="/dispatch", tags=["Despacho"])


@router.post("/run", response_model=DispatchResult)
def execute_dispatch(session: Session = Depends(get_session)):
    """
    Executa o algoritmo de dispatch
    
    Este endpoint:
    1. Pega todos os pedidos PRONTOS (QR bipado) nos últimos 7 minutos
    2. Agrupa por proximidade geográfica
    3. Distribui para motoqueiros disponíveis
    
    Chame periodicamente (ex: a cada 30 segundos) ou 
    manualmente quando precisar forçar distribuição.
    """
    result = run_dispatch(session)
    return result


@router.get("/batches", response_model=List[BatchResponse])
def list_active_batches(session: Session = Depends(get_session)):
    """
    Lista todos os lotes ativos (não concluídos)
    """
    batches = session.exec(
        select(Batch)
        .where(Batch.status.in_([BatchStatus.ASSIGNED, BatchStatus.IN_PROGRESS]))
        .order_by(Batch.created_at.desc())
    ).all()
    
    result = []
    for batch in batches:
        courier = session.get(Courier, batch.courier_id)
        orders = get_batch_orders(session, batch.id)
        
        result.append(BatchResponse(
            id=batch.id,
            courier_id=batch.courier_id,
            courier_name=courier.name if courier else None,
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
def get_dispatch_stats(session: Session = Depends(get_session)):
    """
    Retorna estatísticas do sistema
    
    Útil para o painel do restaurante.
    """
    from models import OrderStatus, CourierStatus
    
    # Conta pedidos por status
    orders_by_status = {}
    for status in OrderStatus:
        count = session.exec(
            select(Order).where(Order.status == status)
        ).all()
        orders_by_status[status.value] = len(count)
    
    # Conta motoqueiros por status
    couriers_by_status = {}
    for status in CourierStatus:
        count = session.exec(
            select(Courier).where(Courier.status == status)
        ).all()
        couriers_by_status[status.value] = len(count)
    
    # Lotes ativos
    active_batches = session.exec(
        select(Batch).where(Batch.status.in_([BatchStatus.ASSIGNED, BatchStatus.IN_PROGRESS]))
    ).all()
    
    return {
        "orders": orders_by_status,
        "couriers": couriers_by_status,
        "active_batches": len(active_batches),
        "pending_orders": orders_by_status.get("ready", 0),
        "available_couriers": couriers_by_status.get("available", 0)
    }


@router.get("/alerts")
def get_alerts(session: Session = Depends(get_session)):
    """
    🚨 Retorna alertas em tempo real
    
    Analisa a situação atual e retorna alertas como:
    - Pedidos acumulando
    - Falta de motoboys
    - Risco de fila
    - Motoboys ociosos
    
    Tipos de alerta:
    - critico: precisa agir AGORA (vermelho)
    - atencao: ficar de olho (amarelo)
    - info: informativo (azul)
    - sucesso: tudo bem (verde)
    """
    resultado = gerar_alertas(session)
    
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
def get_metrics(session: Session = Depends(get_session)):
    """
    📊 Retorna métricas detalhadas do sistema
    
    Inclui:
    - Tempos médios de preparo (SHORT e LONG)
    - Tempo médio de rota
    - Capacidade vs demanda
    - Pedidos aguardando
    """
    metricas = obter_metricas_completas(session)
    
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
def get_motoboy_recommendation(session: Session = Depends(get_session)):
    """
    💡 Retorna recomendação de quantos motoboys são necessários
    
    Baseado em:
    - Taxa atual de pedidos
    - Tempo médio de rota
    - Histórico de preparo
    
    Retorna a recomendação com justificativa.
    """
    return calcular_previsao_motoboys(session)
