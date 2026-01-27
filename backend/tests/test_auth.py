"""
Testes para autenticação e endpoints de auth
"""
import pytest
from fastapi.testclient import TestClient
from models import Restaurant, User


def test_login_sucesso(client: TestClient, test_user: User):
    """
    Testa login com credenciais válidas
    """
    response = client.post(
        "/auth/login",
        json={
            "email": "admin@teste.com",
            "password": "senha123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    assert data["user"]["email"] == "admin@teste.com"


def test_login_senha_incorreta(client: TestClient, test_user: User):
    """
    Testa login com senha incorreta
    """
    response = client.post(
        "/auth/login",
        json={
            "email": "admin@teste.com",
            "password": "senhaerrada"
        }
    )
    assert response.status_code == 401
    assert "Email ou senha incorretos" in response.json()["detail"]


def test_login_email_inexistente(client: TestClient):
    """
    Testa login com email que não existe
    """
    response = client.post(
        "/auth/login",
        json={
            "email": "naoexiste@teste.com",
            "password": "senha123"
        }
    )
    assert response.status_code == 401
    assert "Email ou senha incorretos" in response.json()["detail"]


def test_registro_sucesso(client: TestClient):
    """
    Testa cadastro de novo restaurante e usuário
    """
    response = client.post(
        "/auth/register",
        json={
            "name": "Novo Restaurante",
            "cnpj": "98765432109876",
            "email": "novo@restaurante.com",
            "password": "senha123",
            "phone": "11977777777",
            "address": "Rua Nova, 456"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "novo@restaurante.com"
    assert data["user"]["role"].upper() == "OWNER"


def test_registro_email_duplicado(client: TestClient, test_user: User):
    """
    Testa cadastro com email já existente
    """
    response = client.post(
        "/auth/register",
        json={
            "name": "Outro Restaurante",
            "cnpj": "11111111111111",
            "email": "admin@teste.com",  # Email já existe
            "password": "senha123",
            "phone": "11966666666",
            "address": "Rua Outra, 789"
        }
    )
    assert response.status_code == 400
    assert "cadastrado" in response.json()["detail"]


def test_me_endpoint_autenticado(client: TestClient, auth_headers: dict):
    """
    Testa endpoint /auth/me com token válido
    """
    response = client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == "admin@teste.com"
    assert "id" in data["user"]
    assert "restaurant_id" in data["user"]


def test_me_endpoint_sem_token(client: TestClient):
    """
    Testa endpoint /auth/me sem token
    """
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_me_endpoint_token_invalido(client: TestClient):
    """
    Testa endpoint /auth/me com token inválido
    """
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer token_invalido"}
    )
    assert response.status_code == 401
