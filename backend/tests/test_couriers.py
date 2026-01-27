"""
Testes para endpoints de Motoboys (Couriers)
"""
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from models import (
    Courier, CourierStatus, Order, OrderStatus, Batch, BatchStatus,
    PrepType, Restaurant, PasswordReset
)


# ============ AUTENTICAÇÃO ============

def test_login_sucesso(client: TestClient, test_courier: Courier):
    """Testa login de motoboy com credenciais corretas"""
    response = client.post(
        "/couriers/login",
        json={
            "phone": test_courier.phone,
            "password": "moto123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Bem-vindo" in data["message"]
    assert data["courier"]["id"] == test_courier.id
    assert data["courier"]["name"] == test_courier.name


def test_login_senha_incorreta(client: TestClient, test_courier: Courier):
    """Testa login com senha incorreta"""
    response = client.post(
        "/couriers/login",
        json={
            "phone": test_courier.phone,
            "password": "senhaerrada"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "incorreta" in data["message"].lower()


def test_login_telefone_inexistente(client: TestClient):
    """Testa login com telefone não cadastrado"""
    response = client.post(
        "/couriers/login",
        json={
            "phone": "11999999999",
            "password": "qualquer"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "não cadastrado" in data["message"].lower()


def test_login_telefone_invalido(client: TestClient):
    """Testa login com telefone inválido (muito curto)"""
    response = client.post(
        "/couriers/login",
        json={
            "phone": "123",
            "password": "qualquer"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "inválido" in data["message"].lower()


def test_login_sem_senha_cadastrada(client: TestClient, session: Session, test_restaurant: Restaurant):
    """Testa login de motoboy que não tem senha cadastrada"""
    # Cria motoboy sem senha
    courier = Courier(
        name="Sem",
        last_name="Senha",
        phone="11977777777",
        password_hash=None,  # Sem senha
        status=CourierStatus.AVAILABLE,
        restaurant_id=test_restaurant.id
    )
    session.add(courier)
    session.commit()

    response = client.post(
        "/couriers/login",
        json={
            "phone": "11977777777",
            "password": "qualquer"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "sem senha" in data["message"].lower()


# ============ CRUD ============

def test_criar_motoboy(client: TestClient, session: Session):
    """Testa criação de novo motoboy"""
    response = client.post(
        "/couriers",
        json={
            "name": "Carlos",
            "last_name": "Santos",
            "phone": "11966666666"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Carlos"
    assert data["last_name"] == "Santos"
    assert data["status"] == CourierStatus.OFFLINE  # Começa offline

    # Verifica no banco
    courier = session.get(Courier, data["id"])
    assert courier is not None


def test_listar_motoboys_do_restaurante(
    client: TestClient,
    auth_headers: dict,
    test_courier: Courier,
    session: Session,
    test_restaurant: Restaurant
):
    """Testa listagem de motoboys do próprio restaurante"""
    response = client.get("/couriers", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(c["id"] == test_courier.id for c in data)


def test_listar_motoboys_com_filtro_status(
    client: TestClient,
    auth_headers: dict,
    session: Session,
    test_restaurant: Restaurant
):
    """Testa filtro por status na listagem"""
    from services.auth_service import hash_password

    # Cria motoboys com diferentes status
    available = Courier(
        name="Disponível", last_name="Um", phone="11955555555",
        password_hash=hash_password("123"), status=CourierStatus.AVAILABLE,
        restaurant_id=test_restaurant.id
    )
    offline = Courier(
        name="Offline", last_name="Dois", phone="11944444444",
        password_hash=hash_password("123"), status=CourierStatus.OFFLINE,
        restaurant_id=test_restaurant.id
    )
    session.add(available)
    session.add(offline)
    session.commit()

    # Busca só os AVAILABLE
    response = client.get(f"/couriers?status={CourierStatus.AVAILABLE.value}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert all(c["status"] == CourierStatus.AVAILABLE.value for c in data)


def test_listar_motoboys_isolamento_multi_tenant(
    client: TestClient,
    auth_headers: dict,
    session: Session
):
    """Testa que usuário só vê motoboys do próprio restaurante"""
    from services.auth_service import hash_password

    # Cria outro restaurante
    other_restaurant = Restaurant(
        name="Outro Restaurante",
        slug="outro-motoboys",
        cnpj="99999999999999",
        email="outro@test.com",
        phone="11888888888",
        address="Rua Outro, 999",
        plan="TRIAL"
    )
    session.add(other_restaurant)
    session.commit()
    session.refresh(other_restaurant)

    # Cria motoboy do outro restaurante
    other_courier = Courier(
        name="Outro",
        last_name="Motoboy",
        phone="11933333333",
        password_hash=hash_password("123"),
        status=CourierStatus.AVAILABLE,
        restaurant_id=other_restaurant.id
    )
    session.add(other_courier)
    session.commit()

    # Usuário autenticado lista seus motoboys
    response = client.get("/couriers", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    # NÃO deve conter o motoboy do outro restaurante
    assert not any(c["id"] == other_courier.id for c in data)


def test_buscar_motoboy_por_id(client: TestClient, test_courier: Courier):
    """Testa busca de motoboy específico"""
    response = client.get(f"/couriers/{test_courier.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_courier.id
    assert data["name"] == test_courier.name


def test_buscar_motoboy_inexistente(client: TestClient):
    """Testa busca de motoboy que não existe"""
    response = client.get("/couriers/id-invalido-123")
    assert response.status_code == 404


def test_excluir_motoboy_sucesso(
    client: TestClient,
    auth_headers: dict,
    session: Session,
    test_restaurant: Restaurant
):
    """Testa exclusão de motoboy com sucesso"""
    from services.auth_service import hash_password

    courier = Courier(
        name="Para",
        last_name="Excluir",
        phone="11922222222",
        password_hash=hash_password("123"),
        status=CourierStatus.OFFLINE,
        restaurant_id=test_restaurant.id
    )
    session.add(courier)
    session.commit()
    session.refresh(courier)

    response = client.delete(f"/couriers/{courier.id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["success"] is True

    # Verifica que foi excluído do banco
    deleted = session.get(Courier, courier.id)
    assert deleted is None


def test_excluir_motoboy_outro_restaurante(
    client: TestClient,
    auth_headers: dict,
    session: Session
):
    """Testa que não pode excluir motoboy de outro restaurante"""
    from services.auth_service import hash_password

    # Cria outro restaurante
    other_restaurant = Restaurant(
        name="Outro Restaurante",
        slug="outro-exclusao",
        cnpj="88888888888888",
        email="outro2@test.com",
        phone="11777777777",
        address="Rua Outra, 888",
        plan="TRIAL"
    )
    session.add(other_restaurant)
    session.commit()
    session.refresh(other_restaurant)

    # Cria motoboy do outro restaurante
    other_courier = Courier(
        name="Outro",
        last_name="Protegido",
        phone="11911111111",
        password_hash=hash_password("123"),
        status=CourierStatus.OFFLINE,
        restaurant_id=other_restaurant.id
    )
    session.add(other_courier)
    session.commit()
    session.refresh(other_courier)

    # Tenta excluir
    response = client.delete(f"/couriers/{other_courier.id}", headers=auth_headers)
    assert response.status_code == 403


def test_excluir_motoboy_com_entrega_pendente(
    client: TestClient,
    auth_headers: dict,
    session: Session,
    test_restaurant: Restaurant
):
    """Testa que não pode excluir motoboy com entregas pendentes"""
    from services.auth_service import hash_password

    # Cria motoboy
    courier = Courier(
        name="Com",
        last_name="Entrega",
        phone="11900000000",
        password_hash=hash_password("123"),
        status=CourierStatus.BUSY,
        restaurant_id=test_restaurant.id
    )
    session.add(courier)
    session.commit()
    session.refresh(courier)

    # Cria batch ativo
    batch = Batch(
        courier_id=courier.id,
        restaurant_id=test_restaurant.id,
        status=BatchStatus.IN_PROGRESS
    )
    session.add(batch)
    session.commit()

    # Cria pedido no batch
    order = Order(
        customer_name="Cliente Teste",
        address_text="Rua Teste, 123",
        lat=-23.550520,
        lng=-46.633308,
        prep_type=PrepType.SHORT,
        status=OrderStatus.ASSIGNED,
        restaurant_id=test_restaurant.id,
        batch_id=batch.id
    )
    session.add(order)
    session.commit()

    # Tenta excluir
    response = client.delete(f"/couriers/{courier.id}", headers=auth_headers)
    assert response.status_code == 400
    assert "pendentes" in response.json()["detail"].lower()


# ============ MUDANÇAS DE STATUS ============

def test_marcar_motoboy_disponivel(client: TestClient, session: Session, test_courier: Courier):
    """Testa marcar motoboy como AVAILABLE"""
    response = client.post(f"/couriers/{test_courier.id}/available")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == CourierStatus.AVAILABLE
    assert data["available_since"] is not None

    # Verifica no banco
    session.refresh(test_courier)
    assert test_courier.status == CourierStatus.AVAILABLE


def test_marcar_motoboy_offline(client: TestClient, session: Session, test_courier: Courier):
    """Testa marcar motoboy como OFFLINE"""
    response = client.post(f"/couriers/{test_courier.id}/offline")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == CourierStatus.OFFLINE
    assert data["available_since"] is None


def test_nao_pode_ficar_offline_com_entrega(
    client: TestClient,
    session: Session,
    test_restaurant: Restaurant
):
    """Testa que motoboy não pode ficar offline se tiver entregas"""
    from services.auth_service import hash_password

    # Cria motoboy BUSY
    courier = Courier(
        name="Ocupado",
        last_name="Agora",
        phone="11989898989",
        password_hash=hash_password("123"),
        status=CourierStatus.BUSY,
        restaurant_id=test_restaurant.id
    )
    session.add(courier)
    session.commit()
    session.refresh(courier)

    # Cria batch ativo
    batch = Batch(
        courier_id=courier.id,
        restaurant_id=test_restaurant.id,
        status=BatchStatus.IN_PROGRESS
    )
    session.add(batch)
    session.commit()

    # Cria pedido no batch
    order = Order(
        customer_name="Cliente Teste",
        address_text="Rua Teste, 123",
        lat=-23.550520,
        lng=-46.633308,
        prep_type=PrepType.SHORT,
        status=OrderStatus.ASSIGNED,
        restaurant_id=test_restaurant.id,
        batch_id=batch.id
    )
    session.add(order)
    session.commit()

    # Tenta ficar offline
    response = client.post(f"/couriers/{courier.id}/offline")
    assert response.status_code == 400
    assert "pendentes" in response.json()["detail"].lower()


# ============ LOTE ATUAL ============

def test_buscar_lote_atual_com_lote(
    client: TestClient,
    session: Session,
    test_restaurant: Restaurant
):
    """Testa buscar lote atual quando motoboy tem entregas"""
    from services.auth_service import hash_password

    # Cria motoboy
    courier = Courier(
        name="Com",
        last_name="Lote",
        phone="11987878787",
        password_hash=hash_password("123"),
        status=CourierStatus.BUSY,
        restaurant_id=test_restaurant.id
    )
    session.add(courier)
    session.commit()
    session.refresh(courier)

    # Cria batch
    batch = Batch(
        courier_id=courier.id,
        restaurant_id=test_restaurant.id,
        status=BatchStatus.IN_PROGRESS
    )
    session.add(batch)
    session.commit()
    session.refresh(batch)

    # Cria pedido
    order = Order(
        customer_name="Cliente Lote",
        address_text="Rua Lote, 123",
        lat=-23.550520,
        lng=-46.633308,
        prep_type=PrepType.SHORT,
        status=OrderStatus.ASSIGNED,
        restaurant_id=test_restaurant.id,
        batch_id=batch.id
    )
    session.add(order)
    session.commit()

    # Busca lote atual
    response = client.get(f"/couriers/{courier.id}/current-batch")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == batch.id
    assert data["courier_id"] == courier.id
    assert len(data["orders"]) == 1


def test_buscar_lote_atual_sem_lote(client: TestClient, test_courier: Courier):
    """Testa buscar lote quando motoboy não tem entregas"""
    response = client.get(f"/couriers/{test_courier.id}/current-batch")
    assert response.status_code == 200
    # Retorna null quando não tem lote
    assert response.json() is None


def test_completar_lote_sucesso(
    client: TestClient,
    session: Session,
    test_restaurant: Restaurant
):
    """Testa finalizar lote de entregas"""
    from services.auth_service import hash_password

    # Cria motoboy
    courier = Courier(
        name="Finalizador",
        last_name="Lote",
        phone="11986868686",
        password_hash=hash_password("123"),
        status=CourierStatus.BUSY,
        restaurant_id=test_restaurant.id
    )
    session.add(courier)
    session.commit()
    session.refresh(courier)

    # Cria batch
    batch = Batch(
        courier_id=courier.id,
        restaurant_id=test_restaurant.id,
        status=BatchStatus.IN_PROGRESS
    )
    session.add(batch)
    session.commit()
    session.refresh(batch)

    # Cria pedido
    order = Order(
        customer_name="Cliente Final",
        address_text="Rua Final, 123",
        lat=-23.550520,
        lng=-46.633308,
        prep_type=PrepType.SHORT,
        status=OrderStatus.ASSIGNED,
        restaurant_id=test_restaurant.id,
        batch_id=batch.id
    )
    session.add(order)
    session.commit()
    session.refresh(order)

    # Completa o lote
    response = client.post(f"/couriers/{courier.id}/complete-batch")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == CourierStatus.AVAILABLE  # Fica disponível novamente

    # Verifica que o batch foi finalizado
    session.refresh(batch)
    assert batch.status == BatchStatus.DONE

    # Verifica que o pedido foi entregue
    session.refresh(order)
    assert order.status == OrderStatus.DELIVERED


def test_completar_lote_sem_lote_ativo(client: TestClient, test_courier: Courier):
    """Testa tentar completar lote quando não tem lote ativo"""
    response = client.post(f"/couriers/{test_courier.id}/complete-batch")
    assert response.status_code == 400


# ============ LOCALIZAÇÃO E PUSH TOKEN ============

def test_atualizar_localizacao(client: TestClient, session: Session, test_courier: Courier):
    """Testa atualizar localização do motoboy"""
    lat = -23.561414
    lng = -46.656178

    response = client.put(
        f"/couriers/{test_courier.id}/location",
        params={"lat": lat, "lng": lng}
    )
    assert response.status_code == 200

    # Verifica no banco
    session.refresh(test_courier)
    assert test_courier.last_lat == lat
    assert test_courier.last_lng == lng


def test_atualizar_push_token(client: TestClient, session: Session, test_courier: Courier):
    """Testa salvar token de push notification"""
    token = "fake-fcm-token-12345"

    response = client.put(
        f"/couriers/{test_courier.id}/push-token",
        json={"token": token}
    )
    assert response.status_code == 200
    assert response.json()["success"] is True

    # Verifica no banco
    session.refresh(test_courier)
    assert test_courier.push_token == token


def test_buscar_restaurante_do_motoboy(
    client: TestClient,
    test_courier: Courier,
    test_restaurant: Restaurant
):
    """Testa buscar dados do restaurante do motoboy"""
    response = client.get(f"/couriers/{test_courier.id}/restaurant")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_restaurant.id
    assert data["name"] == test_restaurant.name
    assert data["lat"] is not None
    assert data["lng"] is not None


# ============ RECUPERAÇÃO DE SENHA ============

def test_criar_link_recuperacao_senha(
    client: TestClient,
    session: Session,
    test_courier: Courier
):
    """Testa criar link de recuperação de senha"""
    from unittest.mock import Mock

    # Simula request com base_url
    response = client.post(f"/couriers/{test_courier.id}/password-reset")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "reset_url" in data
    assert test_courier.name in data["courier_name"]


def test_validar_codigo_recuperacao_valido(
    client: TestClient,
    session: Session,
    test_courier: Courier
):
    """Testa validar código de recuperação válido"""
    # Cria código de reset
    reset = PasswordReset(
        code="valid-code-123",
        courier_id=test_courier.id
    )
    session.add(reset)
    session.commit()

    response = client.get("/couriers/password-reset/valid-code-123/validate")
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True


def test_validar_codigo_recuperacao_invalido(client: TestClient):
    """Testa validar código inexistente"""
    response = client.get("/couriers/password-reset/codigo-inexistente/validate")
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False


def test_validar_codigo_recuperacao_usado(
    client: TestClient,
    session: Session,
    test_courier: Courier
):
    """Testa validar código já utilizado"""
    # Cria código usado
    reset = PasswordReset(
        code="used-code-123",
        courier_id=test_courier.id,
        used=True,
        used_at=datetime.now()
    )
    session.add(reset)
    session.commit()

    response = client.get("/couriers/password-reset/used-code-123/validate")
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert "utilizado" in data["message"].lower()


def test_validar_codigo_recuperacao_expirado(
    client: TestClient,
    session: Session,
    test_courier: Courier
):
    """Testa validar código expirado"""
    # Cria código expirado (1 hora atrás)
    reset = PasswordReset(
        code="expired-code-123",
        courier_id=test_courier.id,
        expires_at=datetime.now() - timedelta(hours=2)
    )
    session.add(reset)
    session.commit()

    response = client.get("/couriers/password-reset/expired-code-123/validate")
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert "expirou" in data["message"].lower()


def test_usar_codigo_para_redefinir_senha(
    client: TestClient,
    session: Session,
    test_courier: Courier
):
    """Testa redefinir senha usando código válido"""
    # Cria código de reset
    reset = PasswordReset(
        code="reset-code-456",
        courier_id=test_courier.id
    )
    session.add(reset)
    session.commit()

    # Usa o código para redefinir senha
    response = client.post(
        "/couriers/password-reset/reset-code-456/use",
        params={"new_password": "novasenha123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    # Verifica que o código foi marcado como usado
    session.refresh(reset)
    assert reset.used is True

    # Verifica que a senha foi alterada (tenta fazer login)
    login_response = client.post(
        "/couriers/login",
        json={
            "phone": test_courier.phone,
            "password": "novasenha123"
        }
    )
    assert login_response.status_code == 200
    assert login_response.json()["success"] is True


# ============ ROTAS DE ENTREGA (SEM JWT) ============

def test_coletar_pedido_sucesso(
    client: TestClient,
    session: Session,
    test_restaurant: Restaurant
):
    """Testa motoboy coletando pedido (ASSIGNED -> PICKED_UP)"""
    from services.auth_service import hash_password

    # Cria motoboy
    courier = Courier(
        name="Coletor",
        last_name="Pedidos",
        phone="11985858585",
        password_hash=hash_password("123"),
        status=CourierStatus.BUSY,
        restaurant_id=test_restaurant.id
    )
    session.add(courier)
    session.commit()
    session.refresh(courier)

    # Cria batch
    batch = Batch(
        courier_id=courier.id,
        restaurant_id=test_restaurant.id,
        status=BatchStatus.IN_PROGRESS
    )
    session.add(batch)
    session.commit()
    session.refresh(batch)

    # Cria pedido ASSIGNED
    order = Order(
        customer_name="Cliente Coleta",
        address_text="Rua Coleta, 123",
        lat=-23.550520,
        lng=-46.633308,
        prep_type=PrepType.SHORT,
        status=OrderStatus.ASSIGNED,
        restaurant_id=test_restaurant.id,
        batch_id=batch.id
    )
    session.add(order)
    session.commit()
    session.refresh(order)

    # Coleta o pedido
    response = client.post(f"/couriers/{courier.id}/orders/{order.id}/pickup")
    assert response.status_code == 200
    assert response.json()["success"] is True

    # Verifica status
    session.refresh(order)
    assert order.status == OrderStatus.PICKED_UP


def test_entregar_pedido_sucesso(
    client: TestClient,
    session: Session,
    test_restaurant: Restaurant
):
    """Testa motoboy entregando pedido (PICKED_UP -> DELIVERED)"""
    from services.auth_service import hash_password

    # Cria motoboy
    courier = Courier(
        name="Entregador",
        last_name="Pedidos",
        phone="11984848484",
        password_hash=hash_password("123"),
        status=CourierStatus.BUSY,
        restaurant_id=test_restaurant.id
    )
    session.add(courier)
    session.commit()
    session.refresh(courier)

    # Cria batch
    batch = Batch(
        courier_id=courier.id,
        restaurant_id=test_restaurant.id,
        status=BatchStatus.IN_PROGRESS
    )
    session.add(batch)
    session.commit()
    session.refresh(batch)

    # Cria pedido PICKED_UP
    order = Order(
        customer_name="Cliente Entrega",
        address_text="Rua Entrega, 123",
        lat=-23.550520,
        lng=-46.633308,
        prep_type=PrepType.SHORT,
        status=OrderStatus.PICKED_UP,
        restaurant_id=test_restaurant.id,
        batch_id=batch.id
    )
    session.add(order)
    session.commit()
    session.refresh(order)

    # Entrega o pedido
    response = client.post(f"/couriers/{courier.id}/orders/{order.id}/deliver")
    assert response.status_code == 200
    assert response.json()["success"] is True

    # Verifica status
    session.refresh(order)
    assert order.status == OrderStatus.DELIVERED
    assert order.delivered_at is not None


def test_nao_pode_coletar_pedido_de_outro_batch(
    client: TestClient,
    session: Session,
    test_restaurant: Restaurant
):
    """Testa que motoboy não pode coletar pedido de outro batch"""
    from services.auth_service import hash_password

    # Cria 2 motoboys
    courier1 = Courier(
        name="Motoboy", last_name="Um", phone="11983838383",
        password_hash=hash_password("123"), status=CourierStatus.BUSY,
        restaurant_id=test_restaurant.id
    )
    courier2 = Courier(
        name="Motoboy", last_name="Dois", phone="11982828282",
        password_hash=hash_password("123"), status=CourierStatus.BUSY,
        restaurant_id=test_restaurant.id
    )
    session.add_all([courier1, courier2])
    session.commit()
    session.refresh(courier1)
    session.refresh(courier2)

    # Cria 2 batches
    batch1 = Batch(
        courier_id=courier1.id, restaurant_id=test_restaurant.id,
        status=BatchStatus.IN_PROGRESS
    )
    batch2 = Batch(
        courier_id=courier2.id, restaurant_id=test_restaurant.id,
        status=BatchStatus.IN_PROGRESS
    )
    session.add_all([batch1, batch2])
    session.commit()
    session.refresh(batch1)
    session.refresh(batch2)

    # Cria pedido no batch2
    order = Order(
        customer_name="Cliente Protegido",
        address_text="Rua Protegida, 123",
        lat=-23.550520,
        lng=-46.633308,
        prep_type=PrepType.SHORT,
        status=OrderStatus.ASSIGNED,
        restaurant_id=test_restaurant.id,
        batch_id=batch2.id
    )
    session.add(order)
    session.commit()
    session.refresh(order)

    # Courier1 tenta coletar pedido do batch2
    response = client.post(f"/couriers/{courier1.id}/orders/{order.id}/pickup")
    assert response.status_code == 403
    assert "não pertence" in response.json()["detail"].lower()
