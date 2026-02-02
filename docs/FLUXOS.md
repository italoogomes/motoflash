# 🔄 Fluxos de Dados - MotoFlash

**Versão:** 1.4.2
**Última atualização:** 2026-02-01

Este documento detalha todos os fluxos de dados do sistema, mostrando como frontend e backend se comunicam em cada operação.

---

## 📋 Índice

1. [Cadastro de Restaurante](#1-cadastro-de-restaurante)
2. [Login de Usuário (Dashboard)](#2-login-de-usuário-dashboard)
3. [Criar Pedido](#3-criar-pedido)
4. [Marcar Pedido como Pronto (QR Code)](#4-marcar-pedido-como-pronto-qr-code)
5. [Executar Dispatch](#5-executar-dispatch)
6. [Login do Motoboy (PWA)](#6-login-do-motoboy-pwa)
7. [Motoboy Aceita Lote](#7-motoboy-aceita-lote)
8. [Motoboy Entrega Pedido](#8-motoboy-entrega-pedido)
9. [Criar Motoboy via Convite](#9-criar-motoboy-via-convite)
10. [Upload de Imagem](#10-upload-de-imagem)
11. [Rastrear Pedido (Atendente)](#11-rastrear-pedido-atendente)
12. [Cancelar Pedido](#12-cancelar-pedido) ⭐ NOVO (v1.4.2)

---

## 📊 Status do Pedido (v1.4.2)

```
┌───────────┐    ┌─────────┐    ┌──────────┐    ┌───────────┐    ┌───────────┐
│ PREPARING │───▶│  READY  │───▶│ ASSIGNED │───▶│ PICKED_UP │───▶│ DELIVERED │
└───────────┘    └─────────┘    └──────────┘    └───────────┘    └───────────┘
      │               │               │
      │               │               │
      ▼               ▼               ▼
┌───────────────────────────────────────┐
│            CANCELLED                   │
└───────────────────────────────────────┘
```

**Notas:**
- Pedidos iniciam direto em PREPARING (fluxo simplificado v1.4.1)
- Cancelamento só é permitido antes do PICKED_UP
- Ao cancelar, o motoboy é liberado automaticamente

---

## 1. Cadastro de Restaurante

### 📍 Página: `/login` (auth.html)

### Fluxo Completo:

```
┌─────────────┐
│   USUÁRIO   │
│  preenche   │
│  formulário │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  FRONTEND (auth.html)                   │
│                                         │
│  1. Valida campos (email, senha, etc.)  │
│  2. Monta JSON do request               │
│  3. POST /auth/register                 │
└──────────────────┬──────────────────────┘
                   │
                   ▼ HTTP POST
┌──────────────────────────────────────────────────────┐
│  BACKEND (routers/auth.py)                           │
│                                                      │
│  1. Valida email único (consulta Users table)       │
│  2. Chama geocoding_service.py                      │
│     → Google Maps API (endereço → lat/lng)          │
│  3. Gera slug único (ex: "pizzaria-do-ze")          │
│  4. Cria Restaurant (plan=TRIAL, trial=14 dias)     │
│  5. Cria User (role=OWNER, password hash bcrypt)    │
│  6. Gera JWT token (SECRET_KEY)                     │
│  7. Retorna token + dados do user + restaurant      │
└──────────────────┬───────────────────────────────────┘
                   │
                   ▼ HTTP 200 Response
┌──────────────────────────────────────────┐
│  FRONTEND (auth.html)                    │
│                                          │
│  1. Salva token em localStorage          │
│  2. Salva dados do restaurante           │
│  3. Redireciona para /dashboard          │
└──────────────────────────────────────────┘
```

### Código Frontend (Simplificado):
```javascript
// auth.html
async function handleRegister(formData) {
  const response = await fetch('/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(formData)
  });

  const data = await response.json();

  if (response.ok) {
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('restaurant', JSON.stringify(data.restaurant));
    window.location.href = '/dashboard';
  }
}
```

### Código Backend (Simplificado):
```python
# routers/auth.py
@router.post("/register")
def register_restaurant(data: RestaurantCreate, session: Session):
    # 1. Valida email único
    existing = session.exec(select(User).where(User.email == data.email)).first()
    if existing:
        raise HTTPException(400, "Email já cadastrado")

    # 2. Geocoding
    geo_result = geocode_address_detailed(data.address)
    lat, lng = geo_result["lat"], geo_result["lng"]

    # 3. Cria Restaurant + User
    restaurant = Restaurant(name=data.name, plan=PlanType.TRIAL, ...)
    user = User(email=data.email, password_hash=hash_password(data.password), ...)

    # 4. Gera token
    token = create_access_token({"user_id": user.id, "restaurant_id": restaurant.id})

    return LoginResponse(access_token=token, user=user, restaurant=restaurant)
```

---

## 2. Login de Usuário (Dashboard)

### 📍 Página: `/login` (auth.html)

### Fluxo Completo:

```
┌──────────────┐
│   USUÁRIO    │
│ email+senha  │
└──────┬───────┘
       │
       ▼
┌─────────────────────────────┐
│  FRONTEND (auth.html)       │
│                             │
│  POST /auth/login           │
└──────────┬──────────────────┘
           │
           ▼
┌────────────────────────────────────────────┐
│  BACKEND (routers/auth.py)                 │
│                                            │
│  1. Busca user por email                   │
│  2. Valida senha (bcrypt.checkpw)          │
│  3. Verifica se trial expirou              │
│  4. Atualiza last_login                    │
│  5. Gera JWT token                         │
│  6. Retorna token + dados                  │
└──────────┬─────────────────────────────────┘
           │
           ▼
┌──────────────────────────────┐
│  FRONTEND (auth.html)        │
│                              │
│  1. Salva token              │
│  2. Verifica se bloqueado    │
│  3. Redireciona /dashboard   │
└──────────────────────────────┘
```

### Armazenamento do Token:
```javascript
// Salvo em localStorage
localStorage.setItem('token', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...');

// Usado em todas requisições subsequentes
fetch('/orders', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('token')}`,
    'Content-Type': 'application/json'
  }
});
```

---

## 3. Criar Pedido

### 📍 Página: `/dashboard` (index.html)

### Fluxo Completo:

```
┌──────────────────┐
│  USUÁRIO         │
│ preenche pedido  │
└────────┬─────────┘
         │
         ▼
┌────────────────────────────────────────┐
│  FRONTEND (index.html)                 │
│                                        │
│  1. Monta objeto do pedido             │
│  2. POST /orders (com token JWT)       │
└────────┬───────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────┐
│  BACKEND (routers/orders.py)                         │
│                                                      │
│  1. Valida JWT token (extrai restaurant_id)         │
│  2. Chama geocoding_service.py                      │
│     → Google Maps API (endereço → lat/lng)          │
│  3. Gera QR Code único (6 caracteres)               │
│  4. Cria Order no banco                             │
│     status = CREATED                                │
│     restaurant_id = do token                        │
│  5. Retorna pedido completo                         │
└────────┬─────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│  FRONTEND (index.html)         │
│                                │
│  1. Adiciona pedido na lista   │
│  2. Mostra no mapa (lat/lng)   │
│  3. Exibe QR Code              │
└────────────────────────────────┘
```

### Código Frontend:
```javascript
// index.html - Componente CreateOrderModal
async function handleCreateOrder(orderData) {
  const response = await fetch('/orders', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      customer_name: orderData.customerName,
      address_text: orderData.address,
      items: orderData.items,
      total: orderData.total,
      prep_type: orderData.prepType
    })
  });

  const newOrder = await response.json();

  // Atualiza estado React
  setOrders(prev => [...prev, newOrder]);

  // Mostra no mapa
  addMarkerToMap(newOrder.lat, newOrder.lng);
}
```

### Código Backend:
```python
# routers/orders.py
@router.post("/orders")
def create_order(
    data: OrderCreate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    # 1. Geocoding
    coords = geocode_address(data.address_text)
    if not coords:
        raise HTTPException(400, "Endereço não encontrado")

    # 2. Gera QR Code ID
    qr_code_id = generate_random_code(6)

    # 3. Cria pedido
    order = Order(
        customer_name=data.customer_name,
        address_text=data.address_text,
        lat=coords[0],
        lng=coords[1],
        status=OrderStatus.CREATED,
        restaurant_id=user.restaurant_id,
        qr_code_id=qr_code_id
    )

    session.add(order)
    session.commit()

    return order
```

---

## 4. Marcar Pedido como Pronto (QR Code)

### 📍 Página: `/dashboard` (index.html)

### Fluxo Completo:

```
┌─────────────────┐
│   COZINHA       │
│ escaneia QR Code│
└────────┬────────┘
         │
         ▼
┌────────────────────────────────┐
│  LEITOR QR CODE                │
│ (câmera ou scanner)            │
│                                │
│  Lê código: ABC123             │
└────────┬───────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  FRONTEND (index.html)              │
│                                     │
│  1. Busca pedido pelo QR Code ID    │
│  2. POST /orders/{id}/scan          │
└────────┬────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  BACKEND (routers/orders.py)             │
│                                          │
│  1. Busca Order por ID                   │
│  2. Valida que status = PREPARING        │
│  3. Atualiza:                            │
│     status = READY                       │
│     ready_at = now()                     │
│  4. Retorna pedido atualizado            │
└────────┬─────────────────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│  FRONTEND (index.html)       │
│                              │
│  1. Atualiza status na UI    │
│  2. Move para coluna "READY" │
│  3. Som de notificação       │
└──────────────────────────────┘
```

### Código Frontend:
```javascript
// index.html - QRCodeScanner
function handleQRCodeScan(qrCodeId) {
  // Busca pedido pelo QR Code
  const order = orders.find(o => o.qr_code_id === qrCodeId);

  if (order) {
    // Marca como pronto
    fetch(`/orders/${order.id}/scan`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    .then(res => res.json())
    .then(updatedOrder => {
      // Atualiza estado
      setOrders(prev => prev.map(o =>
        o.id === updatedOrder.id ? updatedOrder : o
      ));

      // Feedback visual
      showNotification('Pedido marcado como pronto!');
    });
  }
}
```

---

## 5. Executar Dispatch

### 📍 Página: `/dashboard` (index.html)

### Fluxo Completo:

```
┌─────────────────────┐
│   USUÁRIO           │
│ clica "Despachar"   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────┐
│  FRONTEND (index.html)          │
│                                 │
│  POST /dispatch/run             │
└──────────┬──────────────────────┘
           │
           ▼
┌────────────────────────────────────────────────────────────────┐
│  BACKEND (routers/dispatch.py)                                 │
│                                                                │
│  Chama: dispatch_service.run_dispatch()                        │
└──────────┬─────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────────────┐
│  ALGORITMO DE DISPATCH (services/dispatch_service.py)                │
│                                                                      │
│  1. Busca pedidos READY do restaurante                               │
│  2. Busca motoboys AVAILABLE do restaurante                          │
│  3. Se não tem pedidos OU motoboys → retorna mensagem                │
│                                                                      │
│  4. AGRUPA PEDIDOS:                                                  │
│     a) Pedidos do MESMO endereço → mesmo grupo                       │
│     b) Pedidos PRÓXIMOS (até 3km) → junta grupos                     │
│     c) Se grupo > 6 pedidos → divide                                 │
│                                                                      │
│  5. Para cada grupo:                                                 │
│     a) Cria Batch (lote) vinculado ao motoboy                        │
│     b) Calcula distância REAL de cada pedido (Google Directions API) │
│     c) Ordena pedidos pela distância (mais perto primeiro)           │
│     d) Atualiza Order:                                               │
│        - batch_id = ID do lote                                       │
│        - stop_order = ordem de parada (1, 2, 3...)                   │
│        - status = ASSIGNED                                           │
│     e) Atualiza Courier:                                             │
│        - status = BUSY                                               │
│     f) Envia push notification (se configurado)                      │
│                                                                      │
│  6. PEDIDOS ÓRFÃOS (sem motoboy):                                    │
│     - Adiciona na rota mais próxima (se couber)                      │
│                                                                      │
│  7. Retorna resumo:                                                  │
│     - Quantos lotes criados                                          │
│     - Quantos pedidos atribuídos                                     │
└──────────┬───────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  FRONTEND (index.html)              │
│                                     │
│  1. Mostra mensagem de sucesso      │
│  2. Atualiza lista de pedidos       │
│  3. Mostra lotes criados            │
│  4. Desenha rotas no mapa (polyline)│
└─────────────────────────────────────┘
```

### Código Backend (Algoritmo Simplificado):
```python
# services/dispatch_service.py
def run_dispatch(session: Session, restaurant_id: str):
    # 1. Busca pedidos READY
    ready_orders = session.exec(
        select(Order)
        .where(Order.status == OrderStatus.READY)
        .where(Order.restaurant_id == restaurant_id)
    ).all()

    # 2. Busca motoboys AVAILABLE
    available_couriers = session.exec(
        select(Courier)
        .where(Courier.status == CourierStatus.AVAILABLE)
        .where(Courier.restaurant_id == restaurant_id)
    ).all()

    # 3. Agrupa pedidos
    clusters = smart_cluster_orders(
        ready_orders,
        MAX_CLUSTER_RADIUS_KM,
        PREFERRED_ORDERS_PER_COURIER,
        len(available_couriers)
    )

    # 4. Cria lotes
    for i, cluster in enumerate(clusters):
        courier = available_couriers[i]

        # Cria batch
        batch = Batch(courier_id=courier.id, restaurant_id=restaurant_id)
        session.add(batch)
        session.commit()

        # Ordena pedidos pela rota REAL (Google)
        sorted_cluster = optimize_route_with_google(cluster, restaurant_lat, restaurant_lng)

        # Atribui pedidos
        for stop_num, order in enumerate(sorted_cluster, 1):
            order.batch_id = batch.id
            order.stop_order = stop_num
            order.status = OrderStatus.ASSIGNED

        # Atualiza motoboy
        courier.status = CourierStatus.BUSY

    session.commit()

    return DispatchResult(batches_created=len(clusters), orders_assigned=len(ready_orders))
```

---

## 6. Login do Motoboy (PWA)

### 📍 Página: `/motoboy` (motoboy.html)

### Fluxo Completo:

```
┌────────────────┐
│   MOTOBOY      │
│ celular+senha  │
└────────┬───────┘
         │
         ▼
┌──────────────────────────────┐
│  FRONTEND (motoboy.html)     │
│                              │
│  POST /couriers/login        │
└────────┬─────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  BACKEND (routers/couriers.py)          │
│                                         │
│  1. Normaliza telefone (só números)     │
│  2. Busca Courier por phone             │
│  3. Valida senha (bcrypt.checkpw)       │
│  4. Atualiza last_login                 │
│  5. Retorna dados do motoboy            │
│     (SEM JWT - retorna direto)          │
└────────┬────────────────────────────────┘
         │
         ▼
┌───────────────────────────────────┐
│  FRONTEND (motoboy.html)          │
│                                   │
│  1. Salva dados em localStorage   │
│  2. Mostra tela de lotes          │
│  3. Inicia polling de novos lotes │
└───────────────────────────────────┘
```

### Código Frontend:
```javascript
// motoboy.html
async function handleLogin(phone, password) {
  const response = await fetch('/couriers/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone, password })
  });

  const data = await response.json();

  if (data.success) {
    // Salva dados do motoboy
    localStorage.setItem('courier', JSON.stringify(data.courier));
    localStorage.setItem('restaurant_name', data.restaurant_name);

    // Redireciona para tela de lotes
    showBatchesScreen();

    // Inicia polling de novos lotes
    setInterval(checkForNewBatch, 30000); // a cada 30s
  } else {
    alert(data.message);
  }
}
```

**⚠️ Nota:** Login de motoboy NÃO usa JWT por simplicidade. Os dados são salvos localmente e o `courier_id` é usado nas requisições subsequentes.

---

## 7. Motoboy Aceita Lote

### 📍 Página: `/motoboy` (motoboy.html)

### Fluxo Completo:

```
┌────────────────────────┐
│   MOTOBOY              │
│ vê notificação de lote │
└────────┬───────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  FRONTEND (motoboy.html)            │
│                                     │
│  GET /couriers/{id}/batch           │
└────────┬────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  BACKEND (routers/couriers.py)           │
│                                          │
│  1. Busca Batch do motoboy               │
│     WHERE courier_id = {id}              │
│     AND status IN (ASSIGNED, IN_PROGRESS)│
│  2. Busca Orders do batch                │
│     WHERE batch_id = {batch_id}          │
│     ORDER BY stop_order                  │
│  3. Retorna batch + orders               │
└────────┬─────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  FRONTEND (motoboy.html)                 │
│                                          │
│  1. Mostra detalhes do lote              │
│  2. Lista pedidos ordenados              │
│  3. Desenha rota no mapa (Leaflet)       │
│  4. Botão "Iniciar Entregas"             │
└────────┬─────────────────────────────────┘
         │
         ▼
┌──────────────────────────┐
│  MOTOBOY                 │
│ clica "Iniciar Entregas" │
└──────────────────────────┘
```

### Busca de Polyline da Rota:
```javascript
// motoboy.html
async function showRouteOnMap(batchId) {
  // Busca polyline da rota
  const response = await fetch(`/batches/${batchId}/polyline`);
  const data = await response.json();

  // Decodifica polyline e desenha no mapa
  const decodedPath = L.Polyline.fromEncoded(data.polyline);

  // Adiciona no mapa Leaflet
  L.polyline(decodedPath, {
    color: '#ff6b00',
    weight: 4
  }).addTo(map);

  // Adiciona marcadores dos pedidos
  data.orders.forEach((order, index) => {
    L.marker([order.lat, order.lng])
      .bindPopup(`Parada ${index + 1}: ${order.address}`)
      .addTo(map);
  });
}
```

---

## 8. Motoboy Entrega Pedido

### 📍 Página: `/motoboy` (motoboy.html)

### Fluxo Completo:

```
┌───────────────────────────┐
│   MOTOBOY                 │
│ entrega pedido ao cliente │
│ marca como "Entregue"     │
└────────┬──────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  FRONTEND (motoboy.html)        │
│                                 │
│  POST /orders/{id}/deliver      │
└────────┬────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  BACKEND (routers/orders.py)             │
│                                          │
│  1. Busca Order por ID                   │
│  2. Valida status = PICKED_UP            │
│  3. Atualiza:                            │
│     status = DELIVERED                   │
│     delivered_at = now()                 │
│  4. Retorna pedido atualizado            │
└────────┬─────────────────────────────────┘
         │
         ▼
┌───────────────────────────────────────────┐
│  FRONTEND (motoboy.html)                  │
│                                           │
│  1. Remove pedido da lista                │
│  2. Verifica se é o último pedido do lote │
│  3. Se SIM → POST /couriers/{id}/batch-complete │
└────────┬──────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│  BACKEND (routers/couriers.py)              │
│                                             │
│  POST /couriers/{id}/batch-complete         │
│                                             │
│  1. Busca Batch do motoboy                  │
│  2. Atualiza Batch:                         │
│     status = COMPLETED                      │
│     completed_at = now()                    │
│  3. Atualiza Courier:                       │
│     status = AVAILABLE                      │
│     available_since = now()                 │
│  4. Retorna sucesso                         │
└────────┬────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│  FRONTEND (motoboy.html)     │
│                              │
│  1. Mostra "Lote Concluído!" │
│  2. Volta para tela inicial  │
│  3. Aguarda novo lote        │
└──────────────────────────────┘
```

---

## 9. Criar Motoboy via Convite

### 📍 Página: `/convite/{code}` (convite.html)

### Fluxo Completo:

```
┌────────────────────────────┐
│   DONO DO RESTAURANTE      │
│ cria convite no dashboard  │
└────────┬───────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│  DASHBOARD (index.html)            │
│                                    │
│  POST /invites                     │
└────────┬───────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  BACKEND (routers/invites.py)            │
│                                          │
│  1. Gera código aleatório (9 chars)      │
│  2. Cria Invite:                         │
│     expires_at = now() + 24h             │
│     used = false                         │
│  3. Retorna código + URL                 │
│     /convite/ABC123XYZ                   │
└────────┬─────────────────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│  DONO DO RESTAURANTE           │
│ envia URL por WhatsApp         │
│ https://.../convite/ABC123XYZ  │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────┐
│   MOTOBOY              │
│ acessa link no celular │
└────────┬───────────────┘
         │
         ▼
┌──────────────────────────────────┐
│  FRONTEND (convite.html)         │
│                                  │
│  1. Extrai código da URL         │
│  2. GET /invites/{code}/validate │
└────────┬─────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│  BACKEND (routers/invites.py)        │
│                                      │
│  1. Busca Invite por code            │
│  2. Valida:                          │
│     - Código existe?                 │
│     - Não expirou?                   │
│     - Não foi usado?                 │
│  3. Retorna valid=true + nome do     │
│     restaurante                      │
└────────┬─────────────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│  FRONTEND (convite.html)       │
│                                │
│  1. Mostra formulário          │
│  2. Motoboy preenche dados     │
│  3. POST /invites/{code}/use   │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│  BACKEND (routers/invites.py)          │
│                                        │
│  1. Valida código novamente            │
│  2. Valida telefone único              │
│  3. Cria Courier:                      │
│     phone, name, last_name             │
│     password_hash (bcrypt)             │
│     restaurant_id = do convite         │
│     status = AVAILABLE                 │
│  4. Marca convite como usado:          │
│     used = true                        │
│     used_by_courier_id = {id}          │
│  5. Retorna sucesso + dados motoboy    │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│  FRONTEND (convite.html)       │
│                                │
│  1. Mostra "Cadastro OK!"      │
│  2. Redireciona para /motoboy  │
└────────────────────────────────┘
```

---

## 10. Upload de Imagem

### 📍 Página: `/cardapio` (cardapio.html)

### Fluxo Completo:

```
┌──────────────────────┐
│   USUÁRIO            │
│ seleciona imagem     │
│ (item do cardápio)   │
└────────┬─────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  FRONTEND (cardapio.html)           │
│                                     │
│  1. Valida arquivo (tipo, tamanho)  │
│  2. Cria FormData                   │
│  3. POST /upload (multipart)        │
└────────┬────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  BACKEND (main.py)                       │
│                                          │
│  1. Valida tipo:                         │
│     JPG, PNG, WebP, GIF                  │
│  2. Valida tamanho:                      │
│     Max 5MB                              │
│  3. Gera nome único:                     │
│     UUID + extensão                      │
│  4. Salva em /data/uploads/              │
│  5. Retorna URL: /uploads/{filename}     │
└────────┬─────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│  FRONTEND (cardapio.html)        │
│                                  │
│  1. Recebe URL da imagem         │
│  2. Exibe preview                │
│  3. Salva URL ao criar/editar    │
│     item do menu                 │
└──────────────────────────────────┘
```

### Código Frontend:
```javascript
// cardapio.html
async function handleImageUpload(file) {
  // Valida tamanho
  if (file.size > 5 * 1024 * 1024) {
    alert('Imagem muito grande (máx 5MB)');
    return;
  }

  // Cria FormData
  const formData = new FormData();
  formData.append('file', file);

  // Upload
  const response = await fetch('/upload', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });

  const data = await response.json();

  // Usa a URL retornada
  setImageUrl(data.url); // Ex: "/uploads/abc123.jpg"
}
```

---

## 11. Rastrear Pedido (Atendente)

### 📍 Página: `/dashboard` (index.html) - Aba Rastreamento

### Fluxo Completo:

```
┌─────────────────────────────┐
│   CLIENTE                   │
│ liga para o restaurante     │
│ "Onde está meu pedido?"     │
└──────────┬──────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│   ATENDENTE                          │
│ acessa aba "Rastreamento"            │
│ digita nome do cliente: "Maria"      │
└──────────┬───────────────────────────┘
           │
           ▼
┌────────────────────────────────────────────────┐
│  FRONTEND (index.html - TrackingPage)          │
│                                                │
│  1. Captura input (debounce 300ms)             │
│  2. Valida query (mínimo 2 caracteres)         │
│  3. GET /orders/search?q=Maria                 │
└────────┬───────────────────────────────────────┘
         │
         ▼ HTTP GET (com JWT)
┌──────────────────────────────────────────────────────┐
│  BACKEND (routers/orders.py)                         │
│                                                      │
│  1. Normaliza texto (remove acentos)                │
│     "María" → "maria"                               │
│  2. Busca em múltiplos campos:                      │
│     - Customer.name (LIKE %maria%)                  │
│     - Customer.phone                                │
│     - Order.short_id (se número)                    │
│     - Order.tracking_code (se MF-)                  │
│  3. Filtra:                                         │
│     - restaurant_id = do token                      │
│     - status != DELIVERED                           │
│  4. Ordena por created_at DESC                      │
│  5. Limita a 10 resultados                          │
│  6. Retorna lista de pedidos                        │
└────────┬─────────────────────────────────────────────┘
         │
         ▼ HTTP 200 Response
┌──────────────────────────────────────────────┐
│  FRONTEND (SearchResults)                    │
│                                              │
│  Exibe cards:                                │
│  ┌──────────────────────────────────────┐   │
│  │ #1234 Maria Silva                    │   │
│  │ Status: 🔵 Em Rota                   │   │
│  │ Motoboy: João Santos                 │   │
│  │ Posição: 2º de 3 entregas            │   │
│  │ [Ver Detalhes no Mapa] →             │   │
│  └──────────────────────────────────────┘   │
└────────┬─────────────────────────────────────┘
         │
         ▼
┌──────────────────────────┐
│   ATENDENTE              │
│ clica "Ver Detalhes"     │
└────────┬─────────────────┘
         │
         ▼
┌────────────────────────────────────────────────┐
│  FRONTEND (TrackingModal)                      │
│                                                │
│  1. Abre modal fullscreen                      │
│  2. GET /orders/{id}/tracking-details          │
│  3. Renderiza mapa (Leaflet.js)                │
│  4. Inicia polling (10 segundos)               │
└────────┬───────────────────────────────────────┘
         │
         ▼ HTTP GET (com JWT)
┌──────────────────────────────────────────────────────────┐
│  BACKEND (routers/orders.py)                             │
│                                                          │
│  get_order_tracking_details(order_id, user)             │
│                                                          │
│  1. Busca Order por ID                                   │
│  2. Valida restaurant_id (multi-tenant)                  │
│  3. Se pedido tem batch_id:                              │
│     a) Busca Batch                                       │
│     b) Busca todos Orders do lote (ORDER BY stop_order) │
│     c) Calcula position (2 de 3)                         │
│     d) Busca Courier                                     │
│     e) Busca GPS atual (last_lat, last_lng)             │
│     f) Busca polyline da rota                            │
│  4. Monta resposta:                                      │
│     {                                                    │
│       order: {...},                                      │
│       batch: {id, status, position, total, orders[]},   │
│       courier: {name, phone, current_lat, current_lng}, │
│       route: {polyline, waypoints[]}                    │
│     }                                                    │
└────────┬─────────────────────────────────────────────────┘
         │
         ▼ HTTP 200 Response
┌────────────────────────────────────────────────────────┐
│  FRONTEND (TrackingModal + TrackingMap)                │
│                                                        │
│  ┌──────────────────────────────────────────────┐     │
│  │  ❌ Fechar         Pedido #1234              │     │
│  ├──────────────────────────────────────────────┤     │
│  │                                              │     │
│  │  [MAPA INTERATIVO - Leaflet.js]             │     │
│  │                                              │     │
│  │  🏪 Restaurante (laranja)                    │     │
│  │  🏍️ Motoboy (azul pulsante) ← GPS atual     │     │
│  │  ① Rua A, 100 (✅ Entregue)                 │     │
│  │  ② Rua das Flores, 123 (📍 VOCÊ ESTÁ AQUI)  │     │
│  │  ③ Rua B, 200 (⏳ Próximo)                   │     │
│  │                                              │     │
│  │  Polyline azul conectando tudo              │     │
│  │                                              │     │
│  ├──────────────────────────────────────────────┤     │
│  │  📦 Detalhes do Pedido                      │     │
│  │  Cliente: Maria Silva                       │     │
│  │  Endereço: Rua das Flores, 123             │     │
│  │  Status: Em Rota 🔵                         │     │
│  │                                              │     │
│  │  🏍️ Motoboy: João Santos                    │     │
│  │  Telefone: (11) 99999-9999                  │     │
│  │  Posição: 2ª parada de 3                    │     │
│  │                                              │     │
│  │  📍 Próximas Entregas:                      │     │
│  │  1. ✅ Rua A, 100 (Entregue)                │     │
│  │  2. 📍 Rua das Flores, 123 ← VOCÊ           │     │
│  │  3. ⏳ Rua B, 200 (Aguardando)              │     │
│  │                                              │     │
│  │  [📱 Enviar por WhatsApp]                   │     │
│  └──────────────────────────────────────────────┘     │
└────────────────────────────────────────────────────────┘
```

### Atualização em Tempo Real (Polling):

```javascript
// Frontend - Polling a cada 10 segundos
useEffect(() => {
  const interval = setInterval(() => {
    fetch(`/orders/${orderId}/tracking-details`)
      .then(res => res.json())
      .then(data => {
        // Atualiza estado
        setTrackingDetails(data);
        // Mapa re-renderiza automaticamente
        // Marcador do motoboy atualiza posição GPS
      });
  }, 10000);

  return () => clearInterval(interval);
}, [orderId]);
```

### Envio por WhatsApp:

```
┌──────────────────────────────────┐
│   ATENDENTE                      │
│ clica "Enviar por WhatsApp"      │
└────────┬─────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│  FRONTEND (handleSendWhatsApp)              │
│                                             │
│  1. Lê tracking_code: "MF-ABC123"           │
│  2. Monta mensagem:                         │
│     "Olá! Seu pedido #1234 está Em Rota.   │
│      Acompanhe em tempo real:              │
│      https://.../track/MF-ABC123"          │
│  3. Abre WhatsApp:                          │
│     window.open(                            │
│       'https://wa.me/?text=...',            │
│       '_blank'                              │
│     )                                       │
└────────┬────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  WHATSAPP WEB/APP               │
│                                 │
│  Abre com mensagem pré-pronta   │
│  Atendente escolhe contato      │
│  Envia para cliente             │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  CLIENTE                        │
│                                 │
│  Recebe link de rastreio        │
│  Clica no link                  │
│  GET /orders/track/{code}       │
│  Vê status do pedido            │
└─────────────────────────────────┘
```

### Código Frontend (Simplificado):

```javascript
// TrackingPage - components.js
function TrackingPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [showModal, setShowModal] = useState(false);

  // Busca com debounce
  useEffect(() => {
    const timer = setTimeout(() => {
      if (query.length >= 2) {
        fetch(`/orders/search?q=${query}`)
          .then(res => res.json())
          .then(data => setResults(data));
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [query]);

  return (
    <div>
      <h1>📍 Rastreamento de Pedidos</h1>
      <input
        value={query}
        onChange={e => setQuery(e.target.value)}
        placeholder="Buscar por nome, telefone ou #ID"
      />
      {results.map(order => (
        <div key={order.id} onClick={() => {
          setSelectedOrder(order);
          setShowModal(true);
        }}>
          #{order.short_id} {order.customer_name}
        </div>
      ))}
      {showModal && (
        <TrackingModal
          order={selectedOrder}
          onClose={() => setShowModal(false)}
        />
      )}
    </div>
  );
}
```

### Código Backend (Simplificado):

```python
# routers/orders.py
from unicodedata import normalize

def normalize_text(text: str) -> str:
    """Remove acentos para busca"""
    nfkd = normalize('NFKD', text)
    return ''.join([c for c in nfkd if not combining(c)]).lower()

@router.get("/search")
def search_orders(q: str, user: User = Depends(get_current_user)):
    normalized = normalize_text(q)

    # Busca multi-critério
    orders = session.exec(
        select(Order)
        .join(Customer)
        .where(
            Order.restaurant_id == user.restaurant_id,
            Order.status != OrderStatus.DELIVERED,
            or_(
                func.lower(func.unaccent(Customer.name)).like(f'%{normalized}%'),
                Customer.phone.like(f'%{q}%'),
                Order.short_id == int(q.replace('#', '')) if q.isdigit() else None
            )
        )
        .order_by(Order.created_at.desc())
        .limit(10)
    ).all()

    return orders

@router.get("/{order_id}/tracking-details")
def get_tracking_details(order_id: str, user: User = Depends(get_current_user)):
    order = session.get(Order, order_id)

    # Valida multi-tenant
    if not order or order.restaurant_id != user.restaurant_id:
        raise HTTPException(404)

    # Monta resposta completa
    response = {
        "order": order,
        "batch": None,
        "courier": None,
        "route": None
    }

    if order.batch_id:
        batch = session.get(Batch, order.batch_id)
        batch_orders = get_batch_orders(batch.id)
        courier = session.get(Courier, batch.courier_id)
        polyline = get_batch_route_polyline(batch.id)

        response.update({
            "batch": {
                "id": batch.id,
                "position": order.stop_order,
                "total": len(batch_orders),
                "orders": batch_orders
            },
            "courier": {
                "name": f"{courier.name} {courier.last_name}",
                "phone": courier.phone,
                "current_lat": courier.last_lat,
                "current_lng": courier.last_lng
            },
            "route": polyline
        })

    return response
```

**Notas:**
- Busca normalizada (sem acentos) para melhor UX
- Multi-tenant seguro (sempre filtra por `restaurant_id`)
- Polling a cada 10 segundos para atualização em tempo real
- Mapa interativo com Leaflet.js
- Compartilhamento via WhatsApp Web/App

**Para mais detalhes:** Ver [RASTREAMENTO.md](./RASTREAMENTO.md)

---

## 📊 Resumo dos Fluxos

| Operação | Frontend | Backend | Serviços Externos |
|----------|----------|---------|-------------------|
| Cadastro | auth.html | auth.py | Google Maps (geocoding) |
| Login | auth.html | auth.py | - |
| Criar Pedido | index.html | orders.py | Google Maps (geocoding) |
| QR Code Scan | index.html | orders.py | - |
| Dispatch | index.html | dispatch.py | Google Maps (directions) |
| Login Motoboy | motoboy.html | couriers.py | - |
| Aceitar Lote | motoboy.html | couriers.py | - |
| Entregar | motoboy.html | orders.py | - |
| Criar Convite | index.html | invites.py | - |
| Usar Convite | convite.html | invites.py | - |
| Upload | cardapio.html | main.py | - |
| Rastrear Pedido ⭐ | index.html (TrackingPage) | orders.py (search + tracking-details) | Leaflet.js (OpenStreetMap) |

---

## 🔄 Polling e Real-time

### Dashboard (index.html)
```javascript
// Atualiza lista de pedidos a cada 10 segundos
setInterval(async () => {
  const response = await fetch('/orders', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const data = await response.json();
  setOrders(data.orders);
}, 10000);
```

### App Motoboy (motoboy.html)
```javascript
// Verifica novos lotes a cada 30 segundos
setInterval(async () => {
  const response = await fetch(`/couriers/${courierId}/batch`);
  const data = await response.json();

  if (data.batch && data.batch.status === 'ASSIGNED') {
    showNotification('Novo lote disponível!');
    showBatchDetails(data.batch, data.orders);
  }
}, 30000);
```

---

## 12. Cancelar Pedido

### 📍 Página: `/dashboard` (index.html) - Aba Pedidos

### Fluxo Completo:

```
┌─────────────────────────┐
│    ATENDENTE            │
│                         │
│  1. Clica no botão ✕    │
│  2. Confirma cancelar   │
└────────┬────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│  FRONTEND (components.js)            │
│                                      │
│  1. Exibe confirm() de confirmação   │
│  2. POST /orders/{id}/cancel         │
└────────┬─────────────────────────────┘
         │
         ▼ HTTP POST
┌──────────────────────────────────────────────────────┐
│  BACKEND (routers/orders.py)                         │
│                                                      │
│  1. Busca Order por ID                               │
│  2. Valida restaurant_id (multi-tenant)             │
│  3. Valida status não é PICKED_UP/DELIVERED/CANCELLED│
│  4. Se estava em batch:                              │
│     → Verifica outros pedidos do motoboy             │
│     → Libera motoboy se não tem mais pedidos         │
│  5. Atualiza:                                        │
│     status = CANCELLED                               │
│     cancelled_at = now()                             │
│     batch_id = NULL                                  │
│  6. Retorna pedido atualizado                        │
└────────┬─────────────────────────────────────────────┘
         │
         ▼ HTTP 200 Response
┌─────────────────────────────────┐
│  FRONTEND (components.js)       │
│                                 │
│  1. Chama fetchAll()            │
│  2. Atualiza lista de pedidos   │
│  3. Pedido some da coluna ativa │
└─────────────────────────────────┘
```

### Código Frontend:
```javascript
// components.js - OrdersPage
const handleCancel = async (order) => {
    if (!confirm(`Cancelar pedido #${order.short_id}?`)) return;
    try {
        await authFetch(`${API_URL}/orders/${order.id}/cancel`, { method: 'POST' });
        fetchAll(); // Atualiza lista
    } catch (err) {
        alert('Erro ao cancelar: ' + err.message);
    }
};
```

### Código Backend:
```python
# routers/orders.py
@router.post("/{order_id}/cancel")
def cancel_order(order_id: str, ...):
    # Valida status
    if order.status in [OrderStatus.PICKED_UP, OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
        raise HTTPException(400, "Pedido não pode ser cancelado")

    # Libera motoboy se necessário
    if order.batch_id:
        # ... verifica outros pedidos

    order.status = OrderStatus.CANCELLED
    order.cancelled_at = datetime.now()
    order.batch_id = None
    return order
```

---

**Próximo:** Ver [FRONTEND_BACKEND.md](./FRONTEND_BACKEND.md) para exemplos de código completo de cada página.
