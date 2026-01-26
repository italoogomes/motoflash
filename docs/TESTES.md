# 🧪 Testes Automatizados - MotoFlash

**Versão:** 1.0.0
**Data:** 2026-01-26

---

## 📊 Visão Geral

O MotoFlash utiliza **pytest** como framework de testes automatizados. Os testes garantem que a API funcione corretamente e previnem regressões quando novas funcionalidades são adicionadas.

### Cobertura Atual

| Módulo | Status | Testes |
|--------|--------|--------|
| **Autenticação** | ✅ Implementado | 8 testes |
| **Pedidos** | ✅ Implementado | 16 testes |
| **Dispatch** | 🔄 Planejado | - |
| **Motoboys** | 🔄 Planejado | - |
| **Cardápio** | 🔄 Planejado | - |

---

## 📁 Estrutura de Testes

```
backend/
├── tests/
│   ├── __init__.py          # Marca como package Python
│   ├── conftest.py          # Fixtures compartilhadas
│   ├── test_auth.py         # Testes de autenticação
│   ├── test_orders.py       # Testes de pedidos (planejado)
│   └── test_dispatch.py     # Testes de dispatch (planejado)
```

---

## 🛠️ Instalação

### 1. Instalar Dependências

```bash
cd backend
pip install -r requirements.txt
```

As dependências de teste incluem:
- `pytest>=7.4.0` - Framework de testes
- `pytest-asyncio>=0.21.0` - Suporte para funções assíncronas

---

## 🚀 Executando os Testes

### Rodar Todos os Testes

```bash
cd backend
pytest
```

### Rodar Testes de um Arquivo Específico

```bash
pytest tests/test_auth.py
```

### Rodar um Teste Específico

```bash
pytest tests/test_auth.py::test_login_sucesso
```

### Rodar com Saída Detalhada

```bash
pytest -v
```

### Rodar com Informações de Print

```bash
pytest -s
```

### Rodar com Cobertura de Código (futuro)

```bash
pytest --cov=. --cov-report=html
```

---

## 🧩 Fixtures Disponíveis

As fixtures são definidas em `conftest.py` e estão disponíveis para todos os testes.

### `session`
Cria um banco de dados SQLite em memória para cada teste.

```python
def test_exemplo(session: Session):
    # Use session para operações de banco
    pass
```

### `client`
Cria um TestClient do FastAPI para fazer requisições HTTP.

```python
def test_exemplo(client: TestClient):
    response = client.get("/orders")
    assert response.status_code == 200
```

### `test_restaurant`
Cria um restaurante de teste no banco.

```python
def test_exemplo(test_restaurant: Restaurant):
    assert test_restaurant.name == "Restaurante Teste"
```

### `test_user`
Cria um usuário de teste (OWNER) no banco.

```python
def test_exemplo(test_user: User):
    assert test_user.email == "admin@teste.com"
```

### `test_courier`
Cria um motoboy de teste no banco.

```python
def test_exemplo(test_courier: Courier):
    assert test_courier.status == "AVAILABLE"
```

### `auth_headers`
Retorna headers HTTP com token JWT válido.

```python
def test_exemplo(client: TestClient, auth_headers: dict):
    response = client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
```

---

## ✅ Testes de Autenticação (test_auth.py)

### Testes Implementados

#### 1. `test_login_sucesso`
- **O que testa:** Login com credenciais válidas
- **Resultado esperado:** Status 200, retorna token JWT e dados do usuário

#### 2. `test_login_senha_incorreta`
- **O que testa:** Login com senha errada
- **Resultado esperado:** Status 401, mensagem de erro

#### 3. `test_login_email_inexistente`
- **O que testa:** Login com email que não existe
- **Resultado esperado:** Status 401, mensagem de erro

#### 4. `test_registro_sucesso`
- **O que testa:** Cadastro de novo restaurante
- **Resultado esperado:** Status 200, retorna token e cria usuário OWNER

#### 5. `test_registro_email_duplicado`
- **O que testa:** Cadastro com email já existente
- **Resultado esperado:** Status 400, mensagem de erro

#### 6. `test_me_endpoint_autenticado`
- **O que testa:** Endpoint /auth/me com token válido
- **Resultado esperado:** Status 200, retorna dados do usuário

#### 7. `test_me_endpoint_sem_token`
- **O que testa:** Endpoint /auth/me sem token
- **Resultado esperado:** Status 401

#### 8. `test_me_endpoint_token_invalido`
- **O que testa:** Endpoint /auth/me com token inválido
- **Resultado esperado:** Status 401

---

## ✅ Testes de Pedidos (test_orders.py)

### Testes Implementados

#### 1. `test_criar_pedido_com_coordenadas`
- **O que testa:** Criação de pedido com lat/lng fornecidos
- **Resultado esperado:** Status 200, pedido criado com coordenadas corretas

#### 2. `test_criar_pedido_nome_default`
- **O que testa:** Criação de pedido sem nome
- **Resultado esperado:** Status 200, nome padrão "Cliente" é usado

#### 3. `test_criar_pedido_sem_autenticacao`
- **O que testa:** Tentativa de criar pedido sem token JWT
- **Resultado esperado:** Status 401

#### 4. `test_listar_pedidos`
- **O que testa:** Listagem de pedidos do restaurante
- **Resultado esperado:** Status 200, retorna lista com pedidos

#### 5. `test_listar_pedidos_filtro_status`
- **O que testa:** Listagem com filtro por status
- **Resultado esperado:** Status 200, apenas pedidos com status correto

#### 6. `test_isolamento_multi_tenant`
- **O que testa:** Isolamento entre restaurantes
- **Resultado esperado:** Restaurante A não vê pedidos do Restaurante B

#### 7. `test_buscar_pedido_especifico`
- **O que testa:** Busca de pedido por ID
- **Resultado esperado:** Status 200, retorna dados do pedido

#### 8. `test_buscar_pedido_inexistente`
- **O que testa:** Busca de pedido que não existe
- **Resultado esperado:** Status 404

#### 9. `test_buscar_pedido_outro_restaurante`
- **O que testa:** Tentativa de buscar pedido de outro restaurante
- **Resultado esperado:** Status 404 (proteção multi-tenant)

#### 10. `test_gerar_qrcode`
- **O que testa:** Geração de QR Code do pedido
- **Resultado esperado:** Status 200, retorna QR Code em base64

#### 11. `test_marcar_pedido_como_preparing`
- **O que testa:** Marcar pedido como "em preparo"
- **Resultado esperado:** Status 200, status atualizado para PREPARING

#### 12. `test_marcar_pedido_como_ready`
- **O que testa:** Marcar pedido como "pronto" (QR Code bipado)
- **Resultado esperado:** Status 200, status READY + timestamp ready_at

#### 13. `test_transicao_status_sequencial`
- **O que testa:** Transição correta de status (CREATED → PREPARING → READY)
- **Resultado esperado:** Todas transições funcionam

#### 14. `test_transicao_status_invalida`
- **O que testa:** Transição inválida (ex: CREATED → DELIVERED)
- **Resultado esperado:** Status 400, mensagem de erro

#### 15. `test_transicao_pickup_requer_assigned`
- **O que testa:** Pickup só funciona se pedido está ASSIGNED
- **Resultado esperado:** Status 400 se não estiver ASSIGNED

#### 16. `test_criar_pedido_prep_type`
- **O que testa:** Criação com tipo de preparo (short/long)
- **Resultado esperado:** Status 200, prep_type correto

---

## 📝 Como Escrever Novos Testes

### Estrutura Básica

```python
def test_nome_do_teste(client: TestClient, auth_headers: dict):
    """
    Descrição do que o teste faz
    """
    # 1. Arrange (preparar dados)
    data = {"campo": "valor"}

    # 2. Act (executar ação)
    response = client.post("/endpoint", json=data, headers=auth_headers)

    # 3. Assert (verificar resultado)
    assert response.status_code == 200
    assert response.json()["campo"] == "valor"
```

### Exemplo: Teste de Criar Pedido

```python
def test_criar_pedido_sucesso(client: TestClient, auth_headers: dict):
    """
    Testa criação de pedido com dados válidos
    """
    # Arrange
    order_data = {
        "customer_name": "João Silva",
        "customer_address": "Rua A, 123",
        "customer_phone": "11999999999",
        "delivery_fee": 5.0,
        "items": [
            {"name": "Pizza", "quantity": 1, "price": 30.0}
        ]
    }

    # Act
    response = client.post(
        "/orders",
        json=order_data,
        headers=auth_headers
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["customer_name"] == "João Silva"
    assert data["status"] == "READY"
    assert data["total"] == 35.0  # 30 + 5 de taxa
```

---

## 🔍 Boas Práticas

### 1. **Nome Descritivo**
```python
✅ def test_login_senha_incorreta()
❌ def test_login_1()
```

### 2. **Um Conceito por Teste**
```python
✅ Teste A: verifica status 200
✅ Teste B: verifica formato dos dados

❌ Teste único que verifica tudo
```

### 3. **Documentação Clara**
```python
def test_exemplo():
    """
    Testa criação de pedido quando motoboy está ocupado.
    Resultado esperado: pedido fica READY até dispatch.
    """
```

### 4. **Isolamento de Testes**
- Cada teste deve ser independente
- Use fixtures para criar dados
- Banco em memória é limpo a cada teste

### 5. **Asserções Específicas**
```python
✅ assert response.status_code == 200
✅ assert "access_token" in response.json()

❌ assert response.ok
❌ assert len(response.json()) > 0
```

---

## 🎯 Próximos Testes a Implementar

### Prioridade 1: Pedidos
- [ ] Criar pedido com dados válidos
- [ ] Criar pedido com endereço inválido
- [ ] Listar pedidos do restaurante
- [ ] Atualizar status de pedido
- [ ] Deletar pedido

### Prioridade 2: Dispatch
- [ ] Executar dispatch com pedidos disponíveis
- [ ] Executar dispatch sem motoboys
- [ ] Executar dispatch sem pedidos
- [ ] Verificar agrupamento correto
- [ ] Verificar cálculo de rotas

### Prioridade 3: Motoboys
- [ ] Criar motoboy
- [ ] Login de motoboy
- [ ] Aceitar lote
- [ ] Marcar pedido como entregue
- [ ] Finalizar lote

### Prioridade 4: Cardápio
- [ ] Criar categoria
- [ ] Criar item
- [ ] Listar itens por categoria
- [ ] Atualizar preços
- [ ] Deletar item

---

## 🐛 Troubleshooting

### Erro: "No module named 'pytest'"
**Solução:** Instale as dependências:
```bash
pip install -r requirements.txt
```

### Erro: "ModuleNotFoundError: No module named 'main'"
**Solução:** Execute pytest da pasta `backend`:
```bash
cd backend
pytest
```

### Erro: "Database is locked"
**Solução:** Use banco em memória (já configurado no conftest.py):
```python
engine = create_engine("sqlite:///:memory:")
```

### Testes Passam Localmente mas Falham no Railway
**Causa:** Testes não devem rodar em produção
**Solução:** Rode testes apenas em ambiente de desenvolvimento

---

## 📊 Exemplo de Saída de Testes

```bash
$ pytest -v

tests/test_auth.py::test_login_sucesso PASSED                    [ 12%]
tests/test_auth.py::test_login_senha_incorreta PASSED            [ 25%]
tests/test_auth.py::test_login_email_inexistente PASSED          [ 37%]
tests/test_auth.py::test_registro_sucesso PASSED                 [ 50%]
tests/test_auth.py::test_registro_email_duplicado PASSED         [ 62%]
tests/test_auth.py::test_me_endpoint_autenticado PASSED          [ 75%]
tests/test_auth.py::test_me_endpoint_sem_token PASSED            [ 87%]
tests/test_auth.py::test_me_endpoint_token_invalido PASSED       [100%]

======================== 8 passed in 2.31s ========================
```

---

## 📚 Referências

- [Documentação Pytest](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLModel Testing](https://sqlmodel.tiangolo.com/tutorial/fastapi/tests/)

---

**Última atualização:** 2026-01-26
**Próximo passo:** Implementar testes de pedidos
