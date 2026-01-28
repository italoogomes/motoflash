"""
Configuração de fixtures para testes do MotoFlash
"""
import pytest
import os
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

# Configura variáveis de ambiente para testes ANTES de importar módulos
os.environ["TESTING"] = "true"  # Desabilita rate limiting durante testes
os.environ["GOOGLE_MAPS_API_KEY"] = "test_key_for_tests"
os.environ["FIREBASE_PRIVATE_KEY_ID"] = "test_key_id"
os.environ["FIREBASE_PRIVATE_KEY"] = "test_private_key"
os.environ["FIREBASE_CLIENT_EMAIL"] = "test@test.com"
os.environ["FIREBASE_PROJECT_ID"] = "test_project"

from main import app
from database import get_session
from models import Restaurant, User, Courier


@pytest.fixture(name="session")
def session_fixture():
    """
    Cria uma sessão de banco de dados em memória para testes
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """
    Cria um cliente de teste do FastAPI
    """
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="test_restaurant")
def test_restaurant_fixture(session: Session):
    """
    Cria um restaurante de teste no banco (com coordenadas)
    """
    restaurant = Restaurant(
        name="Restaurante Teste",
        slug="restaurante-teste",
        cnpj="12345678901234",
        email="teste@restaurante.com",
        phone="11999999999",
        address="Rua Teste, 123",
        plan="TRIAL",
        lat=-23.550520,  # São Paulo (centro)
        lng=-46.633308
    )
    session.add(restaurant)
    session.commit()
    session.refresh(restaurant)
    return restaurant


@pytest.fixture(name="test_user")
def test_user_fixture(session: Session, test_restaurant: Restaurant):
    """
    Cria um usuário de teste no banco
    """
    from services.auth_service import hash_password

    user = User(
        name="Admin Teste",
        email="admin@teste.com",
        password_hash=hash_password("senha123"),
        role="OWNER",
        restaurant_id=test_restaurant.id
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="test_courier")
def test_courier_fixture(session: Session, test_restaurant: Restaurant):
    """
    Cria um motoboy de teste no banco
    """
    from services.auth_service import hash_password

    courier = Courier(
        name="João",
        last_name="Silva",
        phone="11988888888",
        password_hash=hash_password("moto123"),
        status="AVAILABLE",
        restaurant_id=test_restaurant.id
    )
    session.add(courier)
    session.commit()
    session.refresh(courier)
    return courier


@pytest.fixture(name="auth_headers")
def auth_headers_fixture(client: TestClient, test_user: User):
    """
    Retorna headers com token JWT válido
    """
    response = client.post(
        "/auth/login",
        json={
            "email": test_user.email,
            "password": "senha123"
        }
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(name="test_order")
def test_order_fixture(session: Session, test_restaurant: Restaurant):
    """
    Cria um pedido de teste no banco
    """
    from models import Order, OrderStatus, PrepType

    order = Order(
        customer_name="João Silva",
        address_text="Rua Teste, 123",
        lat=-23.550520,
        lng=-46.633308,
        prep_type=PrepType.SHORT,
        status=OrderStatus.CREATED,
        restaurant_id=test_restaurant.id,
        short_id=1001,
        tracking_code="MF-TESTFIX"
    )
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


@pytest.fixture(name="test_orders_ready")
def test_orders_ready_fixture(session: Session, test_restaurant: Restaurant):
    """
    Cria vários pedidos com status READY para testar dispatch

    Cria 5 pedidos em locais diferentes de São Paulo:
    - 2 pedidos próximos (< 1km) - devem ser agrupados
    - 2 pedidos próximos (< 1km) - devem ser agrupados
    - 1 pedido distante (> 5km) - deve ficar separado
    """
    from models import Order, OrderStatus, PrepType
    from datetime import datetime

    orders = [
        # Grupo 1: Próximos (Paulista região)
        Order(
            customer_name="Cliente 1",
            address_text="Av. Paulista, 1000",
            lat=-23.561414,
            lng=-46.656178,
            prep_type=PrepType.SHORT,
            status=OrderStatus.READY,
            ready_at=datetime.now(),
            restaurant_id=test_restaurant.id,
            short_id=1001,
            tracking_code="MF-TEST01"
        ),
        Order(
            customer_name="Cliente 2",
            address_text="Av. Paulista, 1500",
            lat=-23.563891,
            lng=-46.652870,
            prep_type=PrepType.SHORT,
            status=OrderStatus.READY,
            ready_at=datetime.now(),
            restaurant_id=test_restaurant.id,
            short_id=1002,
            tracking_code="MF-TEST02"
        ),
        # Grupo 2: Próximos (Jardins região)
        Order(
            customer_name="Cliente 3",
            address_text="Rua Oscar Freire, 100",
            lat=-23.562010,
            lng=-46.671650,
            prep_type=PrepType.SHORT,
            status=OrderStatus.READY,
            ready_at=datetime.now(),
            restaurant_id=test_restaurant.id,
            short_id=1003,
            tracking_code="MF-TEST03"
        ),
        Order(
            customer_name="Cliente 4",
            address_text="Rua Haddock Lobo, 200",
            lat=-23.560385,
            lng=-46.669875,
            prep_type=PrepType.SHORT,
            status=OrderStatus.READY,
            ready_at=datetime.now(),
            restaurant_id=test_restaurant.id,
            short_id=1004,
            tracking_code="MF-TEST04"
        ),
        # Pedido distante (Zona Leste)
        Order(
            customer_name="Cliente 5",
            address_text="Av. Aricanduva, 5000",
            lat=-23.573636,
            lng=-46.516197,
            prep_type=PrepType.SHORT,
            status=OrderStatus.READY,
            ready_at=datetime.now(),
            restaurant_id=test_restaurant.id,
            short_id=1005,
            tracking_code="MF-TEST05"
        ),
    ]

    for order in orders:
        session.add(order)
    session.commit()

    for order in orders:
        session.refresh(order)

    return orders


@pytest.fixture(name="test_couriers_available")
def test_couriers_available_fixture(session: Session, test_restaurant: Restaurant):
    """
    Cria vários motoboys disponíveis para testar dispatch
    """
    from services.auth_service import hash_password
    from datetime import datetime

    couriers = [
        Courier(
            name="Motoboy",
            last_name="Um",
            phone="11988881111",
            hashed_password=hash_password("moto123"),
            status="AVAILABLE",
            available_since=datetime.now(),
            restaurant_id=test_restaurant.id
        ),
        Courier(
            name="Motoboy",
            last_name="Dois",
            phone="11988882222",
            hashed_password=hash_password("moto123"),
            status="AVAILABLE",
            available_since=datetime.now(),
            restaurant_id=test_restaurant.id
        ),
        Courier(
            name="Motoboy",
            last_name="Três",
            phone="11988883333",
            hashed_password=hash_password("moto123"),
            status="AVAILABLE",
            available_since=datetime.now(),
            restaurant_id=test_restaurant.id
        ),
    ]

    for courier in couriers:
        session.add(courier)
    session.commit()

    for courier in couriers:
        session.refresh(courier)

    return couriers
