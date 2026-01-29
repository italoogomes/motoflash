# 📍 Sistema de Rastreamento para Atendente - MotoFlash

**Versão:** 1.3.0
**Última atualização:** 2026-01-28

Este documento detalha o Sistema de Rastreamento de Pedidos, uma funcionalidade que permite atendentes do restaurante buscar e acompanhar pedidos em tempo real através de um mapa interativo.

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Casos de Uso](#casos-de-uso)
3. [Fluxo Completo de Rastreamento](#fluxo-completo-de-rastreamento)
4. [Arquitetura Frontend](#arquitetura-frontend)
5. [Arquitetura Backend](#arquitetura-backend)
6. [Integração com Leaflet.js](#integração-com-leafletjs)
7. [Atualização em Tempo Real](#atualização-em-tempo-real)
8. [Compartilhamento via WhatsApp](#compartilhamento-via-whatsapp)
9. [Multi-tenant e Segurança](#multi-tenant-e-segurança)
10. [Troubleshooting](#troubleshooting)

---

## Visão Geral

### O que é?

Sistema que permite atendentes do restaurante rastrearem pedidos em tempo real para informar clientes que ligam perguntando "onde está meu pedido?".

### Funcionalidades Principais

1. **Busca Multi-critério:**
   - Por nome do cliente (busca parcial, sem acentos)
   - Por telefone do cliente
   - Por #ID do pedido (ex: #1234)
   - Por código de rastreio (ex: MF-ABC123)

2. **Visualização em Mapa:**
   - Rota completa do motoboy
   - Posição atual do motoboy (GPS)
   - Marcadores numerados dos pedidos
   - Indicação de qual pedido é o buscado

3. **Informações em Tempo Real:**
   - Status atual do pedido
   - Posição na fila (ex: "2º de 3 entregas")
   - Dados do motoboy (nome, telefone)
   - Lista de próximas entregas

4. **Compartilhamento:**
   - Botão para enviar link de rastreio via WhatsApp
   - Link público para cliente acompanhar (sem login)

---

## Casos de Uso

### Caso 1: Cliente liga perguntando sobre o pedido

```
Cliente: "Oi, fiz um pedido há 30 minutos, onde está?"
Atendente: [Abre aba Rastreamento, busca por nome "João Silva"]
Atendente: "Seu pedido já saiu para entrega! O motoboy está na 2ª parada de 3,
           deve chegar em aproximadamente 10 minutos."
```

### Caso 2: Cliente liga com código do pedido

```
Cliente: "Meu pedido é o #1234, quanto tempo falta?"
Atendente: [Busca "#1234", abre mapa]
Atendente: "Seu pedido está em rota! Vou te enviar um link por WhatsApp
           para você acompanhar em tempo real."
```

### Caso 3: Atendente proativo

```
Restaurante recebe vários pedidos.
Atendente monitora todos na aba Rastreamento.
Identifica pedido atrasado e liga proativamente para explicar.
```

---

## Fluxo Completo de Rastreamento

### 1. Atendente Busca Pedido

```
┌──────────────────┐
│   ATENDENTE      │
│ digita "Maria"   │
└────────┬─────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  FRONTEND (TrackingPage)                │
│                                         │
│  1. Captura input (debounce 300ms)     │
│  2. Valida query (min 2 caracteres)    │
│  3. GET /orders/search?q=Maria         │
└────────┬────────────────────────────────┘
         │
         ▼ HTTP GET (com JWT)
┌──────────────────────────────────────────────────────┐
│  BACKEND (routers/orders.py)                         │
│                                                      │
│  Endpoint: search_orders(q: str, user: User)        │
│                                                      │
│  1. Extrai restaurant_id do token JWT               │
│  2. Normaliza query:                                │
│     - Remove acentos (unicodedata.normalize)        │
│     - Converte para lowercase                       │
│  3. Tenta match por short_id (se for número)        │
│  4. Tenta match por tracking_code (se "MF-")        │
│  5. Busca por nome no Customer (LIKE %maria%)       │
│  6. Busca por telefone no Customer                  │
│  7. Filtra por:                                     │
│     - restaurant_id (multi-tenant)                  │
│     - status != DELIVERED                           │
│  8. Ordena por created_at DESC                      │
│  9. Limita a 10 resultados                          │
│  10. Retorna lista de pedidos                       │
└────────┬─────────────────────────────────────────────┘
         │
         ▼ HTTP 200 Response
┌──────────────────────────────────────┐
│  FRONTEND (SearchResults)            │
│                                      │
│  1. Exibe cards dos pedidos          │
│  2. Mostra: #ID, nome, status, lote  │
│  3. Botão "Ver Detalhes no Mapa"     │
└──────────────────────────────────────┘
```

### 2. Atendente Abre Detalhes no Mapa

```
┌──────────────────────────┐
│   ATENDENTE              │
│ clica "Ver Detalhes"     │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────────────────────────┐
│  FRONTEND (TrackingModal)                    │
│                                              │
│  1. Abre modal fullscreen                    │
│  2. GET /orders/{id}/tracking-details        │
│  3. Renderiza mapa (Leaflet.js)              │
│  4. Inicia polling (10 segundos)             │
└────────┬─────────────────────────────────────┘
         │
         ▼ HTTP GET (com JWT)
┌──────────────────────────────────────────────────────────┐
│  BACKEND (routers/orders.py)                             │
│                                                          │
│  Endpoint: get_order_tracking_details(order_id, user)   │
│                                                          │
│  1. Busca Order por ID                                   │
│  2. Valida restaurant_id (multi-tenant)                  │
│  3. Se pedido tem batch_id:                              │
│     a) Busca Batch                                       │
│     b) Busca todos Orders do lote (ORDER BY stop_order) │
│     c) Calcula position (stop_order do pedido)           │
│     d) Busca Courier vinculado ao batch                  │
│     e) Busca GPS atual do motoboy (last_lat, last_lng)  │
│     f) Busca polyline: get_batch_route_polyline()       │
│  4. Monta resposta estruturada:                          │
│     - order: Dados completos do pedido                   │
│     - batch: Info do lote + lista de pedidos            │
│     - courier: Dados do motoboy + GPS                    │
│     - route: Polyline + waypoints                        │
│  5. Retorna OrderTrackingDetails                         │
└────────┬─────────────────────────────────────────────────┘
         │
         ▼ HTTP 200 Response
┌────────────────────────────────────────────────────────┐
│  FRONTEND (TrackingModal)                              │
│                                                        │
│  1. Renderiza mapa interativo (Leaflet)                │
│  2. Adiciona elementos:                                │
│     - Polyline da rota (azul)                          │
│     - Marcador restaurante (laranja 🏪)                │
│     - Marcador motoboy (azul pulsante 🏍️)             │
│     - Marcadores pedidos (numerados 1, 2, 3...)        │
│     - Destaca pedido atual (cor diferente)             │
│  3. Ajusta zoom para mostrar tudo (fitBounds)          │
│  4. Exibe painel lateral:                              │
│     - Detalhes do pedido                               │
│     - Info do motoboy                                  │
│     - Lista de próximas entregas                       │
│     - Botão WhatsApp                                   │
└────────────────────────────────────────────────────────┘
```

### 3. Atualização em Tempo Real (Polling)

```
┌────────────────────────────────┐
│  FRONTEND (TrackingModal)      │
│                                │
│  useEffect(() => {             │
│    const interval = setInterval│
│      () => fetchUpdates(),     │
│      10000                     │
│    );                          │
│    return clearInterval;       │
│  }, [orderId]);                │
└────────┬───────────────────────┘
         │
         ▼ A cada 10 segundos
┌────────────────────────────────────────┐
│  BACKEND (GET /tracking-details)       │
│                                        │
│  1. Busca dados atualizados            │
│  2. GPS do motoboy pode ter mudado     │
│  3. Status do pedido pode ter mudado   │
│  4. Retorna novos dados                │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│  FRONTEND (TrackingModal)              │
│                                        │
│  1. useEffect detecta mudança em state │
│  2. Re-renderiza marcador do motoboy   │
│  3. Atualiza status se mudou           │
│  4. Mapa continua interativo           │
└────────────────────────────────────────┘
```

### 4. Envio por WhatsApp

```
┌───────────────────────────────┐
│   ATENDENTE                   │
│ clica "📱 Enviar por WhatsApp"│
└────────┬──────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────┐
│  FRONTEND (handleSendWhatsApp)               │
│                                              │
│  1. Lê tracking_code do pedido               │
│  2. Monta mensagem:                          │
│     "Olá! Seu pedido #1234 está Em Rota.    │
│      Acompanhe: https://.../track/MF-ABC123"│
│  3. Constrói URL do WhatsApp:                │
│     https://wa.me/?text={mensagem_encoded}  │
│  4. window.open(url, '_blank')               │
└────────┬─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  WHATSAPP WEB/APP                   │
│                                     │
│  1. Abre com mensagem pré-pronta    │
│  2. Atendente seleciona contato     │
│  3. Envia                           │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  CLIENTE                            │
│                                     │
│  1. Recebe link                     │
│  2. Clica no link                   │
│  3. GET /orders/track/{code}        │
│  4. Vê rastreamento público         │
└─────────────────────────────────────┘
```

---

## Arquitetura Frontend

### Estrutura de Componentes

```
TrackingPage (componente principal)
├── SearchInput (campo de busca)
│   ├── Debounce (300ms)
│   ├── Loading indicator
│   └── Icon de lupa
├── SearchResults (lista de resultados)
│   └── ResultCard (cada pedido)
│       ├── Short ID (#1234)
│       ├── Nome do cliente
│       ├── StatusBadge
│       ├── Info do motoboy
│       ├── Posição na fila
│       └── Botão "Ver Detalhes"
└── TrackingModal (modal com mapa)
    ├── TrackingMap (mapa Leaflet)
    │   ├── Polyline da rota
    │   ├── Marcador restaurante
    │   ├── Marcador motoboy
    │   └── Marcadores pedidos (1, 2, 3...)
    └── OrderDetailsPanel (painel lateral)
        ├── Detalhes do pedido
        ├── Info do motoboy
        ├── Lista de entregas
        └── Botão WhatsApp
```

### Estados React

```javascript
// TrackingPage
const [query, setQuery] = useState('');
const [searching, setSearching] = useState(false);
const [results, setResults] = useState([]);
const [selectedOrder, setSelectedOrder] = useState(null);
const [showModal, setShowModal] = useState(false);

// TrackingModal
const [trackingDetails, setTrackingDetails] = useState(null);
const [loading, setLoading] = useState(true);
const [map, setMap] = useState(null);
```

### Código de Busca (Simplificado)

```javascript
// TrackingPage - components.js
function TrackingPage() {
  const handleSearch = async (value) => {
    if (value.trim().length < 2) return;

    setSearching(true);
    const res = await authFetch(
      `${API_URL}/orders/search?q=${encodeURIComponent(value)}`
    );

    if (res.ok) {
      const data = await res.json();
      setResults(data);
    }

    setSearching(false);
  };

  // Debounce
  useEffect(() => {
    const timer = setTimeout(() => {
      if (query) handleSearch(query);
    }, 300);
    return () => clearTimeout(timer);
  }, [query]);

  return (
    <div className="tracking-page">
      <h1>📍 Rastreamento de Pedidos</h1>
      <SearchInput
        value={query}
        onChange={setQuery}
        searching={searching}
      />
      <SearchResults
        results={results}
        onSelect={handleOpenModal}
      />
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

### Código do Mapa (Simplificado)

```javascript
// TrackingModal - components.js
function TrackingMap({ trackingDetails }) {
  const mapRef = useRef(null);

  useEffect(() => {
    if (!mapRef.current || !trackingDetails?.route) return;

    // Inicializa mapa
    const map = L.map(mapRef.current).setView([lat, lng], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

    // Adiciona polyline da rota
    const decoded = decodePolyline(trackingDetails.route.polyline);
    L.polyline(decoded, { color: '#60a5fa', weight: 4 }).addTo(map);

    // Marcador do restaurante
    L.marker([restaurantLat, restaurantLng], {
      icon: createCustomIcon('🏪', 'orange')
    }).addTo(map).bindPopup('Restaurante');

    // Marcador do motoboy (pulsante)
    if (trackingDetails.courier?.current_lat) {
      L.marker([
        trackingDetails.courier.current_lat,
        trackingDetails.courier.current_lng
      ], {
        icon: createPulsingIcon('🏍️')
      }).addTo(map).bindPopup('Motoboy');
    }

    // Marcadores dos pedidos (numerados)
    trackingDetails.batch?.orders.forEach((order, index) => {
      const isCurrentOrder = order.id === trackingDetails.order.id;
      L.marker([order.lat, order.lng], {
        icon: createNumberedIcon(index + 1, isCurrentOrder)
      }).addTo(map).bindPopup(`${index + 1}. ${order.customer_name}`);
    });

    // Ajusta zoom para mostrar tudo
    const bounds = L.latLngBounds(decoded);
    map.fitBounds(bounds, { padding: [50, 50] });

    return () => map.remove(); // Cleanup
  }, [trackingDetails]);

  return <div ref={mapRef} className="tracking-map" />;
}
```

---

## Arquitetura Backend

### Novos Schemas (models.py)

```python
# Schemas de Resposta
class SimpleOrder(BaseModel):
    id: str
    short_id: int
    customer_name: str
    address_text: str
    lat: Optional[float]
    lng: Optional[float]
    status: OrderStatus
    stop_order: Optional[int]

class Waypoint(BaseModel):
    lat: float
    lng: float
    address: str
    order: int

class RouteInfo(BaseModel):
    polyline: str
    waypoints: List[Waypoint]

class CourierInfo(BaseModel):
    id: str
    name: str
    last_name: str
    phone: str
    current_lat: Optional[float]
    current_lng: Optional[float]

class BatchInfo(BaseModel):
    id: str
    status: BatchStatus
    position: int  # stop_order do pedido atual
    total: int     # total de pedidos no lote
    orders: List[SimpleOrder]

class OrderTrackingDetails(BaseModel):
    order: OrderResponse
    batch: Optional[BatchInfo] = None
    courier: Optional[CourierInfo] = None
    route: Optional[RouteInfo] = None
```

### Endpoint de Busca (orders.py)

```python
# routers/orders.py
from unicodedata import normalize

def normalize_text(text: str) -> str:
    """Remove acentos e converte para lowercase"""
    nfkd = normalize('NFKD', text)
    return ''.join([c for c in nfkd if not unicodedata.combining(c)]).lower()

@router.get("/search", response_model=List[OrderResponse])
def search_orders(
    q: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Busca pedidos por múltiplos critérios
    """
    # Normaliza query
    normalized_query = normalize_text(q)

    # Tenta match por short_id (se for número)
    if q.replace('#', '').isdigit():
        short_id = int(q.replace('#', ''))
        statement = select(Order).where(
            Order.restaurant_id == current_user.restaurant_id,
            Order.short_id == short_id,
            Order.status != OrderStatus.DELIVERED
        )
        result = session.exec(statement).first()
        if result:
            return [result]

    # Tenta match por tracking_code
    if q.upper().startswith('MF-'):
        statement = select(Order).where(
            Order.restaurant_id == current_user.restaurant_id,
            Order.tracking_code == q.upper(),
            Order.status != OrderStatus.DELIVERED
        )
        result = session.exec(statement).first()
        if result:
            return [result]

    # Busca por nome ou telefone (via Customer)
    statement = select(Order).join(Customer).where(
        Order.restaurant_id == current_user.restaurant_id,
        Order.status != OrderStatus.DELIVERED,
        or_(
            func.lower(func.unaccent(Customer.name)).like(f'%{normalized_query}%'),
            Customer.phone.like(f'%{q}%')
        )
    ).order_by(Order.created_at.desc()).limit(10)

    results = session.exec(statement).all()
    return results
```

### Endpoint de Detalhes (orders.py)

```python
# routers/orders.py
@router.get("/{order_id}/tracking-details", response_model=OrderTrackingDetails)
def get_order_tracking_details(
    order_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Retorna detalhes completos para rastreamento
    """
    # Busca pedido
    order = session.get(Order, order_id)
    if not order or order.restaurant_id != current_user.restaurant_id:
        raise HTTPException(404, "Pedido não encontrado")

    # Inicializa resposta
    response = OrderTrackingDetails(order=order)

    # Se pedido tem batch
    if order.batch_id:
        batch = session.get(Batch, order.batch_id)

        # Busca todos pedidos do lote
        batch_orders = session.exec(
            select(Order)
            .where(Order.batch_id == batch.id)
            .order_by(Order.stop_order)
        ).all()

        # Monta BatchInfo
        response.batch = BatchInfo(
            id=batch.id,
            status=batch.status,
            position=order.stop_order,
            total=len(batch_orders),
            orders=[SimpleOrder.from_orm(o) for o in batch_orders]
        )

        # Busca motoboy
        courier = session.get(Courier, batch.courier_id)
        response.courier = CourierInfo(
            id=courier.id,
            name=courier.name,
            last_name=courier.last_name,
            phone=courier.phone,
            current_lat=courier.last_lat,
            current_lng=courier.last_lng
        )

        # Busca rota
        polyline_data = get_batch_route_polyline(batch.id, session)
        if polyline_data:
            response.route = RouteInfo(
                polyline=polyline_data['polyline'],
                waypoints=polyline_data['waypoints']
            )

    return response
```

---

## Integração com Leaflet.js

### Instalação (index.html)

```html
<!-- CDN Links -->
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
```

### Decodificação de Polyline

```javascript
// components.js - Função auxiliar
function decodePolyline(encoded) {
  const poly = [];
  let index = 0, len = encoded.length;
  let lat = 0, lng = 0;

  while (index < len) {
    let b, shift = 0, result = 0;
    do {
      b = encoded.charCodeAt(index++) - 63;
      result |= (b & 0x1f) << shift;
      shift += 5;
    } while (b >= 0x20);
    const dlat = ((result & 1) ? ~(result >> 1) : (result >> 1));
    lat += dlat;

    shift = 0;
    result = 0;
    do {
      b = encoded.charCodeAt(index++) - 63;
      result |= (b & 0x1f) << shift;
      shift += 5;
    } while (b >= 0x20);
    const dlng = ((result & 1) ? ~(result >> 1) : (result >> 1));
    lng += dlng;

    poly.push([lat / 1e5, lng / 1e5]);
  }
  return poly;
}
```

### Marcador Pulsante (Motoboy)

```css
/* dashboard.css */
@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.7);
  }
  50% {
    transform: scale(1.1);
    box-shadow: 0 0 0 10px rgba(59, 130, 246, 0);
  }
}

.courier-marker {
  animation: pulse 2s ease-in-out infinite;
}
```

---

## Atualização em Tempo Real

### Polling (Frontend)

```javascript
// TrackingModal - components.js
useEffect(() => {
  if (!showModal || !selectedOrder) return;

  const fetchUpdates = async () => {
    const res = await authFetch(
      `${API_URL}/orders/${selectedOrder.id}/tracking-details`
    );
    if (res.ok) {
      const data = await res.json();
      setTrackingDetails(data);
    }
  };

  fetchUpdates(); // Inicial
  const interval = setInterval(fetchUpdates, 10000); // 10s

  return () => clearInterval(interval);
}, [showModal, selectedOrder]);
```

### Otimização: Conditional Requests (Futuro)

```javascript
// Usar ETag para evitar transferir dados se nada mudou
const res = await authFetch('/tracking-details', {
  headers: {
    'If-None-Match': lastETag
  }
});

if (res.status === 304) {
  // Sem mudanças, não atualiza
} else {
  // Atualiza com novos dados
  setTrackingDetails(await res.json());
  setLastETag(res.headers.get('ETag'));
}
```

---

## Compartilhamento via WhatsApp

### Fluxo Completo

1. **Atendente clica botão "Enviar por WhatsApp"**
2. **Frontend monta mensagem:**
   ```javascript
   const message = `Olá! Seu pedido #${shortId} está ${statusText}. Acompanhe em tempo real: ${trackingUrl}`;
   ```
3. **Frontend abre WhatsApp:**
   ```javascript
   const whatsappUrl = `https://wa.me/?text=${encodeURIComponent(message)}`;
   window.open(whatsappUrl, '_blank');
   ```
4. **Cliente recebe link e acessa**
5. **Backend retorna rastreamento público (GET /orders/track/{code})**

### Endpoint Público de Rastreamento

```python
# routers/orders.py
@router.get("/track/{tracking_code}")
def track_order_public(tracking_code: str, session: Session):
    """
    Rastreamento público (sem autenticação)
    Retorna apenas informações básicas
    """
    order = session.exec(
        select(Order).where(Order.tracking_code == tracking_code.upper())
    ).first()

    if not order:
        raise HTTPException(404, "Pedido não encontrado")

    return {
        "tracking_code": order.tracking_code,
        "customer_name": order.customer_name,
        "status": order.status,
        "status_label": get_status_label(order.status),
        "created_at": order.created_at,
        "estimated_delivery": estimate_delivery_time(order)
    }
```

---

## Multi-tenant e Segurança

### Filtros Automáticos

Todos os endpoints de rastreamento SEMPRE filtram por `restaurant_id`:

```python
# ✅ CORRETO - Multi-tenant seguro
statement = select(Order).where(
    Order.restaurant_id == current_user.restaurant_id,
    Order.short_id == short_id
)

# ❌ ERRADO - Vulnerabilidade de segurança
statement = select(Order).where(Order.short_id == short_id)
```

### Validação de Acesso

```python
# Sempre valida que pedido pertence ao restaurante
order = session.get(Order, order_id)
if not order or order.restaurant_id != current_user.restaurant_id:
    raise HTTPException(404, "Pedido não encontrado")
```

### Limitação de Resultados

```python
# Busca limitada a 10 resultados
.limit(10)
```

### Dados Sensíveis

- **Dashboard (autenticado):** Retorna endereço completo, telefone, etc.
- **Rastreamento público:** Retorna apenas informações básicas (sem endereço completo)

---

## Troubleshooting

### Erro: "Nenhum resultado encontrado"

**Possíveis causas:**
1. Pedido já foi entregue (filtro `status != DELIVERED`)
2. Pedido pertence a outro restaurante (multi-tenant)
3. Query muito curta (mínimo 2 caracteres)

**Solução:**
- Verificar status do pedido no banco
- Conferir `restaurant_id` do pedido e do usuário
- Digitar pelo menos 2 caracteres na busca

---

### Erro: "Mapa não carrega"

**Possíveis causas:**
1. CDN do Leaflet.js bloqueado
2. Coordenadas inválidas
3. Polyline mal formatada

**Solução:**
```javascript
// Verificar no console do browser
console.log('Leaflet loaded?', typeof L !== 'undefined');
console.log('Coordinates:', lat, lng);
console.log('Polyline:', polyline);
```

---

### Motoboy não aparece no mapa

**Possíveis causas:**
1. Motoboy não enviou GPS recente (`last_lat` / `last_lng` são null)
2. Coordenadas fora do bounds do mapa

**Solução:**
- Verificar se `courier.current_lat` existe
- Adicionar fallback para última posição conhecida

```javascript
if (trackingDetails.courier?.current_lat) {
  // Adiciona marcador
} else {
  console.log('GPS do motoboy não disponível');
  // Mostrar mensagem: "Aguardando localização do motoboy"
}
```

---

### WhatsApp não abre

**Possíveis causas:**
1. URL mal formatada
2. Bloqueio de pop-up do navegador

**Solução:**
```javascript
// Verificar se window.open funcionou
const newWindow = window.open(whatsappUrl, '_blank');
if (!newWindow) {
  alert('Por favor, permita pop-ups para enviar por WhatsApp');
}
```

---

### Polling consome muitos recursos

**Sintoma:** CPU alta, muitas requisições

**Solução:**
- Aumentar intervalo de 10s para 30s
- Pausar polling quando modal está fechado
- Usar WebSocket no futuro (substituir polling)

```javascript
// Pausar quando modal fecha
useEffect(() => {
  if (!showModal) return; // ✅ Não faz polling se modal fechado

  const interval = setInterval(fetchUpdates, 10000);
  return () => clearInterval(interval);
}, [showModal]);
```

---

## 📊 Resumo Técnico

| Componente | Tecnologia | Arquivo |
|------------|-----------|---------|
| Frontend - Busca | React + useState + debounce | components.js (TrackingPage) |
| Frontend - Mapa | Leaflet.js 1.9.4 | components.js (TrackingMap) |
| Frontend - Modal | React + useEffect + polling | components.js (TrackingModal) |
| Backend - Busca | FastAPI + SQLModel + unicodedata | routers/orders.py (search_orders) |
| Backend - Detalhes | FastAPI + SQLModel + joins | routers/orders.py (get_order_tracking_details) |
| Backend - Schemas | Pydantic BaseModel | models.py (OrderTrackingDetails, etc.) |
| Normalização | unicodedata.normalize('NFKD') | routers/orders.py (normalize_text) |
| Multi-tenant | JWT + restaurant_id filter | Todos endpoints protegidos |
| Mapa | OpenStreetMap tiles | Leaflet.js default |
| Polyline | Google Directions API | batch_service.py |
| GPS | Courier.last_lat / last_lng | Atualizado pelo app PWA |

---

## 🚀 Melhorias Futuras

1. **WebSocket para real-time:**
   - Substituir polling por WebSocket
   - Push de atualizações quando status muda

2. **Cache de polylines:**
   - Redis para cachear rotas já calculadas
   - Evitar chamadas repetidas ao Google Maps API

3. **Histórico de rastreamento:**
   - Salvar snapshots de GPS a cada minuto
   - Replay da rota completa depois da entrega

4. **Notificações proativas:**
   - Push notification para atendente quando cliente abre link de rastreio
   - Email automático com link de rastreio

5. **Analytics:**
   - Quantas vezes cada pedido foi rastreado
   - Tempo médio de visualização
   - Taxa de conversão (ligações → rastreios enviados)

---

**Próximo:** Ver [API_ENDPOINTS.md](./API_ENDPOINTS.md) para detalhes completos dos endpoints.
