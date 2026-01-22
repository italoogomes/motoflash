"""
Serviço de Métricas - Calcula tempos e capacidades

🔒 PROTEÇÃO MULTI-TENANT:
- Todas as métricas filtram por restaurant_id
"""
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass
from sqlmodel import Session, select

from models import Order, Courier, OrderStatus, CourierStatus, PrepType


@dataclass
class MetricasPreparo:
    media_short: Optional[float]
    media_long: Optional[float]
    media_geral: Optional[float]
    amostras_short: int
    amostras_long: int


@dataclass
class MetricasRota:
    media_minutos: Optional[float]
    amostras: int


@dataclass
class MetricasCapacidade:
    pedidos_ultima_hora: int
    pedidos_por_hora: float
    motoboys_disponiveis: int
    motoboys_ocupados: int
    motoboys_total_ativos: int
    capacidade_por_motoboy: float
    motoboys_necessarios: int
    deficit_motoboys: int


@dataclass
class MetricasCompletas:
    preparo: MetricasPreparo
    rota: MetricasRota
    capacidade: MetricasCapacidade
    pedidos_aguardando: int
    timestamp: datetime


# ============ FUNÇÕES DE CÁLCULO ============

def calcular_tempo_preparo(
    session: Session, 
    prep_type: Optional[PrepType] = None,
    restaurant_id: str = None  # 🔒 PROTEÇÃO
) -> tuple[Optional[float], int]:
    """
    Calcula tempo médio de preparo (created_at → ready_at)
    Retorna (média em minutos, quantidade de amostras)
    """
    cutoff = datetime.now() - timedelta(hours=24)
    
    query = select(Order).where(
        Order.ready_at != None,
        Order.created_at >= cutoff
    )
    
    # 🔒 Filtra por restaurante
    if restaurant_id:
        query = query.where(Order.restaurant_id == restaurant_id)
    
    if prep_type:
        query = query.where(Order.prep_type == prep_type)
    
    orders = session.exec(query).all()
    
    tempos = []
    for order in orders:
        if order.ready_at and order.created_at:
            diff = (order.ready_at - order.created_at).total_seconds() / 60
            if 0 < diff < 120:  # Entre 0 e 2 horas
                tempos.append(diff)
    
    if len(tempos) < 2:
        return None, len(tempos)
    
    return sum(tempos) / len(tempos), len(tempos)


def calcular_tempo_rota(
    session: Session,
    restaurant_id: str = None  # 🔒 PROTEÇÃO
) -> tuple[Optional[float], int]:
    """
    Calcula tempo médio de rota (ready_at → delivered_at) * 1.5 para ida+volta
    """
    cutoff = datetime.now() - timedelta(hours=24)
    
    query = select(Order).where(
        Order.status == OrderStatus.DELIVERED,
        Order.delivered_at != None,
        Order.ready_at != None,
        Order.ready_at >= cutoff
    )
    
    # 🔒 Filtra por restaurante
    if restaurant_id:
        query = query.where(Order.restaurant_id == restaurant_id)
    
    orders = session.exec(query).all()
    
    tempos = []
    for order in orders:
        if order.delivered_at and order.ready_at:
            diff = (order.delivered_at - order.ready_at).total_seconds() / 60
            if 0 < diff < 180:
                tempos.append(diff * 1.5)  # Multiplica por 1.5 para considerar volta
    
    if len(tempos) < 2:
        return None, len(tempos)
    
    return sum(tempos) / len(tempos), len(tempos)


def contar_pedidos_hora(
    session: Session,
    restaurant_id: str = None  # 🔒 PROTEÇÃO
) -> int:
    """Conta pedidos na última hora"""
    uma_hora = datetime.now() - timedelta(hours=1)
    
    query = select(Order).where(Order.created_at >= uma_hora)
    
    # 🔒 Filtra por restaurante
    if restaurant_id:
        query = query.where(Order.restaurant_id == restaurant_id)
    
    orders = session.exec(query).all()
    return len(orders)


def contar_motoboys(
    session: Session,
    restaurant_id: str = None  # 🔒 PROTEÇÃO
) -> tuple[int, int]:
    """Retorna (disponíveis, ocupados)"""
    
    # Query disponíveis
    query_disp = select(Courier).where(Courier.status == CourierStatus.AVAILABLE)
    if restaurant_id:
        query_disp = query_disp.where(Courier.restaurant_id == restaurant_id)
    disponiveis = len(session.exec(query_disp).all())
    
    # Query ocupados
    query_ocup = select(Courier).where(Courier.status == CourierStatus.BUSY)
    if restaurant_id:
        query_ocup = query_ocup.where(Courier.restaurant_id == restaurant_id)
    ocupados = len(session.exec(query_ocup).all())
    
    return disponiveis, ocupados


def calcular_motoboys_necessarios(pedidos_hora: float, tempo_rota_min: float) -> int:
    """
    Fórmula: motoboys = pedidos_por_hora / capacidade_por_motoboy
    Onde capacidade = 60 / tempo_rota
    """
    if tempo_rota_min is None or tempo_rota_min <= 0:
        tempo_rota_min = 30  # Padrão
    
    capacidade = 60 / tempo_rota_min
    
    if capacidade <= 0 or pedidos_hora <= 0:
        return 1
    
    return max(1, int(pedidos_hora / capacidade + 0.9))


def obter_metricas_completas(
    session: Session,
    restaurant_id: str = None  # 🔒 PROTEÇÃO
) -> MetricasCompletas:
    """Retorna todas as métricas consolidadas"""
    
    # Preparo
    media_short, amostras_short = calcular_tempo_preparo(session, PrepType.SHORT, restaurant_id)
    media_long, amostras_long = calcular_tempo_preparo(session, PrepType.LONG, restaurant_id)
    media_geral, _ = calcular_tempo_preparo(session, None, restaurant_id)
    
    # Rota
    tempo_rota, amostras_rota = calcular_tempo_rota(session, restaurant_id)
    
    # Capacidade
    pedidos_hora = contar_pedidos_hora(session, restaurant_id)
    disponiveis, ocupados = contar_motoboys(session, restaurant_id)
    total_ativos = disponiveis + ocupados
    
    # Capacidade por motoboy (entregas/hora)
    if tempo_rota and tempo_rota > 0:
        capacidade_motoboy = 60 / tempo_rota
    else:
        capacidade_motoboy = 2.0  # Padrão: 2 entregas/hora
    
    motoboys_necessarios = calcular_motoboys_necessarios(pedidos_hora, tempo_rota or 30)
    deficit = max(0, motoboys_necessarios - total_ativos)
    
    # Pedidos aguardando
    query_aguardando = select(Order).where(Order.status == OrderStatus.READY)
    if restaurant_id:
        query_aguardando = query_aguardando.where(Order.restaurant_id == restaurant_id)
    aguardando = len(session.exec(query_aguardando).all())
    
    return MetricasCompletas(
        preparo=MetricasPreparo(
            media_short=media_short,
            media_long=media_long,
            media_geral=media_geral,
            amostras_short=amostras_short,
            amostras_long=amostras_long
        ),
        rota=MetricasRota(
            media_minutos=tempo_rota,
            amostras=amostras_rota
        ),
        capacidade=MetricasCapacidade(
            pedidos_ultima_hora=pedidos_hora,
            pedidos_por_hora=float(pedidos_hora),
            motoboys_disponiveis=disponiveis,
            motoboys_ocupados=ocupados,
            motoboys_total_ativos=total_ativos,
            capacidade_por_motoboy=capacidade_motoboy,
            motoboys_necessarios=motoboys_necessarios,
            deficit_motoboys=deficit
        ),
        pedidos_aguardando=aguardando,
        timestamp=datetime.now()
    )
