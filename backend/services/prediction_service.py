"""
Serviço de Previsão Híbrida - Combina aprendizado histórico com tempo real

🔒 PROTEÇÃO MULTI-TENANT:
- Todos os cálculos filtram por restaurant_id

MODELO HÍBRIDO:
1. APRENDIZADO HISTÓRICO: Analisa últimas 4-6 semanas por dia/hora
2. TEMPO REAL: Compara ritmo atual com histórico
3. BALANCEAMENTO DE FLUXO: taxa_preparo vs taxa_entrega
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from collections import defaultdict
from sqlmodel import Session, select, func

from models import (
    Order, Courier, OrderStatus, CourierStatus,
    PadraoDemanda, PrevisaoHibrida
)


# ============ CONSTANTES ============

SEMANAS_HISTORICO = 4          # Quantas semanas analisar
MIN_AMOSTRAS_CONFIAVEL = 3     # Mínimo de amostras para considerar confiável
FATOR_SEGURANCA = 1.2          # Margem de segurança (20% a mais)


# ============ FUNÇÕES DE APRENDIZADO ============

def atualizar_padroes_historicos(
    session: Session,
    restaurant_id: str
) -> Dict[str, int]:
    """
    Analisa pedidos das últimas N semanas e atualiza padrões.

    🔒 Filtra por restaurant_id

    Retorna:
        {"padroes_atualizados": N, "amostras_analisadas": M}
    """
    cutoff = datetime.now() - timedelta(weeks=SEMANAS_HISTORICO)

    # Busca todos os pedidos entregues no período
    query = select(Order).where(
        Order.restaurant_id == restaurant_id,
        Order.created_at >= cutoff,
        Order.status == OrderStatus.DELIVERED,
        Order.delivered_at != None,
        Order.ready_at != None
    )
    orders = session.exec(query).all()

    if not orders:
        return {"padroes_atualizados": 0, "amostras_analisadas": 0}

    # Agrupa por dia_semana + hora
    # Estrutura: {(dia, hora): {"pedidos": [], "tempos_preparo": [], "tempos_rota": []}}
    padroes: Dict[Tuple[int, int], Dict[str, List]] = defaultdict(
        lambda: {"pedidos": [], "tempos_preparo": [], "tempos_rota": []}
    )

    # Conta pedidos por dia específico (para calcular média por hora)
    pedidos_por_dia_hora: Dict[Tuple[int, int, str], int] = defaultdict(int)

    for order in orders:
        # Dia da semana (0=Segunda, 6=Domingo)
        dia = order.created_at.weekday()
        hora = order.created_at.hour
        data_str = order.created_at.strftime("%Y-%m-%d")

        # Conta pedido neste slot
        pedidos_por_dia_hora[(dia, hora, data_str)] += 1

        # Calcula tempo de preparo (created_at → ready_at)
        if order.ready_at and order.created_at:
            tempo_preparo = (order.ready_at - order.created_at).total_seconds() / 60
            if 0 < tempo_preparo < 120:  # Entre 0 e 2 horas
                padroes[(dia, hora)]["tempos_preparo"].append(tempo_preparo)

        # Calcula tempo de rota (ready_at → delivered_at) * 1.5 para ida+volta
        if order.delivered_at and order.ready_at:
            tempo_rota = (order.delivered_at - order.ready_at).total_seconds() / 60
            if 0 < tempo_rota < 180:  # Entre 0 e 3 horas
                padroes[(dia, hora)]["tempos_rota"].append(tempo_rota * 1.5)

    # Calcula média de pedidos por hora (agrupando dias iguais)
    for (dia, hora, data_str), count in pedidos_por_dia_hora.items():
        padroes[(dia, hora)]["pedidos"].append(count)

    # Salva/atualiza padrões no banco
    padroes_atualizados = 0

    for (dia, hora), dados in padroes.items():
        if not dados["pedidos"]:
            continue

        # Calcula médias
        media_pedidos = sum(dados["pedidos"]) / len(dados["pedidos"])

        media_preparo = None
        if dados["tempos_preparo"]:
            media_preparo = sum(dados["tempos_preparo"]) / len(dados["tempos_preparo"])

        media_rota = None
        if dados["tempos_rota"]:
            media_rota = sum(dados["tempos_rota"]) / len(dados["tempos_rota"])

        # Calcula motoboys recomendados
        motoboys_rec = calcular_motoboys_necessarios(
            media_pedidos,
            media_rota or 30  # Default: 30 min
        )

        # Busca ou cria padrão existente
        padrao_existente = session.exec(
            select(PadraoDemanda).where(
                PadraoDemanda.restaurant_id == restaurant_id,
                PadraoDemanda.dia_semana == dia,
                PadraoDemanda.hora == hora
            )
        ).first()

        if padrao_existente:
            # Atualiza
            padrao_existente.media_pedidos_hora = media_pedidos
            if media_preparo:
                padrao_existente.media_tempo_preparo = media_preparo
            if media_rota:
                padrao_existente.media_tempo_rota = media_rota
            padrao_existente.motoboys_recomendados = motoboys_rec
            padrao_existente.amostras = len(dados["pedidos"])
            padrao_existente.ultima_atualizacao = datetime.now()
        else:
            # Cria novo
            novo_padrao = PadraoDemanda(
                restaurant_id=restaurant_id,
                dia_semana=dia,
                hora=hora,
                media_pedidos_hora=media_pedidos,
                media_tempo_preparo=media_preparo or 15.0,
                media_tempo_rota=media_rota or 30.0,
                motoboys_recomendados=motoboys_rec,
                amostras=len(dados["pedidos"])
            )
            session.add(novo_padrao)

        padroes_atualizados += 1

    session.commit()

    return {
        "padroes_atualizados": padroes_atualizados,
        "amostras_analisadas": len(orders)
    }


def obter_padrao_atual(
    session: Session,
    restaurant_id: str,
    dia_semana: Optional[int] = None,
    hora: Optional[int] = None
) -> Optional[PadraoDemanda]:
    """
    Busca o padrão histórico para o dia/hora especificado.
    Se não informados, usa o momento atual.
    """
    if dia_semana is None:
        dia_semana = datetime.now().weekday()
    if hora is None:
        hora = datetime.now().hour

    return session.exec(
        select(PadraoDemanda).where(
            PadraoDemanda.restaurant_id == restaurant_id,
            PadraoDemanda.dia_semana == dia_semana,
            PadraoDemanda.hora == hora
        )
    ).first()


# ============ FUNÇÕES DE TEMPO REAL ============

def contar_motoboys_tempo_real(
    session: Session,
    restaurant_id: str
) -> Tuple[int, int]:
    """Retorna (disponíveis, ocupados)"""
    query_disp = select(Courier).where(
        Courier.restaurant_id == restaurant_id,
        Courier.status == CourierStatus.AVAILABLE
    )
    disponiveis = len(session.exec(query_disp).all())

    query_ocup = select(Courier).where(
        Courier.restaurant_id == restaurant_id,
        Courier.status == CourierStatus.BUSY
    )
    ocupados = len(session.exec(query_ocup).all())

    return disponiveis, ocupados


def contar_pedidos_tempo_real(
    session: Session,
    restaurant_id: str
) -> Dict[str, int]:
    """
    Conta pedidos em diferentes estados.
    Retorna: {fila, em_rota, ultima_hora}
    """
    # Pedidos na fila (READY)
    query_fila = select(Order).where(
        Order.restaurant_id == restaurant_id,
        Order.status == OrderStatus.READY
    )
    fila = len(session.exec(query_fila).all())

    # Pedidos em rota (ASSIGNED ou PICKED_UP)
    query_rota = select(Order).where(
        Order.restaurant_id == restaurant_id,
        Order.status.in_([OrderStatus.ASSIGNED, OrderStatus.PICKED_UP])
    )
    em_rota = len(session.exec(query_rota).all())

    # Pedidos na última hora
    uma_hora = datetime.now() - timedelta(hours=1)
    query_hora = select(Order).where(
        Order.restaurant_id == restaurant_id,
        Order.created_at >= uma_hora
    )
    ultima_hora = len(session.exec(query_hora).all())

    return {
        "fila": fila,
        "em_rota": em_rota,
        "ultima_hora": ultima_hora
    }


def calcular_tempos_tempo_real(
    session: Session,
    restaurant_id: str
) -> Dict[str, Optional[float]]:
    """
    Calcula tempos médios das últimas 2 horas.
    Retorna: {preparo, rota}
    """
    cutoff = datetime.now() - timedelta(hours=2)

    # Tempo de preparo
    query_preparo = select(Order).where(
        Order.restaurant_id == restaurant_id,
        Order.ready_at != None,
        Order.created_at >= cutoff
    )
    orders_preparo = session.exec(query_preparo).all()

    tempos_preparo = []
    for order in orders_preparo:
        if order.ready_at and order.created_at:
            diff = (order.ready_at - order.created_at).total_seconds() / 60
            if 0 < diff < 120:
                tempos_preparo.append(diff)

    tempo_preparo = None
    if len(tempos_preparo) >= 2:
        tempo_preparo = sum(tempos_preparo) / len(tempos_preparo)

    # Tempo de rota
    query_rota = select(Order).where(
        Order.restaurant_id == restaurant_id,
        Order.status == OrderStatus.DELIVERED,
        Order.delivered_at != None,
        Order.ready_at != None,
        Order.ready_at >= cutoff
    )
    orders_rota = session.exec(query_rota).all()

    tempos_rota = []
    for order in orders_rota:
        if order.delivered_at and order.ready_at:
            diff = (order.delivered_at - order.ready_at).total_seconds() / 60
            if 0 < diff < 180:
                tempos_rota.append(diff * 1.5)  # Ida + volta

    tempo_rota = None
    if len(tempos_rota) >= 2:
        tempo_rota = sum(tempos_rota) / len(tempos_rota)

    return {
        "preparo": tempo_preparo,
        "rota": tempo_rota
    }


# ============ FUNÇÕES DE BALANCEAMENTO ============

def calcular_motoboys_necessarios(pedidos_hora: float, tempo_rota_min: float) -> int:
    """
    Fórmula: motoboys = pedidos_por_hora / capacidade_por_motoboy
    Onde capacidade = 60 / tempo_rota
    """
    if tempo_rota_min is None or tempo_rota_min <= 0:
        tempo_rota_min = 30  # Default

    capacidade = 60 / tempo_rota_min

    if capacidade <= 0 or pedidos_hora <= 0:
        return 1

    # Aplica fator de segurança
    return max(1, int((pedidos_hora / capacidade) * FATOR_SEGURANCA + 0.5))


def calcular_balanceamento_fluxo(
    taxa_saida_pedidos: float,      # Pedidos prontos por hora
    motoboys_disponiveis: int,
    tempo_ciclo_motoboy: float      # Tempo médio de ida+volta (min)
) -> Dict[str, Optional[float]]:
    """
    Calcula o balanceamento entre produção e entrega.

    TEORIA DE FILAS:
    - Se taxa_entrada > taxa_servico → fila cresce
    - Se taxa_entrada < taxa_servico → fila diminui

    Retorna:
        {
            "capacidade_entrega": N,      # Pedidos/hora que motoboys conseguem entregar
            "balanco": M,                 # Diferença (negativo = acumulando)
            "tempo_acumulo_min": X        # Minutos até fila começar a crescer
        }
    """
    if tempo_ciclo_motoboy is None or tempo_ciclo_motoboy <= 0:
        tempo_ciclo_motoboy = 30

    # Capacidade de entrega: quantos pedidos os motoboys conseguem entregar por hora
    entregas_por_motoboy_hora = 60 / tempo_ciclo_motoboy
    capacidade_total = motoboys_disponiveis * entregas_por_motoboy_hora

    # Balanço: positivo = sobra capacidade, negativo = falta capacidade
    balanco = capacidade_total - taxa_saida_pedidos

    # Tempo até acumular (se balanço negativo)
    tempo_acumulo = None
    if balanco < 0 and abs(balanco) > 0.1:
        # A cada hora, acumula |balanco| pedidos
        # Tempo para acumular 1 pedido = 60 / |balanco|
        tempo_acumulo = int(60 / abs(balanco))

    return {
        "capacidade_entrega": round(capacidade_total, 1),
        "balanco": round(balanco, 1),
        "tempo_acumulo_min": tempo_acumulo
    }


# ============ FUNÇÃO PRINCIPAL: PREVISÃO HÍBRIDA ============

def calcular_previsao_hibrida(
    session: Session,
    restaurant_id: str
) -> PrevisaoHibrida:
    """
    Combina dados históricos com tempo real para previsão inteligente.

    🔒 Filtra por restaurant_id

    LÓGICA:
    1. Busca padrão histórico para dia/hora atual
    2. Coleta dados em tempo real
    3. Compara atual vs histórico
    4. Calcula balanceamento de fluxo
    5. Gera recomendação final
    """
    agora = datetime.now()
    dia_semana = agora.weekday()
    hora = agora.hour

    # ===== 1. DADOS HISTÓRICOS =====
    padrao = obter_padrao_atual(session, restaurant_id, dia_semana, hora)

    historico_disponivel = padrao is not None and padrao.amostras >= MIN_AMOSTRAS_CONFIAVEL

    # ===== 2. DADOS EM TEMPO REAL =====
    disponiveis, ocupados = contar_motoboys_tempo_real(session, restaurant_id)
    total_ativos = disponiveis + ocupados

    pedidos = contar_pedidos_tempo_real(session, restaurant_id)
    tempos = calcular_tempos_tempo_real(session, restaurant_id)

    # ===== 3. COMPARAÇÃO HISTÓRICO vs ATUAL =====
    variacao_demanda = None
    if historico_disponivel and padrao.media_pedidos_hora > 0:
        variacao_demanda = (
            (pedidos["ultima_hora"] - padrao.media_pedidos_hora)
            / padrao.media_pedidos_hora
        ) * 100

    # ===== 4. BALANCEAMENTO DE FLUXO =====
    # Taxa de saída = pedidos prontos por hora (estimado)
    # Usamos pedidos na última hora como proxy
    taxa_saida = float(pedidos["ultima_hora"])

    # Tempo de ciclo: usa tempo real se disponível, senão histórico, senão default
    tempo_ciclo = tempos["rota"]
    if tempo_ciclo is None and historico_disponivel:
        tempo_ciclo = padrao.media_tempo_rota
    if tempo_ciclo is None:
        tempo_ciclo = 30.0  # Default

    balanceamento = calcular_balanceamento_fluxo(
        taxa_saida,
        disponiveis,  # Só conta disponíveis para entrega imediata
        tempo_ciclo
    )

    # ===== 5. RECOMENDAÇÃO FINAL =====
    # Combina histórico + situação atual

    motoboys_rec = None  # None = sem dados para recomendação (aparece como "-")
    status = "adequado"
    mensagem = ""
    sugestao = None

    # Verifica se há dados suficientes para uma recomendação
    tem_fila = pedidos["fila"] > 0
    tem_pedidos_recentes = pedidos["ultima_hora"] > 0

    # Se tem histórico confiável, usa como base
    if historico_disponivel:
        motoboys_base = padrao.motoboys_recomendados

        # Ajusta com base na variação de demanda
        if variacao_demanda is not None:
            if variacao_demanda > 30:
                # Demanda 30% acima do normal
                motoboys_rec = int(motoboys_base * (1 + variacao_demanda / 200))
                status = "atencao"
                mensagem = f"Demanda {variacao_demanda:.0f}% acima do normal para {_nome_dia(dia_semana)} às {hora}h"
                sugestao = f"Considere ativar {motoboys_rec - total_ativos} motoboy(s) adicional(is)"
            elif variacao_demanda < -30:
                # Demanda 30% abaixo do normal
                motoboys_rec = max(1, int(motoboys_base * (1 + variacao_demanda / 200)))
                status = "adequado"
                mensagem = f"Demanda {abs(variacao_demanda):.0f}% abaixo do normal. Operação tranquila!"
            else:
                # Demanda normal
                motoboys_rec = motoboys_base
                mensagem = f"Demanda dentro do esperado para {_nome_dia(dia_semana)} às {hora}h"
        else:
            motoboys_rec = motoboys_base
            mensagem = f"Baseado no histórico: {motoboys_base} motoboy(s) recomendado(s)"
    elif tem_fila or tem_pedidos_recentes:
        # Sem histórico mas tem atividade: calcula baseado no tempo real
        motoboys_rec = calcular_motoboys_necessarios(
            float(pedidos["ultima_hora"]) if tem_pedidos_recentes else float(pedidos["fila"]),
            tempo_ciclo
        )
        mensagem = "Ainda coletando dados históricos. Recomendação baseada no ritmo atual."
    else:
        # Sem histórico E sem atividade: não há dados para recomendar
        motoboys_rec = None
        mensagem = "Sem dados suficientes para recomendação. Aguardando mais pedidos."

    # Verifica situação crítica (fila crescendo)
    if pedidos["fila"] > 0 and disponiveis == 0:
        status = "critico" if pedidos["fila"] >= 3 else "atencao"
        mensagem = f"{pedidos['fila']} pedido(s) aguardando e nenhum motoboy disponível!"
        # Calcula recomendação urgente baseada na fila
        motoboys_rec = max(motoboys_rec or 1, (pedidos["fila"] // 2) + 1)
        sugestao = f"Ative mais motoboys AGORA! Recomendado: {motoboys_rec}"

    # Verifica balanceamento negativo
    if balanceamento["balanco"] is not None and balanceamento["balanco"] < -1:
        if status != "critico":
            status = "atencao"
        if balanceamento["tempo_acumulo_min"]:
            mensagem += f" Fila pode crescer em ~{balanceamento['tempo_acumulo_min']}min."

    # Se tem fila, garante recomendação mínima baseada na fila atual
    if tem_fila and motoboys_rec is not None:
        motoboys_rec = max(motoboys_rec, (pedidos["fila"] // 2) + 1)

    # ===== MONTA RESPOSTA =====
    return PrevisaoHibrida(
        # Histórico
        historico_pedidos_hora=padrao.media_pedidos_hora if padrao else None,
        historico_tempo_preparo=padrao.media_tempo_preparo if padrao else None,
        historico_tempo_rota=padrao.media_tempo_rota if padrao else None,
        historico_motoboys=padrao.motoboys_recomendados if padrao else None,
        historico_amostras=padrao.amostras if padrao else 0,

        # Tempo real
        atual_pedidos_hora=pedidos["ultima_hora"],
        atual_tempo_preparo=tempos["preparo"],
        atual_tempo_rota=tempos["rota"],
        atual_motoboys_ativos=total_ativos,
        atual_motoboys_disponiveis=disponiveis,
        atual_pedidos_fila=pedidos["fila"],
        atual_pedidos_em_rota=pedidos["em_rota"],

        # Balanceamento
        taxa_saida_pedidos=taxa_saida,
        capacidade_entrega=balanceamento["capacidade_entrega"],
        balanco_fluxo=balanceamento["balanco"],
        tempo_acumulo_estimado=balanceamento["tempo_acumulo_min"],

        # Comparação
        variacao_demanda_pct=round(variacao_demanda, 1) if variacao_demanda else None,

        # Recomendação
        motoboys_recomendados=motoboys_rec,
        status=status,
        mensagem=mensagem,
        sugestao_acao=sugestao,

        # Metadata
        dia_semana=dia_semana,
        hora_atual=hora,
        dados_historicos_disponiveis=historico_disponivel
    )


def _nome_dia(dia: int) -> str:
    """Retorna nome do dia da semana em português"""
    dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    return dias[dia] if 0 <= dia <= 6 else str(dia)
