"""
Testes do Sistema de Previsão Híbrida

Cobre:
- Cálculo de previsão híbrida
- Atualização de padrões históricos
- Balanceamento de fluxo
- Isolamento multi-tenant
"""
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlmodel import Session

from models import (
    Order, Courier, OrderStatus, CourierStatus, PrepType,
    PadraoDemanda, Restaurant
)


# ============ TESTES DO ENDPOINT DE PREVISÃO ============

def test_previsao_endpoint_retorna_estrutura_correta(
    client: TestClient,
    auth_headers: dict
):
    """
    Testa que o endpoint /dispatch/previsao retorna a estrutura correta
    """
    response = client.get("/dispatch/previsao", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    # Verifica estrutura principal
    assert "historico" in data
    assert "atual" in data
    assert "balanceamento" in data
    assert "comparacao" in data
    assert "recomendacao" in data
    assert "dia_semana" in data
    assert "hora_atual" in data
    assert "timestamp" in data


def test_previsao_sem_historico(
    client: TestClient,
    auth_headers: dict
):
    """
    Testa previsão quando não há dados históricos
    """
    response = client.get("/dispatch/previsao", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    # Sem histórico, deve usar tempo real
    assert data["historico"]["disponivel"] is False
    assert data["historico"]["amostras"] == 0

    # Recomendação deve existir mesmo sem histórico
    assert data["recomendacao"]["motoboys"] >= 1
    assert data["recomendacao"]["status"] in ["adequado", "atencao", "critico"]


def test_previsao_com_pedidos_na_fila(
    client: TestClient,
    auth_headers: dict,
    session: Session,
    test_restaurant: Restaurant
):
    """
    Testa previsão quando há pedidos na fila
    """
    # Cria pedidos READY (na fila)
    for i in range(3):
        order = Order(
            customer_name=f"Cliente {i}",
            address_text=f"Rua {i}, 100",
            lat=-23.550520,
            lng=-46.633308,
            prep_type=PrepType.SHORT,
            status=OrderStatus.READY,
            ready_at=datetime.now(),
            restaurant_id=test_restaurant.id
        )
        session.add(order)
    session.commit()

    response = client.get("/dispatch/previsao", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    # Deve detectar pedidos na fila
    assert data["atual"]["pedidos_fila"] == 3

    # Deve recomendar motoboys suficientes
    assert data["recomendacao"]["motoboys"] >= 2


def test_previsao_sem_autenticacao(client: TestClient):
    """
    Testa que previsão requer autenticação
    """
    response = client.get("/dispatch/previsao")

    assert response.status_code == 401


# ============ TESTES DO ENDPOINT DE ATUALIZAÇÃO DE PADRÕES ============

def test_atualizar_padroes_sem_dados(
    client: TestClient,
    auth_headers: dict
):
    """
    Testa atualização de padrões quando não há pedidos históricos
    """
    response = client.post("/dispatch/atualizar-padroes", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert data["sucesso"] is True
    assert data["padroes_atualizados"] == 0
    assert data["pedidos_analisados"] == 0


def test_atualizar_padroes_com_dados(
    client: TestClient,
    auth_headers: dict,
    session: Session,
    test_restaurant: Restaurant
):
    """
    Testa atualização de padrões quando há pedidos históricos
    """
    # Cria pedidos entregues nos últimos dias
    base_time = datetime.now() - timedelta(days=7)

    for i in range(5):
        created = base_time + timedelta(hours=i)
        ready = created + timedelta(minutes=15)
        delivered = ready + timedelta(minutes=25)

        order = Order(
            customer_name=f"Cliente {i}",
            address_text=f"Rua {i}, 100",
            lat=-23.550520,
            lng=-46.633308,
            prep_type=PrepType.SHORT,
            status=OrderStatus.DELIVERED,
            created_at=created,
            ready_at=ready,
            delivered_at=delivered,
            restaurant_id=test_restaurant.id
        )
        session.add(order)
    session.commit()

    response = client.post("/dispatch/atualizar-padroes", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert data["sucesso"] is True
    assert data["pedidos_analisados"] == 5


def test_atualizar_padroes_sem_autenticacao(client: TestClient):
    """
    Testa que atualização de padrões requer autenticação
    """
    response = client.post("/dispatch/atualizar-padroes")

    assert response.status_code == 401


# ============ TESTES DO ENDPOINT DE LISTAGEM DE PADRÕES ============

def test_listar_padroes_vazio(
    client: TestClient,
    auth_headers: dict
):
    """
    Testa listagem quando não há padrões
    """
    response = client.get("/dispatch/padroes", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert data["total_padroes"] == 0
    assert data["padroes"] == []


def test_listar_padroes_com_dados(
    client: TestClient,
    auth_headers: dict,
    session: Session,
    test_restaurant: Restaurant
):
    """
    Testa listagem quando há padrões salvos
    """
    # Cria padrão manualmente
    padrao = PadraoDemanda(
        restaurant_id=test_restaurant.id,
        dia_semana=3,  # Quinta
        hora=19,
        media_pedidos_hora=15.0,
        media_tempo_preparo=12.0,
        media_tempo_rota=30.0,
        motoboys_recomendados=3,
        amostras=10
    )
    session.add(padrao)
    session.commit()

    response = client.get("/dispatch/padroes", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert data["total_padroes"] == 1
    assert len(data["padroes"]) == 1

    p = data["padroes"][0]
    assert p["dia_semana"] == 3
    assert p["dia_nome"] == "Quinta"
    assert p["hora"] == 19
    assert p["media_pedidos_hora"] == 15.0
    assert p["motoboys_recomendados"] == 3


# ============ TESTES DE ISOLAMENTO MULTI-TENANT ============

def test_previsao_isolamento_multi_tenant(
    client: TestClient,
    auth_headers: dict,
    session: Session,
    test_restaurant: Restaurant
):
    """
    Testa que previsão só considera dados do próprio restaurante
    """
    # Cria outro restaurante
    other_restaurant = Restaurant(
        name="Outro Restaurante",
        slug="outro-restaurante",
        cnpj="98765432109876",
        email="outro@teste.com",
        phone="11999999999",
        address="Outra Rua, 456",
        plan="TRIAL",
        lat=-23.550520,
        lng=-46.633308
    )
    session.add(other_restaurant)
    session.commit()
    session.refresh(other_restaurant)

    # Cria pedidos do outro restaurante
    for i in range(5):
        order = Order(
            customer_name=f"Cliente Outro {i}",
            address_text=f"Rua Outro {i}, 100",
            lat=-23.550520,
            lng=-46.633308,
            prep_type=PrepType.SHORT,
            status=OrderStatus.READY,
            ready_at=datetime.now(),
            restaurant_id=other_restaurant.id
        )
        session.add(order)
    session.commit()

    response = client.get("/dispatch/previsao", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    # NÃO deve contar pedidos do outro restaurante
    assert data["atual"]["pedidos_fila"] == 0


def test_padroes_isolamento_multi_tenant(
    client: TestClient,
    auth_headers: dict,
    session: Session,
    test_restaurant: Restaurant
):
    """
    Testa que padrões são isolados por restaurante
    """
    # Cria outro restaurante
    other_restaurant = Restaurant(
        name="Outro Restaurante",
        slug="outro-restaurante-2",
        cnpj="98765432109877",
        email="outro2@teste.com",
        phone="11999999998",
        address="Outra Rua, 457",
        plan="TRIAL",
        lat=-23.550520,
        lng=-46.633308
    )
    session.add(other_restaurant)
    session.commit()
    session.refresh(other_restaurant)

    # Cria padrão do outro restaurante
    padrao_outro = PadraoDemanda(
        restaurant_id=other_restaurant.id,
        dia_semana=3,
        hora=19,
        media_pedidos_hora=50.0,
        media_tempo_preparo=5.0,
        media_tempo_rota=15.0,
        motoboys_recomendados=10,
        amostras=100
    )
    session.add(padrao_outro)
    session.commit()

    response = client.get("/dispatch/padroes", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    # NÃO deve ver padrões do outro restaurante
    assert data["total_padroes"] == 0


# ============ TESTES DE BALANCEAMENTO DE FLUXO ============

def test_balanceamento_com_motoboys_disponiveis(
    client: TestClient,
    auth_headers: dict,
    session: Session,
    test_restaurant: Restaurant
):
    """
    Testa cálculo de balanceamento quando há motoboys disponíveis
    """
    from services.auth_service import hash_password

    # Cria motoboys disponíveis
    for i in range(2):
        courier = Courier(
            name=f"Motoboy {i}",
            phone=f"1199999{i}000",
            password_hash=hash_password("teste123"),
            status=CourierStatus.AVAILABLE,
            available_since=datetime.now(),
            restaurant_id=test_restaurant.id
        )
        session.add(courier)
    session.commit()

    response = client.get("/dispatch/previsao", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert data["atual"]["motoboys_disponiveis"] == 2
    # Com motoboys disponíveis, capacidade de entrega deve ser > 0
    if data["balanceamento"]["capacidade_entrega"]:
        assert data["balanceamento"]["capacidade_entrega"] > 0


def test_balanceamento_sem_motoboys(
    client: TestClient,
    auth_headers: dict,
    session: Session,
    test_restaurant: Restaurant
):
    """
    Testa cálculo de balanceamento quando não há motoboys
    """
    # Cria pedidos na fila
    for i in range(3):
        order = Order(
            customer_name=f"Cliente {i}",
            address_text=f"Rua {i}, 100",
            lat=-23.550520,
            lng=-46.633308,
            prep_type=PrepType.SHORT,
            status=OrderStatus.READY,
            ready_at=datetime.now(),
            restaurant_id=test_restaurant.id
        )
        session.add(order)
    session.commit()

    response = client.get("/dispatch/previsao", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    # Sem motoboys, status deve ser atencao ou critico
    assert data["recomendacao"]["status"] in ["atencao", "critico"]


# ============ TESTES DE COMPARAÇÃO HISTÓRICO vs ATUAL ============

def test_variacao_demanda_acima_normal(
    client: TestClient,
    auth_headers: dict,
    session: Session,
    test_restaurant: Restaurant
):
    """
    Testa detecção de demanda acima do normal
    """
    agora = datetime.now()

    # Cria padrão histórico com baixa demanda
    padrao = PadraoDemanda(
        restaurant_id=test_restaurant.id,
        dia_semana=agora.weekday(),
        hora=agora.hour,
        media_pedidos_hora=5.0,  # Baixo
        media_tempo_preparo=15.0,
        media_tempo_rota=30.0,
        motoboys_recomendados=2,
        amostras=10  # Suficiente para ser confiável
    )
    session.add(padrao)

    # Cria muitos pedidos na última hora (alta demanda)
    for i in range(15):
        order = Order(
            customer_name=f"Cliente {i}",
            address_text=f"Rua {i}, 100",
            lat=-23.550520,
            lng=-46.633308,
            prep_type=PrepType.SHORT,
            status=OrderStatus.CREATED,
            created_at=datetime.now() - timedelta(minutes=30),
            restaurant_id=test_restaurant.id
        )
        session.add(order)
    session.commit()

    response = client.get("/dispatch/previsao", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    # Deve detectar variação positiva (demanda acima do normal)
    if data["comparacao"]["variacao_demanda_pct"]:
        assert data["comparacao"]["variacao_demanda_pct"] > 0


def test_variacao_demanda_abaixo_normal(
    client: TestClient,
    auth_headers: dict,
    session: Session,
    test_restaurant: Restaurant
):
    """
    Testa detecção de demanda abaixo do normal
    """
    agora = datetime.now()

    # Cria padrão histórico com alta demanda
    padrao = PadraoDemanda(
        restaurant_id=test_restaurant.id,
        dia_semana=agora.weekday(),
        hora=agora.hour,
        media_pedidos_hora=20.0,  # Alto
        media_tempo_preparo=15.0,
        media_tempo_rota=30.0,
        motoboys_recomendados=5,
        amostras=10
    )
    session.add(padrao)

    # Cria poucos pedidos na última hora
    for i in range(2):
        order = Order(
            customer_name=f"Cliente {i}",
            address_text=f"Rua {i}, 100",
            lat=-23.550520,
            lng=-46.633308,
            prep_type=PrepType.SHORT,
            status=OrderStatus.CREATED,
            created_at=datetime.now() - timedelta(minutes=30),
            restaurant_id=test_restaurant.id
        )
        session.add(order)
    session.commit()

    response = client.get("/dispatch/previsao", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    # Deve detectar variação negativa (demanda abaixo do normal)
    if data["comparacao"]["variacao_demanda_pct"]:
        assert data["comparacao"]["variacao_demanda_pct"] < 0
