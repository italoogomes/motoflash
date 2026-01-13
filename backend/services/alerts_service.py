"""
Serviço de Alertas - Gera alertas inteligentes em tempo real
"""
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass, field
from enum import Enum
from sqlmodel import Session, select

from models import Order, Courier, OrderStatus, CourierStatus
from services.metrics_service import (
    calcular_tempo_preparo, 
    calcular_tempo_rota, 
    contar_pedidos_hora,
    contar_motoboys,
    calcular_motoboys_necessarios
)


class TipoAlerta(Enum):
    CRITICO = "critico"
    ATENCAO = "atencao"
    INFO = "info"
    SUCESSO = "sucesso"


class StatusGeral(Enum):
    CRITICO = "critico"
    ATENCAO = "atencao"
    INFO = "info"
    SUCESSO = "sucesso"


@dataclass
class Alerta:
    tipo: TipoAlerta
    titulo: str
    mensagem: str
    icone: str
    acao_sugerida: Optional[str] = None
    valor: Optional[int] = None


@dataclass
class ResultadoAlertas:
    status_geral: StatusGeral
    motoboys_sugeridos: int
    alertas: List[Alerta]
    timestamp: datetime = field(default_factory=datetime.now)


# ============ CONFIGURAÇÕES DE THRESHOLD ============

FILA_ATENCAO = 3      # Alerta amarelo se 3+ pedidos na fila
FILA_CRITICO = 5      # Alerta vermelho se 5+ pedidos na fila
OCIOSIDADE_ALERTA = 50  # % de motoboys ociosos para alertar


def gerar_alertas(session: Session) -> ResultadoAlertas:
    """
    Analisa o estado atual e gera alertas
    
    LÓGICA PRINCIPAL:
    - Se tem pedidos prontos e motoboys disponíveis suficientes → Só executar dispatch
    - Se tem pedidos prontos e poucos motoboys disponíveis → Alerta
    - Se não tem pedidos prontos → Tudo OK
    """
    alertas: List[Alerta] = []
    status_geral = StatusGeral.SUCESSO
    
    # ===== Coleta de dados =====
    
    # Pedidos na fila (prontos, aguardando motoboy)
    pedidos_fila = len(session.exec(
        select(Order).where(Order.status == OrderStatus.READY)
    ).all())
    
    # Motoboys
    disponiveis, ocupados = contar_motoboys(session)
    total_ativos = disponiveis + ocupados
    
    # ===== CENÁRIO 1: Nenhum motoboy ativo e tem pedidos =====
    if total_ativos == 0 and pedidos_fila > 0:
        alertas.append(Alerta(
            tipo=TipoAlerta.CRITICO,
            titulo="Nenhum motoboy ativo!",
            mensagem=f"{pedidos_fila} pedido(s) pronto(s) e nenhum motoboy para entregar",
            icone="🚫",
            acao_sugerida="Ative motoboys AGORA para iniciar as entregas",
            valor=pedidos_fila
        ))
        return ResultadoAlertas(
            status_geral=StatusGeral.CRITICO,
            motoboys_sugeridos=max(1, (pedidos_fila // 2) + 1),
            alertas=alertas
        )
    
    # ===== CENÁRIO 2: Tem pedidos prontos =====
    if pedidos_fila > 0:
        
        # 2A: Tem motoboys DISPONÍVEIS suficientes → Só precisa executar dispatch
        if disponiveis >= pedidos_fila:
            alertas.append(Alerta(
                tipo=TipoAlerta.INFO,
                titulo="Pedidos prontos para sair!",
                mensagem=f"{pedidos_fila} pedido(s) pronto(s), {disponiveis} motoboy(s) disponível(is)",
                icone="🚀",
                acao_sugerida="Execute o dispatch para enviar os pedidos",
                valor=pedidos_fila
            ))
            status_geral = StatusGeral.INFO
        
        # 2B: Alguns motoboys disponíveis, mas não suficientes
        elif disponiveis > 0:
            faltam = pedidos_fila - disponiveis
            alertas.append(Alerta(
                tipo=TipoAlerta.ATENCAO,
                titulo="Mais pedidos que motoboys livres",
                mensagem=f"{pedidos_fila} pedido(s) pronto(s), mas só {disponiveis} motoboy(s) disponível(is)",
                icone="⚠️",
                acao_sugerida=f"Execute o dispatch. Quando os ocupados voltarem, envie o resto. Ou ative mais {faltam}.",
                valor=faltam
            ))
            status_geral = StatusGeral.ATENCAO
        
        # 2C: Nenhum motoboy disponível (todos ocupados)
        else:
            alertas.append(Alerta(
                tipo=TipoAlerta.ATENCAO,
                titulo="Motoboys todos ocupados",
                mensagem=f"{pedidos_fila} pedido(s) aguardando, {ocupados} motoboy(s) em entrega",
                icone="⏳",
                acao_sugerida="Aguarde os motoboys retornarem ou ative mais motoboys",
                valor=pedidos_fila
            ))
            status_geral = StatusGeral.ATENCAO
    
    # ===== CENÁRIO 3: Sem pedidos prontos =====
    else:
        # Verifica se tem pedidos em rota (operação ativa)
        pedidos_em_rota = len(session.exec(
            select(Order).where(Order.status.in_([OrderStatus.ASSIGNED, OrderStatus.PICKED_UP]))
        ).all())
        
        if pedidos_em_rota > 0:
            # Operação ativa, tudo fluindo
            alertas.append(Alerta(
                tipo=TipoAlerta.SUCESSO,
                titulo="Operação fluindo bem!",
                mensagem=f"{pedidos_em_rota} pedido(s) em rota, nenhum acumulado",
                icone="✅",
                acao_sugerida=None,
                valor=0
            ))
        else:
            # Sem operação ativa
            alertas.append(Alerta(
                tipo=TipoAlerta.SUCESSO,
                titulo="Operação normal",
                mensagem="Nenhum pedido aguardando",
                icone="✅",
                acao_sugerida=None,
                valor=0
            ))
        status_geral = StatusGeral.SUCESSO
    
    # Calcula sugestão de motoboys baseado na situação ATUAL
    if pedidos_fila > 0:
        # Precisa de pelo menos 1 motoboy para cada 2 pedidos
        motoboys_sugeridos = max(disponiveis, (pedidos_fila // 2) + 1)
    else:
        motoboys_sugeridos = total_ativos if total_ativos > 0 else 1
    
    return ResultadoAlertas(
        status_geral=status_geral,
        motoboys_sugeridos=motoboys_sugeridos,
        alertas=alertas
    )


def calcular_previsao_motoboys(session: Session) -> dict:
    """
    Calcula recomendação de motoboys baseado na situação ATUAL
    
    LÓGICA SIMPLES:
    - Olha quantos pedidos PRONTOS tem agora
    - Olha quantos motoboys DISPONÍVEIS tem agora
    - Se disponíveis >= prontos → Adequado
    - Se disponíveis < prontos → Precisa de mais
    """
    # Dados atuais
    tempo_preparo, amostras_preparo = calcular_tempo_preparo(session)
    tempo_rota, amostras_rota = calcular_tempo_rota(session)
    pedidos_hora = contar_pedidos_hora(session)
    disponiveis, ocupados = contar_motoboys(session)
    total_ativos = disponiveis + ocupados
    
    # Pedidos na fila (READY esperando)
    pedidos_fila = len(session.exec(
        select(Order).where(Order.status == OrderStatus.READY)
    ).all())
    
    # Pedidos em rota
    pedidos_em_rota = len(session.exec(
        select(Order).where(Order.status.in_([OrderStatus.ASSIGNED, OrderStatus.PICKED_UP]))
    ).all())
    
    # Capacidade por motoboy (se tiver dados)
    capacidade = None
    if tempo_rota and tempo_rota > 0:
        capacidade = round(60 / tempo_rota, 1)
    
    # ===== LÓGICA DE RECOMENDAÇÃO =====
    
    # Se não tem pedidos na fila
    if pedidos_fila == 0:
        return {
            "motoboys_recomendados": total_ativos if total_ativos > 0 else None,
            "motoboys_atuais": total_ativos,
            "motoboys_disponiveis": disponiveis,
            "status": "adequado",
            "mensagem": "Nenhum pedido aguardando. Tudo OK!",
            "tempo_medio_preparo": round(tempo_preparo, 1) if tempo_preparo else None,
            "tempo_medio_rota": round(tempo_rota, 1) if tempo_rota else None,
            "pedidos_por_hora": pedidos_hora,
            "capacidade_por_motoboy": capacidade,
            "pedidos_na_fila": 0,
            "pedidos_em_rota": pedidos_em_rota,
            "dados_suficientes": amostras_rota >= 5,
            "timestamp": datetime.now().isoformat()
        }
    
    # Tem pedidos na fila - calcula recomendação
    # Cada motoboy pode pegar até 2 pedidos por viagem
    motoboys_necessarios = (pedidos_fila // 2) + (1 if pedidos_fila % 2 else 0)
    motoboys_necessarios = max(1, motoboys_necessarios)
    
    # Verifica situação
    if disponiveis >= pedidos_fila:
        # Tem motoboys suficientes disponíveis
        status = "adequado"
        mensagem = f"Execute o dispatch! {disponiveis} motoboy(s) para {pedidos_fila} pedido(s)"
    elif disponiveis > 0:
        # Tem alguns, mas não suficientes
        faltam = motoboys_necessarios - disponiveis
        if faltam > 0:
            status = "atencao"
            mensagem = f"Pode precisar de mais {faltam} motoboy(s), ou aguarde os ocupados voltarem"
        else:
            status = "adequado"
            mensagem = "Execute o dispatch!"
    else:
        # Nenhum disponível
        if ocupados > 0:
            status = "atencao"
            mensagem = f"Aguarde os {ocupados} motoboy(s) em rota voltarem, ou ative mais"
        else:
            status = "critico"
            mensagem = f"Ative pelo menos {motoboys_necessarios} motoboy(s)!"
    
    return {
        "motoboys_recomendados": motoboys_necessarios,
        "motoboys_atuais": total_ativos,
        "motoboys_disponiveis": disponiveis,
        "status": status,
        "mensagem": mensagem,
        "tempo_medio_preparo": round(tempo_preparo, 1) if tempo_preparo else None,
        "tempo_medio_rota": round(tempo_rota, 1) if tempo_rota else None,
        "pedidos_por_hora": pedidos_hora,
        "capacidade_por_motoboy": capacidade,
        "pedidos_na_fila": pedidos_fila,
        "pedidos_em_rota": pedidos_em_rota,
        "dados_suficientes": amostras_rota >= 5,
        "timestamp": datetime.now().isoformat()
    }
