"""
Configuração de fixtures para testes do MotoFlash
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

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
    Cria um restaurante de teste no banco
    """
    restaurant = Restaurant(
        name="Restaurante Teste",
        cnpj="12345678901234",
        email="teste@restaurante.com",
        phone="11999999999",
        address="Rua Teste, 123",
        plan="TRIAL"
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
    from services.auth_service import get_password_hash

    user = User(
        email="admin@teste.com",
        hashed_password=get_password_hash("senha123"),
        full_name="Admin Teste",
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
    from services.auth_service import get_password_hash

    courier = Courier(
        name="João",
        sobrenome="Silva",
        phone="11988888888",
        hashed_password=get_password_hash("moto123"),
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
        restaurant_id=test_restaurant.id
    )
    session.add(order)
    session.commit()
    session.refresh(order)
    return order
