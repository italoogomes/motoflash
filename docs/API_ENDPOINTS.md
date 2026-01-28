# 📡 API Endpoints - MotoFlash

**Versão da API:** 1.1.0
**Base URL:** `https://motoflash-production.up.railway.app` (produção)
**Documentação Interativa:** `/docs` (Swagger UI)

---

## 📋 Índice

1. [Autenticação](#autenticação)
2. [Pedidos](#pedidos)
3. [Motoboys](#motoboys)
4. [Dispatch](#dispatch)
5. [Cardápio](#cardápio)
6. [Clientes](#clientes)
7. [Convites](#convites)
8. [Utilidades](#utilidades)

---

## 🔐 Autenticação

### Headers Necessários

Para **endpoints protegidos**, inclua:
```http
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

---

### POST /auth/register

Cadastra um novo restaurante (self-service).

**Rate Limit:** 5 requisições/minuto

**Request Body:**
```json
{
  "name": "Pizzaria do Zé",
  "email": "contato@pizzariadoze.com",
  "password": "senha123",
  "phone": "16999887766",
  "cnpj": "12345678000190",
  "address": "Rua General Osório, 634 - Centro"
}
```

**Response 200:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid-v4",
    "name": "Pizzaria do Zé",
    "email": "contato@pizzariadoze.com",
    "restaurant_id": "uuid-v4",
    "role": "OWNER",
    "active": true
  },
  "restaurant": {
    "id": "uuid-v4",
    "slug": "pizzaria-do-ze",
    "name": "Pizzaria do Zé",
    "email": "contato@pizzariadoze.com",
    "plan": "TRIAL",
    "trial_ends_at": "2026-02-08T00:00:00",
    "days_remaining": 14,
    "blocked": false
  }
}
```

**Erros:**
- `400` - Email já cadastrado
- `429` - Rate limit excedido

---

### POST /auth/login

Faz login de usuário do dashboard.

**Rate Limit:** 10 requisições/minuto

**Request Body:**
```json
{
  "email": "contato@pizzariadoze.com",
  "password": "senha123"
}
```

**Response 200:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": { ... },
  "restaurant": { ... }
}
```

**Erros:**
- `401` - Email ou senha incorretos
- `403` - Trial expirado

---

### GET /auth/me

Retorna dados do usuário logado (verifica se token ainda é válido).

**Headers:** Requer `Authorization`

**Response 200:**
```json
{
  "access_token": "novo-token-refreshed",
  "token_type": "bearer",
  "user": { ... },
  "restaurant": { ... }
}
```

---

### GET /auth/check-email?email={email}

Verifica se email está disponível para cadastro.

**Response 200:**
```json
{
  "email": "test@example.com",
  "available": true
}
```

---

## 📦 Pedidos

### POST /orders

Cria um novo pedido.

**Headers:** Requer `Authorization`

**Request Body:**
```json
{
  "customer_name": "João Silva",
  "customer_phone": "16999887766",
  "address_text": "Rua XV de Novembro, 123",
  "address_complement": "Apto 201",
  "address_reference": "Próximo ao banco",
  "items": [
    {
      "name": "Pizza Margherita",
      "quantity": 1,
      "price": 45.0
    }
  ],
  "total": 45.0,
  "payment_method": "DINHEIRO",
  "prep_type": "LONG"
}
```

**Response 201:**
```json
{
  "id": "uuid-v4",
  "customer_name": "João Silva",
  "address_text": "Rua XV de Novembro, 123",
  "lat": -21.1775,
  "lng": -47.8102,
  "status": "CREATED",
  "total": 45.0,
  "prep_type": "LONG",
  "created_at": "2026-01-25T10:30:00",
  "qr_code_id": "ABC123"
}
```

**Notas:**
- Backend faz **geocoding automático** do endereço
- Se geocoding falhar, retorna erro 400
- QR Code é gerado automaticamente

---

### GET /orders

Lista pedidos do restaurante.

**Headers:** Requer `Authorization`

**Query Params:**
- `status` (opcional): Filtra por status (CREATED, PREPARING, READY, etc.)
- `limit` (opcional): Limita resultados (padrão: 50)

**Response 200:**
```json
{
  "orders": [
    {
      "id": "uuid-v4",
      "customer_name": "João Silva",
      "status": "READY",
      "total": 45.0,
      "created_at": "2026-01-25T10:30:00"
    }
  ]
}
```

---

### GET /orders/{order_id}

Retorna detalhes de um pedido específico.

**Headers:** Requer `Authorization`

**Response 200:**
```json
{
  "id": "uuid-v4",
  "customer_name": "João Silva",
  "address_text": "Rua XV de Novembro, 123",
  "lat": -21.1775,
  "lng": -47.8102,
  "status": "READY",
  "batch_id": null,
  "stop_order": null,
  "items": [ ... ],
  "total": 45.0,
  "created_at": "2026-01-25T10:30:00"
}
```

---

### POST /orders/{order_id}/scan

Marca pedido como READY (usado quando cozinha escaneia QR Code).

**Headers:** Requer `Authorization`

**Response 200:**
```json
{
  "id": "uuid-v4",
  "status": "READY",
  "ready_at": "2026-01-25T10:45:00"
}
```

---

### POST /orders/{order_id}/preparing

Marca pedido como PREPARING.

**Headers:** Requer `Authorization`

**Response 200:**
```json
{
  "id": "uuid-v4",
  "status": "PREPARING"
}
```

---

### POST /orders/{order_id}/pickup

Marca pedido como PICKED_UP (motoboy retirou).

**Response 200:**
```json
{
  "id": "uuid-v4",
  "status": "PICKED_UP",
  "picked_up_at": "2026-01-25T11:00:00"
}
```

---

### POST /orders/{order_id}/deliver

Marca pedido como DELIVERED (entregue ao cliente).

**Response 200:**
```json
{
  "id": "uuid-v4",
  "status": "DELIVERED",
  "delivered_at": "2026-01-25T11:30:00"
}
```

---

### GET /orders/{order_id}/qrcode

Retorna QR Code como base64 (para exibir na tela).

**Headers:** Requer `Authorization`

**Response 200:**
```json
{
  "qr_code_base64": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."
}
```

---

### GET /orders/{order_id}/qrcode.png

Download direto da imagem PNG do QR Code.

**Headers:** Requer `Authorization`

**Response 200:**
- Content-Type: `image/png`
- Imagem binária

---

## 🏍️ Motoboys

### POST /couriers/login

Login do motoboy (não usa JWT).

**Rate Limit:** 10 requisições/minuto

**Request Body:**
```json
{
  "phone": "16999887766",
  "password": "senha123"
}
```

**Response 200:**
```json
{
  "success": true,
  "message": "Bem-vindo, João Silva!",
  "courier": {
    "id": "uuid-v4",
    "name": "João",
    "last_name": "Silva",
    "phone": "16999887766",
    "status": "AVAILABLE",
    "restaurant_id": "uuid-v4"
  },
  "restaurant_name": "Pizzaria do Zé"
}
```

**Erros:**
- `200` com `success: false` - Credenciais inválidas

---

### POST /couriers

Cria um novo motoboy.

**Headers:** Requer `Authorization`

**Request Body:**
```json
{
  "name": "João",
  "last_name": "Silva",
  "phone": "16999887766",
  "password": "senha123"
}
```

**Response 201:**
```json
{
  "id": "uuid-v4",
  "name": "João",
  "last_name": "Silva",
  "phone": "16999887766",
  "status": "AVAILABLE"
}
```

---

### GET /couriers

Lista motoboys do restaurante.

**Headers:** Requer `Authorization`

**Response 200:**
```json
{
  "couriers": [
    {
      "id": "uuid-v4",
      "name": "João",
      "last_name": "Silva",
      "phone": "16999887766",
      "status": "AVAILABLE"
    }
  ]
}
```

---

### GET /couriers/{courier_id}

Retorna detalhes de um motoboy específico.

**⚠️ ATENÇÃO:** Endpoint sem filtro de `restaurant_id` (bug de segurança conhecido).

**Response 200:**
```json
{
  "id": "uuid-v4",
  "name": "João",
  "last_name": "Silva",
  "phone": "16999887766",
  "status": "BUSY",
  "restaurant_id": "uuid-v4"
}
```

---

### DELETE /couriers/{courier_id}

Deleta um motoboy.

**Headers:** Requer `Authorization`

**Response 200:**
```json
{
  "message": "Motoboy deletado com sucesso"
}
```

---

### POST /couriers/{courier_id}/available

Marca motoboy como disponível.

**Response 200:**
```json
{
  "id": "uuid-v4",
  "status": "AVAILABLE",
  "available_since": "2026-01-25T12:00:00"
}
```

---

### GET /couriers/{courier_id}/batch

Retorna o lote atual do motoboy.

**Response 200:**
```json
{
  "batch": {
    "id": "uuid-v4",
    "status": "ASSIGNED",
    "created_at": "2026-01-25T11:00:00"
  },
  "orders": [
    {
      "id": "uuid-v4",
      "customer_name": "João Silva",
      "address_text": "Rua XV, 123",
      "stop_order": 1
    }
  ]
}
```

---

### POST /couriers/{courier_id}/batch-complete

Finaliza o lote do motoboy (todos pedidos entregues).

**Response 200:**
```json
{
  "message": "Lote finalizado com sucesso",
  "courier_status": "AVAILABLE"
}
```

---

## 🚀 Dispatch

### POST /dispatch/run

Executa o algoritmo de agrupamento e cria lotes.

**Headers:** Requer `Authorization`

**Response 200:**
```json
{
  "batches_created": 3,
  "orders_assigned": 12,
  "message": "3 lote(s) criado(s), 12 pedido(s) atribuído(s)"
}
```

**Notas:**
- Busca pedidos com status `READY`
- Busca motoboys com status `AVAILABLE`
- Agrupa pedidos por proximidade (algoritmo V0.9)
- Cria lotes e atribui aos motoboys
- Envia push notification (se configurado)

---

### GET /dispatch/batches

Lista lotes ativos.

**Headers:** Requer `Authorization`

**Response 200:**
```json
{
  "batches": [
    {
      "id": "uuid-v4",
      "courier_id": "uuid-v4",
      "courier_name": "João Silva",
      "status": "IN_PROGRESS",
      "order_count": 4,
      "created_at": "2026-01-25T11:00:00"
    }
  ]
}
```

---

### GET /batches/{batch_id}/polyline

Retorna a polyline da rota para desenhar no mapa.

**Response 200:**
```json
{
  "polyline": "encoded-polyline-string-from-google",
  "start": {
    "lat": -21.2020,
    "lng": -47.8130
  },
  "orders": [
    {
      "lat": -21.1775,
      "lng": -47.8102,
      "address": "Rua XV, 123"
    }
  ]
}
```

**Notas:**
- Usa Google Directions API
- Polyline pode ser decodificada com Leaflet ou Google Maps

---

### GET /dispatch/previsao ⭐ NOVO (v1.1.0)

Previsão híbrida de motoboys - combina dados históricos com tempo real.

**Headers:** Requer `Authorization`

**Response 200:**
```json
{
  "historico": {
    "pedidos_hora": 15.0,
    "tempo_preparo_min": 12.0,
    "tempo_rota_min": 30.0,
    "motoboys_recomendados": 3,
    "amostras": 10,
    "disponivel": true
  },
  "atual": {
    "pedidos_hora": 20,
    "tempo_preparo_min": 10.5,
    "tempo_rota_min": 28.0,
    "motoboys_ativos": 2,
    "motoboys_disponiveis": 1,
    "pedidos_fila": 3,
    "pedidos_em_rota": 2
  },
  "balanceamento": {
    "taxa_saida_pedidos": 20.0,
    "capacidade_entrega": 4.0,
    "balanco_fluxo": -16.0,
    "tempo_acumulo_min": 4
  },
  "comparacao": {
    "variacao_demanda_pct": 33.3
  },
  "recomendacao": {
    "motoboys": 5,
    "status": "atencao",
    "mensagem": "Demanda 33% acima do normal para Quinta às 19h",
    "sugestao_acao": "Considere ativar 3 motoboy(s) adicional(is)"
  },
  "dia_semana": 3,
  "hora_atual": 19,
  "timestamp": "2026-01-28T19:30:00"
}
```

**Notas:**
- `historico.disponivel`: `false` se não há dados históricos suficientes
- `balanco_fluxo`: Negativo indica que pedidos estão acumulando
- `status`: `adequado`, `atencao` ou `critico`

---

### POST /dispatch/atualizar-padroes ⭐ NOVO (v1.1.0)

Atualiza padrões históricos analisando últimas 4 semanas de pedidos.

**Headers:** Requer `Authorization`

**Response 200:**
```json
{
  "sucesso": true,
  "padroes_atualizados": 45,
  "pedidos_analisados": 320,
  "mensagem": "Padrões atualizados! 45 slots de dia/hora processados."
}
```

**Notas:**
- Recomendado executar semanalmente
- Analisa pedidos DELIVERED das últimas 4 semanas
- Calcula médias por dia da semana e hora

---

### GET /dispatch/padroes ⭐ NOVO (v1.1.0)

Lista padrões históricos aprendidos.

**Headers:** Requer `Authorization`

**Response 200:**
```json
{
  "total_padroes": 45,
  "padroes": [
    {
      "dia_semana": 0,
      "dia_nome": "Segunda",
      "hora": 19,
      "media_pedidos_hora": 15.5,
      "media_tempo_preparo_min": 12.0,
      "media_tempo_rota_min": 28.5,
      "motoboys_recomendados": 3,
      "amostras": 8,
      "ultima_atualizacao": "2026-01-28T10:00:00"
    }
  ]
}
```

**Notas:**
- `dia_semana`: 0=Segunda, 1=Terça... 6=Domingo
- `amostras`: Quantidade de dados históricos usados
- Útil para visualizar quais horários são mais movimentados

---

## 🍕 Cardápio

### POST /menu/categories

Cria uma nova categoria.

**Headers:** Requer `Authorization`

**Request Body:**
```json
{
  "name": "Pizzas",
  "order": 1,
  "active": true
}
```

**Response 201:**
```json
{
  "id": "uuid-v4",
  "name": "Pizzas",
  "order": 1,
  "active": true
}
```

---

### GET /menu/categories

Lista categorias do restaurante.

**Headers:** Requer `Authorization`

**Response 200:**
```json
{
  "categories": [
    {
      "id": "uuid-v4",
      "name": "Pizzas",
      "order": 1,
      "active": true
    }
  ]
}
```

---

### PUT /menu/categories/{category_id}

Atualiza uma categoria.

**Headers:** Requer `Authorization`

**Request Body:**
```json
{
  "name": "Pizzas Especiais",
  "order": 1,
  "active": true
}
```

---

### DELETE /menu/categories/{category_id}

Deleta uma categoria.

**Headers:** Requer `Authorization`

**Response 200:**
```json
{
  "message": "Categoria deletada com sucesso"
}
```

---

### POST /menu/items

Cria um novo item do menu.

**Headers:** Requer `Authorization`

**Request Body:**
```json
{
  "name": "Pizza Margherita",
  "description": "Molho de tomate, muçarela e manjericão",
  "price": 45.0,
  "image_url": "/uploads/abc123.jpg",
  "category_id": "uuid-v4",
  "active": true,
  "available": true
}
```

**Response 201:**
```json
{
  "id": "uuid-v4",
  "name": "Pizza Margherita",
  "price": 45.0,
  "active": true
}
```

---

### GET /menu/items

Lista itens do menu.

**Headers:** Requer `Authorization`

**Query Params:**
- `category_id` (opcional): Filtra por categoria

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid-v4",
      "name": "Pizza Margherita",
      "price": 45.0,
      "category_id": "uuid-v4"
    }
  ]
}
```

---

### PUT /menu/items/{item_id}

Atualiza um item.

**Headers:** Requer `Authorization`

---

### DELETE /menu/items/{item_id}

Deleta um item.

**Headers:** Requer `Authorization`

---

## 👥 Clientes

### POST /customers

Cria um novo cliente (cache de endereço).

**Headers:** Requer `Authorization`

**Request Body:**
```json
{
  "phone": "16999887766",
  "name": "João Silva",
  "address": "Rua XV de Novembro, 123",
  "complement": "Apto 201",
  "reference": "Próximo ao banco"
}
```

**Response 201:**
```json
{
  "id": "uuid-v4",
  "phone": "16999887766",
  "name": "João Silva",
  "address": "Rua XV de Novembro, 123",
  "lat": -21.1775,
  "lng": -47.8102
}
```

**Notas:**
- Backend faz geocoding automático
- Coordenadas são armazenadas para evitar chamadas repetidas à API

---

### GET /customers

Lista clientes do restaurante.

**Headers:** Requer `Authorization`

**Response 200:**
```json
{
  "customers": [
    {
      "id": "uuid-v4",
      "phone": "16999887766",
      "name": "João Silva",
      "address": "Rua XV, 123"
    }
  ]
}
```

---

### GET /customers/{customer_id}

Retorna detalhes de um cliente.

**Headers:** Requer `Authorization`

---

### PUT /customers/{customer_id}

Atualiza um cliente.

**Headers:** Requer `Authorization`

---

### DELETE /customers/{customer_id}

Deleta um cliente.

**Headers:** Requer `Authorization`

---

## 🎟️ Convites

### POST /invites

Cria um código de convite para motoboy.

**Headers:** Requer `Authorization`

**Response 201:**
```json
{
  "id": "uuid-v4",
  "code": "ABC123XYZ",
  "expires_at": "2026-01-26T23:59:59",
  "invite_url": "https://motoflash.com/convite/ABC123XYZ"
}
```

**Notas:**
- Código expira em 24 horas
- Pode ser usado apenas uma vez

---

### GET /invites

Lista convites criados.

**Headers:** Requer `Authorization`

**Response 200:**
```json
{
  "invites": [
    {
      "id": "uuid-v4",
      "code": "ABC123XYZ",
      "expires_at": "2026-01-26T23:59:59",
      "used": false
    }
  ]
}
```

---

### GET /invites/{code}/validate

Valida se código de convite é válido.

**Response 200:**
```json
{
  "valid": true,
  "restaurant_name": "Pizzaria do Zé"
}
```

**Erros:**
- `404` - Código não encontrado
- `400` - Código expirado ou já usado

---

### POST /invites/{code}/use

Motoboy usa o convite para se cadastrar.

**Request Body:**
```json
{
  "name": "João",
  "last_name": "Silva",
  "phone": "16999887766",
  "password": "senha123"
}
```

**Response 200:**
```json
{
  "success": true,
  "message": "Cadastro realizado com sucesso!",
  "courier": {
    "id": "uuid-v4",
    "name": "João",
    "last_name": "Silva"
  }
}
```

---

## 🛠️ Utilidades

### POST /upload

Faz upload de uma imagem.

**Headers:** Requer `Authorization`
**Content-Type:** `multipart/form-data`

**Request Body:**
```
file: <binary data>
```

**Limites:**
- Tamanho máximo: 5MB
- Formatos aceitos: JPG, PNG, WebP, GIF

**Response 200:**
```json
{
  "url": "/uploads/abc123def456.jpg"
}
```

---

### GET /geocode

Endpoint de teste para geocoding.

**Query Params:**
- `address` (obrigatório): Endereço a geocodificar
- `city` (opcional): Cidade (padrão: Ribeirão Preto)
- `state` (opcional): Estado (padrão: SP)

**Response 200:**
```json
{
  "found": true,
  "lat": -21.1775,
  "lng": -47.8102,
  "address_searched": "Rua XV de Novembro, 123, Ribeirão Preto, SP, Brasil"
}
```

---

### GET /health

Health check do servidor.

**Response 200:**
```json
{
  "status": "healthy"
}
```

---

### GET /

Informações da API.

**Response 200:**
```json
{
  "app": "MotoFlash",
  "version": "0.9.0",
  "docs": "/docs",
  "status": "running"
}
```

---

## 🚨 Códigos de Erro

| Código | Significado |
|--------|-------------|
| `200` | Sucesso |
| `201` | Criado com sucesso |
| `400` | Requisição inválida |
| `401` | Não autenticado |
| `403` | Sem permissão |
| `404` | Não encontrado |
| `429` | Rate limit excedido |
| `500` | Erro interno do servidor |

---

## 📝 Notas Importantes

1. **Todos endpoints protegidos** requerem header `Authorization: Bearer <token>`
2. **Multi-tenant:** Filtros automáticos por `restaurant_id` do token
3. **Rate limiting:** Aplicado em endpoints de autenticação
4. **Geocoding:** Automático em pedidos e clientes
5. **QR Codes:** Gerados automaticamente ao criar pedido

---

**Para mais detalhes:**
- Ver [FLUXOS.md](./FLUXOS.md) para entender o fluxo completo
- Ver [FRONTEND_BACKEND.md](./FRONTEND_BACKEND.md) para exemplos de uso no frontend
