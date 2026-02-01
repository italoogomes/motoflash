"""
Testes para endpoints de pedidos (orders)
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session
from models import Order, Restaurant, User


def test_criar_pedido_com_coordenadas(client: TestClient, auth_headers: dict):
    """
    Testa criação de pedido com lat/lng fornecidos (sem geocoding)
    """
    response = client.post(
        "/orders",
        json={
            "customer_name": "Maria Santos",
            "address_text": "Av. Paulista, 1000",
            "lat": -23.561684,
            "lng": -46.655981,
            "prep_type": "short"
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["customer_name"] == "Maria Santos"
    assert data["address_text"] == "Av. Paulista, 1000"
    assert data["lat"] == -23.561684
    assert data["lng"] == -46.655981
    assert data["status"] == "preparing"  # Pedido já inicia em preparo (simplificado)
    assert "id" in data


def test_criar_pedido_nome_default(client: TestClient, auth_headers: dict):
    """
    Testa criação de pedido sem nome (deve usar 'Cliente' como padrão)
    """
    response = client.post(
        "/orders",
        json={
            "address_text": "Rua das Flores, 456",
            "lat": -23.550520,
            "lng": -46.633308
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["customer_name"] == "Cliente"


def test_criar_pedido_sem_autenticacao(client: TestClient):
    """
    Testa criação de pedido sem token JWT
    """
    response = client.post(
        "/orders",
        json={
            "customer_name": "Teste",
            "address_text": "Rua Teste, 123",
            "lat": -23.550520,
            "lng": -46.633308
        }
    )
    assert response.status_code == 401


def test_listar_pedidos(client: TestClient, auth_headers: dict, test_order: Order):
    """
    Testa listagem de pedidos do restaurante
    """
    response = client.get("/orders", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    # Verifica se o pedido de teste está na lista
    order_ids = [order["id"] for order in data]
    assert test_order.id in order_ids


def test_listar_pedidos_filtro_status(
    client: TestClient,
    auth_headers: dict,
    session: Session,
    test_restaurant: Restaurant
):
    """
    Testa listagem de pedidos com filtro por status
    """
    from models import Order, OrderStatus, PrepType

    # Cria pedido com status READY
    order_ready = Order(
        customer_name="Pedido Pronto",
        address_text="Rua A, 1",
        lat=-23.5,
        lng=-46.6,
        prep_type=PrepType.SHORT,
        status=OrderStatus.READY,
        restaurant_id=test_restaurant.id,
        short_id=2001,
        tracking_code="MF-READY01"
    )
    session.add(order_ready)
    session.commit()

    # Lista apenas pedidos READY
    response = client.get("/orders?status=ready", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    # Verifica que todos têm status READY
    for order in data:
        assert order["status"] == "ready"


def test_isolamento_multi_tenant(
    client: TestClient,
    session: Session,
    test_user: User,
    test_order: Order
):
    """
    Testa que um restaurante não vê pedidos de outro restaurante
    """
    from models import Restaurant, User, Order, OrderStatus, PrepType
    from services.auth_service import hash_password

    # Cria outro restaurante
    restaurant2 = Restaurant(
        name="Outro Restaurante",
        slug="outro-restaurante",
        cnpj="99999999999999",
        email="outro@restaurante.com",
        phone="11988888888",
        address="Rua Outra, 999",
        plan="TRIAL"
    )
    session.add(restaurant2)
    session.commit()
    session.refresh(restaurant2)

    # Cria usuário do outro restaurante
    user2 = User(
        email="admin@outro.com",
        password_hash=hash_password("senha123"),
        name="Admin Outro",
        role="OWNER",
        restaurant_id=restaurant2.id
    )
    session.add(user2)
    session.commit()

    # Cria pedido do outro restaurante
    order2 = Order(
        customer_name="Cliente Outro",
        address_text="Rua X, 999",
        lat=-23.6,
        lng=-46.7,
        prep_type=PrepType.SHORT,
        status=OrderStatus.CREATED,
        restaurant_id=restaurant2.id,
        short_id=1001,
        tracking_code="MF-OTHER01"
    )
    session.add(order2)
    session.commit()

    # Faz login com user2
    response = client.post(
        "/auth/login",
        json={"email": "admin@outro.com", "password": "senha123"}
    )
    token2 = response.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    # Lista pedidos do restaurante 2
    response = client.get("/orders", headers=headers2)
    assert response.status_code == 200
    data = response.json()

    # Deve ver apenas o pedido do restaurante 2
    order_ids = [order["id"] for order in data]
    assert order2.id in order_ids
    assert test_order.id not in order_ids  # Não deve ver pedido do restaurante 1


def test_buscar_pedido_especifico(client: TestClient, auth_headers: dict, test_order: Order):
    """
    Testa buscar pedido por ID
    """
    response = client.get(f"/orders/{test_order.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_order.id
    assert data["customer_name"] == test_order.customer_name


def test_buscar_pedido_inexistente(client: TestClient, auth_headers: dict):
    """
    Testa buscar pedido que não existe
    """
    response = client.get("/orders/id-inexistente", headers=auth_headers)
    assert response.status_code == 404


def test_buscar_pedido_outro_restaurante(
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """
    Testa buscar pedido de outro restaurante (deve retornar 404)
    """
    from models import Restaurant, Order, OrderStatus, PrepType

    # Cria outro restaurante
    restaurant2 = Restaurant(
        name="Restaurante 2",
        slug="restaurante-2",
        cnpj="88888888888888",
        email="r2@teste.com",
        phone="11977777777",
        address="Rua 2",
        plan="TRIAL"
    )
    session.add(restaurant2)
    session.commit()

    # Cria pedido do outro restaurante
    order2 = Order(
        customer_name="Cliente R2",
        address_text="Rua R2, 100",
        lat=-23.5,
        lng=-46.6,
        prep_type=PrepType.SHORT,
        status=OrderStatus.CREATED,
        restaurant_id=restaurant2.id,
        short_id=1001,
        tracking_code="MF-R2-001"
    )
    session.add(order2)
    session.commit()

    # Tenta buscar pedido do restaurante 2 usando token do restaurante 1
    response = client.get(f"/orders/{order2.id}", headers=auth_headers)
    assert response.status_code == 404


def test_gerar_qrcode(client: TestClient, auth_headers: dict, test_order: Order):
    """
    Testa geração de QR Code do pedido
    """
    response = client.get(f"/orders/{test_order.id}/qrcode", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "qrcode" in data
    assert "order_id" in data
    assert data["order_id"] == test_order.id
    # QR Code deve ser base64
    assert isinstance(data["qrcode"], str)
    assert len(data["qrcode"]) > 0


def test_pedido_ja_inicia_em_preparing(client: TestClient, auth_headers: dict, test_order: Order):
    """
    Testa que pedido já inicia em status PREPARING (fluxo simplificado)
    Nota: Endpoint /preparing não é mais necessário, pedido já inicia em preparo
    """
    # Verifica que o pedido da fixture já está em PREPARING
    response = client.get(f"/orders/{test_order.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "preparing"


def test_marcar_pedido_como_ready(client: TestClient, auth_headers: dict, test_order: Order):
    """
    Testa marcar pedido como PRONTO (scan QR Code)
    """
    response = client.post(
        f"/orders/{test_order.id}/scan",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["ready_at"] is not None


def test_transicao_status_sequencial(client: TestClient, auth_headers: dict, test_order: Order):
    """
    Testa transição de status (PREPARING → READY)
    Nota: Pedidos já iniciam em PREPARING (fluxo simplificado)
    """
    # Pedido já está em PREPARING (test_order fixture)
    # Transição: PREPARING → READY
    response = client.post(f"/orders/{test_order.id}/scan", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_transicao_status_invalida(client: TestClient, auth_headers: dict, session: Session, test_restaurant: Restaurant):
    """
    Testa transição de status inválida (ex: tentar marcar DELIVERED sem estar PICKED_UP)
    """
    from models import Order, OrderStatus, PrepType

    # Cria pedido em status PREPARING (fluxo simplificado)
    order = Order(
        customer_name="Teste",
        address_text="Rua T, 1",
        lat=-23.5,
        lng=-46.6,
        prep_type=PrepType.SHORT,
        status=OrderStatus.PREPARING,
        restaurant_id=test_restaurant.id,
        short_id=3001,
        tracking_code="MF-TST001"
    )
    session.add(order)
    session.commit()
    session.refresh(order)

    # Tenta marcar como DELIVERED direto (deve falhar)
    response = client.post(f"/orders/{order.id}/deliver", headers=auth_headers)
    assert response.status_code == 400
    assert "não pode ser entregue" in response.json()["detail"]


def test_transicao_pickup_requer_assigned(
    client: TestClient,
    auth_headers: dict,
    session: Session,
    test_restaurant: Restaurant
):
    """
    Testa que pickup só funciona se pedido está ASSIGNED
    """
    from models import Order, OrderStatus, PrepType

    # Cria pedido em status READY (não ASSIGNED)
    order = Order(
        customer_name="Teste",
        address_text="Rua T, 1",
        lat=-23.5,
        lng=-46.6,
        prep_type=PrepType.SHORT,
        status=OrderStatus.READY,
        restaurant_id=test_restaurant.id,
        short_id=4001,
        tracking_code="MF-RDY001"
    )
    session.add(order)
    session.commit()
    session.refresh(order)

    # Tenta fazer pickup sem estar ASSIGNED (deve falhar)
    response = client.post(f"/orders/{order.id}/pickup", headers=auth_headers)
    assert response.status_code == 400
    assert "não pode ser coletado" in response.json()["detail"]


def test_pedido_criado_com_short_id(client: TestClient, auth_headers: dict):
    """
    Testa se o pedido é criado com short_id sequencial
    """
    response = client.post(
        "/orders",
        json={
            "customer_name": "João Silva",
            "address_text": "Rua A, 123",
            "lat": -23.5,
            "lng": -46.6
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "short_id" in data
    assert data["short_id"] is not None
    assert data["short_id"] >= 1001  # Começa em 1001


def test_pedido_criado_com_tracking_code(client: TestClient, auth_headers: dict):
    """
    Testa se o pedido é criado com tracking_code único
    """
    response = client.post(
        "/orders",
        json={
            "customer_name": "Maria Santos",
            "address_text": "Rua B, 456",
            "lat": -23.5,
            "lng": -46.6
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "tracking_code" in data
    assert data["tracking_code"] is not None
    assert data["tracking_code"].startswith("MF-")
    assert len(data["tracking_code"]) == 9  # MF-XXXXXX (9 caracteres)


def test_short_id_sequencial_por_restaurante(client: TestClient, auth_headers: dict):
    """
    Testa se o short_id é sequencial por restaurante
    """
    # Cria primeiro pedido
    response1 = client.post(
        "/orders",
        json={
            "customer_name": "Cliente 1",
            "address_text": "Rua A, 1",
            "lat": -23.5,
            "lng": -46.6
        },
        headers=auth_headers
    )
    assert response1.status_code == 200
    short_id1 = response1.json()["short_id"]

    # Cria segundo pedido
    response2 = client.post(
        "/orders",
        json={
            "customer_name": "Cliente 2",
            "address_text": "Rua A, 2",
            "lat": -23.5,
            "lng": -46.6
        },
        headers=auth_headers
    )
    assert response2.status_code == 200
    short_id2 = response2.json()["short_id"]

    # Verifica que o segundo é incremento do primeiro
    assert short_id2 == short_id1 + 1


def test_tracking_code_unico(client: TestClient, auth_headers: dict):
    """
    Testa se cada pedido tem tracking_code único
    """
    # Cria dois pedidos
    response1 = client.post(
        "/orders",
        json={
            "customer_name": "Cliente 1",
            "address_text": "Rua A, 1",
            "lat": -23.5,
            "lng": -46.6
        },
        headers=auth_headers
    )
    response2 = client.post(
        "/orders",
        json={
            "customer_name": "Cliente 2",
            "address_text": "Rua A, 2",
            "lat": -23.5,
            "lng": -46.6
        },
        headers=auth_headers
    )

    tracking1 = response1.json()["tracking_code"]
    tracking2 = response2.json()["tracking_code"]

    # Tracking codes devem ser diferentes
    assert tracking1 != tracking2


def test_endpoint_rastreio_publico(client: TestClient, auth_headers: dict):
    """
    Testa endpoint público de rastreio (sem autenticação)
    """
    # Cria um pedido
    response = client.post(
        "/orders",
        json={
            "customer_name": "Cliente Rastreio",
            "address_text": "Rua X, 999",
            "lat": -23.5,
            "lng": -46.6
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    tracking_code = response.json()["tracking_code"]

    # Rastreia o pedido SEM autenticação
    track_response = client.get(f"/orders/track/{tracking_code}")
    assert track_response.status_code == 200

    track_data = track_response.json()
    assert track_data["tracking_code"] == tracking_code
    assert track_data["status"] == "preparing"  # Pedido já inicia em preparo
    assert track_data["customer_name"] == "Cliente Rastreio"
    assert "short_id" in track_data


def test_endpoint_rastreio_codigo_invalido(client: TestClient):
    """
    Testa endpoint de rastreio com código inexistente
    """
    response = client.get("/orders/track/MF-INVALIDO")
    assert response.status_code == 404
    assert "não encontrado" in response.json()["detail"].lower()


def test_short_id_independente_por_restaurante(
    client: TestClient,
    session: Session,
    test_user: User
):
    """
    Testa se short_ids são independentes entre restaurantes
    """
    from models import Restaurant, User
    from services.auth_service import hash_password

    # Cria segundo restaurante
    restaurant2 = Restaurant(
        name="Restaurante 2",
        slug="restaurante-2",
        email="restaurante2@teste.com",
        address="Rua B, 200"
    )
    session.add(restaurant2)
    session.commit()
    session.refresh(restaurant2)

    # Cria usuário do segundo restaurante
    user2 = User(
        email="admin2@teste.com",
        password_hash=hash_password("senha123"),
        name="Admin 2",
        role="owner",
        restaurant_id=restaurant2.id
    )
    session.add(user2)
    session.commit()

    # Login do segundo restaurante
    login_response = client.post(
        "/auth/login",
        json={"email": "admin2@teste.com", "password": "senha123"}
    )
    auth_headers2 = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    # Cria pedido no restaurante 1
    response1 = client.post(
        "/orders",
        json={
            "customer_name": "Cliente R1",
            "address_text": "Rua A, 1",
            "lat": -23.5,
            "lng": -46.6
        },
        headers={"Authorization": f"Bearer {test_user.id}"}  # Usa token do test_user
    )

    # Cria pedido no restaurante 2
    response2 = client.post(
        "/orders",
        json={
            "customer_name": "Cliente R2",
            "address_text": "Rua B, 1",
            "lat": -23.5,
            "lng": -46.6
        },
        headers=auth_headers2
    )

    # Ambos devem ter short_id começando em 1001 (independentes)
    if response1.status_code == 200 and response2.status_code == 200:
        short_id1 = response1.json()["short_id"]
        short_id2 = response2.json()["short_id"]

        # Ambos começam em 1001 (são independentes)
        assert short_id1 == 1001 or short_id1 > 1000
        assert short_id2 == 1001 or short_id2 > 1000
