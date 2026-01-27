"""
Testes do Algoritmo de Dispatch

Cobre:
- Execução básica do dispatch
- Agrupamento de pedidos próximos
- Atribuição de motoboys
- Isolamento multi-tenant
"""
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from models import Order, Courier, Batch, OrderStatus, CourierStatus, BatchStatus


# ============ TESTES DE EXECUÇÃO BÁSICA ============

def test_dispatch_com_pedidos_e_motoboys(
    client: TestClient,
    auth_headers: dict,
    test_orders_ready: list,
    test_couriers_available: list
):
    """
    Testa execução básica do dispatch com pedidos READY e motoboys AVAILABLE

    Resultado esperado: Cria lotes e atribui pedidos
    """
    response = client.post("/dispatch/run", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert data["batches_created"] > 0
    assert data["orders_assigned"] > 0
    assert "lote(s) criado(s)" in data["message"]


def test_dispatch_sem_pedidos_ready(
    client: TestClient,
    auth_headers: dict,
    test_couriers_available: list
):
    """
    Testa dispatch quando não há pedidos READY

    Resultado esperado: Retorna mensagem indicando que não há pedidos
    """
    response = client.post("/dispatch/run", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert data["batches_created"] == 0
    assert data["orders_assigned"] == 0
    assert "Nenhum pedido pronto aguardando" in data["message"]


def test_dispatch_sem_motoboys_disponiveis(
    client: TestClient,
    auth_headers: dict,
    test_orders_ready: list,
    session: Session
):
    """
    Testa dispatch quando não há motoboys AVAILABLE

    Resultado esperado: Retorna mensagem indicando falta de motoboys
    """
    # Marca todos os motoboys como OFFLINE
    couriers = session.exec(select(Courier)).all()
    for courier in couriers:
        courier.status = CourierStatus.OFFLINE
        session.add(courier)
    session.commit()

    response = client.post("/dispatch/run", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert data["batches_created"] == 0
    assert data["orders_assigned"] == 0
    assert "nenhum motoqueiro disponível" in data["message"]


def test_dispatch_sem_autenticacao(client: TestClient, test_orders_ready: list):
    """
    Testa dispatch sem token JWT

    Resultado esperado: Status 401
    """
    response = client.post("/dispatch/run")

    assert response.status_code == 401


# ============ TESTES DE AGRUPAMENTO ============

def test_pedidos_proximos_sao_agrupados(
    client: TestClient,
    auth_headers: dict,
    session: Session,
    test_orders_ready: list,
    test_couriers_available: list
):
    """
    Testa se pedidos próximos (< 3km) são agrupados no mesmo lote

    Fixture tem 2 grupos de 2 pedidos próximos cada
    """
    response = client.post("/dispatch/run", headers=auth_headers)

    assert response.status_code == 200

    # Verifica os lotes criados
    batches = session.exec(select(Batch)).all()

    # Deve criar pelo menos 1 lote (pode agrupar todos ou separar distantes)
    assert len(batches) >= 1

    # Verifica que pelo menos um lote tem mais de 1 pedido (agrupamento funcionou)
    batch_with_multiple = []
    for batch in batches:
        orders = session.exec(
            select(Order).where(Order.batch_id == batch.id)
        ).all()
        if len(orders) > 1:
            batch_with_multiple.append(batch)

    assert len(batch_with_multiple) > 0


def test_respeita_maximo_de_pedidos_por_lote(
    client: TestClient,
    auth_headers: dict,
    session: Session,
    test_restaurant
):
    """
    Testa que o dispatch respeita o máximo de 6 pedidos por lote
    """
    from models import Order, OrderStatus, PrepType
    from datetime import datetime

    # Cria 8 pedidos no MESMO local (mesmo endereço)
    orders = []
    for i in range(8):
        order = Order(
            customer_name=f"Cliente {i}",
            address_text="Rua Teste, 100",
            lat=-23.550520,
            lng=-46.633308,
            prep_type=PrepType.SHORT,
            status=OrderStatus.READY,
            ready_at=datetime.now(),
            restaurant_id=test_restaurant.id
        )
        session.add(order)
        orders.append(order)
    session.commit()

    # Cria 2 motoboys disponíveis (necessário para 8 pedidos / max 6 por lote)
    from services.auth_service import hash_password
    courier1 = Courier(
        name="Motoboy",
        last_name="Um",
        phone="11999999991",
        password_hash=hash_password("teste123"),
        status=CourierStatus.AVAILABLE,
        restaurant_id=test_restaurant.id
    )
    courier2 = Courier(
        name="Motoboy",
        last_name="Dois",
        phone="11999999992",
        password_hash=hash_password("teste123"),
        status=CourierStatus.AVAILABLE,
        restaurant_id=test_restaurant.id
    )
    session.add(courier1)
    session.add(courier2)
    session.commit()

    response = client.post("/dispatch/run", headers=auth_headers)

    assert response.status_code == 200

    # Verifica os lotes criados
    batches = session.exec(select(Batch)).all()

    # Deve criar pelo menos 2 lotes (8 pedidos não cabem em 1 lote de máx 6)
    assert len(batches) >= 2

    # Verifica que nenhum lote tem mais de 6 pedidos
    for batch in batches:
        orders = session.exec(
            select(Order).where(Order.batch_id == batch.id)
        ).all()
        assert len(orders) <= 6


# ============ TESTES DE ATRIBUIÇÃO ============

def test_motoboy_fica_busy_apos_dispatch(
    client: TestClient,
    auth_headers: dict,
    session: Session,
    test_orders_ready: list,
    test_couriers_available: list
):
    """
    Testa se motoboys ficam BUSY após receberem lote
    """
    response = client.post("/dispatch/run", headers=auth_headers)

    assert response.status_code == 200

    # Recarrega os motoboys do banco
    couriers = session.exec(select(Courier)).all()

    # Pelo menos um motoboy deve estar BUSY
    busy_couriers = [c for c in couriers if c.status == CourierStatus.BUSY]
    assert len(busy_couriers) > 0


def test_pedidos_ficam_assigned_apos_dispatch(
    client: TestClient,
    auth_headers: dict,
    session: Session,
    test_orders_ready: list,
    test_couriers_available: list
):
    """
    Testa se pedidos ficam ASSIGNED após dispatch
    """
    response = client.post("/dispatch/run", headers=auth_headers)

    assert response.status_code == 200

    # Recarrega os pedidos do banco
    orders = session.exec(select(Order)).all()

    # Todos os pedidos que estavam READY devem estar ASSIGNED
    assigned_orders = [o for o in orders if o.status == OrderStatus.ASSIGNED]
    assert len(assigned_orders) > 0


def test_batch_criado_com_dados_corretos(
    client: TestClient,
    auth_headers: dict,
    session: Session,
    test_orders_ready: list,
    test_couriers_available: list
):
    """
    Testa se o batch é criado com os dados corretos
    """
    response = client.post("/dispatch/run", headers=auth_headers)

    assert response.status_code == 200

    # Busca o batch criado
    batch = session.exec(select(Batch)).first()

    assert batch is not None
    assert batch.courier_id is not None
    assert batch.restaurant_id is not None
    assert batch.status == BatchStatus.ASSIGNED
    assert batch.created_at is not None

    # Verifica que tem pedidos associados
    orders = session.exec(
        select(Order).where(Order.batch_id == batch.id)
    ).all()
    assert len(orders) > 0


def test_ordem_de_paradas_correta(
    client: TestClient,
    auth_headers: dict,
    session: Session,
    test_orders_ready: list,
    test_couriers_available: list
):
    """
    Testa se os pedidos têm stop_order sequencial (1, 2, 3, ...)
    """
    response = client.post("/dispatch/run", headers=auth_headers)

    assert response.status_code == 200

    # Busca o batch criado
    batch = session.exec(select(Batch)).first()

    assert batch is not None

    # Pega os pedidos ordenados
    orders = session.exec(
        select(Order)
        .where(Order.batch_id == batch.id)
        .order_by(Order.stop_order)
    ).all()

    # Verifica que stop_order é sequencial
    for i, order in enumerate(orders, start=1):
        assert order.stop_order == i


# ============ TESTES DE ISOLAMENTO MULTI-TENANT ============

def test_dispatch_isolamento_pedidos(
    client: TestClient,
    auth_headers: dict,
    session: Session,
    test_orders_ready: list,
    test_couriers_available: list
):
    """
    Testa se dispatch só pega pedidos do próprio restaurante

    Cria pedidos de outro restaurante e verifica que não são atribuídos
    """
    from models import Restaurant, Order, OrderStatus, PrepType
    from datetime import datetime

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

    # Cria pedido do outro restaurante (READY)
    other_order = Order(
        customer_name="Cliente Outro",
        address_text="Rua Outro, 789",
        lat=-23.550520,
        lng=-46.633308,
        prep_type=PrepType.SHORT,
        status=OrderStatus.READY,
        ready_at=datetime.now(),
        restaurant_id=other_restaurant.id
    )
    session.add(other_order)
    session.commit()
    session.refresh(other_order)

    response = client.post("/dispatch/run", headers=auth_headers)

    assert response.status_code == 200

    # Recarrega o pedido do outro restaurante
    session.refresh(other_order)

    # O pedido do outro restaurante NÃO deve ter sido atribuído
    assert other_order.status == OrderStatus.READY
    assert other_order.batch_id is None


def test_dispatch_isolamento_motoboys(
    client: TestClient,
    auth_headers: dict,
    session: Session,
    test_orders_ready: list
):
    """
    Testa se dispatch só atribui motoboys do próprio restaurante

    Cria motoboy de outro restaurante e verifica que não é usado
    """
    from models import Restaurant
    from services.auth_service import hash_password
    from datetime import datetime

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

    # Cria motoboy do outro restaurante (AVAILABLE)
    other_courier = Courier(
        name="Motoboy",
        last_name="Outro",
        phone="11999999999",
        password_hash=hash_password("teste123"),
        status=CourierStatus.AVAILABLE,
        available_since=datetime.now(),
        restaurant_id=other_restaurant.id
    )
    session.add(other_courier)
    session.commit()
    session.refresh(other_courier)

    response = client.post("/dispatch/run", headers=auth_headers)

    assert response.status_code == 200

    # Recarrega o motoboy do outro restaurante
    session.refresh(other_courier)

    # O motoboy do outro restaurante NÃO deve ter sido usado
    assert other_courier.status == CourierStatus.AVAILABLE

    # Verifica que não foi criado batch para ele
    batches = session.exec(
        select(Batch).where(Batch.courier_id == other_courier.id)
    ).all()
    assert len(batches) == 0


# ============ TESTES DE ENDPOINTS ============

def test_listar_batches_ativos(
    client: TestClient,
    auth_headers: dict,
    test_orders_ready: list,
    test_couriers_available: list
):
    """
    Testa listagem de batches ativos
    """
    # Executa dispatch primeiro
    client.post("/dispatch/run", headers=auth_headers)

    # Lista batches
    response = client.get("/dispatch/batches", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) > 0

    # Verifica estrutura do batch
    batch = data[0]
    assert "id" in batch
    assert "courier_id" in batch
    assert "courier_name" in batch
    assert "status" in batch
    assert "orders" in batch
    assert isinstance(batch["orders"], list)


def test_stats_endpoint(
    client: TestClient,
    auth_headers: dict,
    test_orders_ready: list,
    test_couriers_available: list
):
    """
    Testa endpoint de estatísticas
    """
    response = client.get("/dispatch/stats", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert "orders" in data
    assert "couriers" in data
    assert "active_batches" in data
    assert "pending_orders" in data
    assert "available_couriers" in data
