# 🔗 Comunicação Frontend ↔ Backend - MotoFlash

**Versão:** 0.9.0
**Última atualização:** 2026-01-25

Este documento detalha **exatamente** como cada página do frontend se comunica com o backend, com exemplos de código real.

---

## 📋 Índice

1. [Estrutura Geral](#estrutura-geral)
2. [Dashboard (index.html)](#dashboard-indexhtml) - **Arquitetura Modular** ⭐
3. [App Motoboy (motoboy.html)](#app-motoboy-motoboyhtml)
4. [Autenticação (auth.html)](#autenticação-authhtml)
5. [Convites (convite.html)](#convites-convitehtml)
6. [Padrões de Código](#padrões-de-código)

> **Nota:** As páginas `cardapio.html` e `clientes.html` foram **integradas ao dashboard** (index.html) como parte da arquitetura SPA modular. Veja [ARQUITETURA_MODULAR.md](./ARQUITETURA_MODULAR.md) para detalhes.

---

## Estrutura Geral

### Localização dos Arquivos

```
backend/
├── static/               # Frontend (Arquitetura Modular)
│   ├── index.html       # Dashboard principal (36 linhas - SPA)
│   ├── motoboy.html     # App PWA motoboys
│   ├── auth.html        # Login/Cadastro
│   ├── convite.html     # Aceitar convite
│   ├── recuperar-senha.html
│   │
│   ├── css/
│   │   └── dashboard.css # Estilos do dashboard
│   │
│   └── js/
│       ├── utils/
│       │   └── helpers.js  # Auth, config, API utils
│       ├── components.js   # Todos componentes React
│       └── app.js          # Componente App principal
```

### Tecnologia Frontend

**Dashboard (index.html) - Arquitetura Modular:**
- **React 18** (via CDN - desenvolvimento mode)
- **Babel Standalone** (JSX compilado no browser)
- **Tailwind CSS** (via CDN)
- **Fetch API** (requisições HTTP)
- **Código separado em módulos** (helpers, components, app)

**Outras páginas:**
- Mesma stack do dashboard (React 18 + Tailwind)
- Estrutura monolítica (código inline)

**Estrutura Padrão:**
```html
<!DOCTYPE html>
<html>
<head>
  <script src="https://unpkg.com/react@18/umd/react.development.js"></script>
  <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body>
  <div id="root"></div>

  <script type="text/babel">
    // Código React aqui
  </script>
</body>
</html>
```

---

## Dashboard (index.html) - **ARQUITETURA MODULAR**

### Localização
**URL:** `/` ou `/dashboard`
**Arquivos:**
```
backend/static/
├── index.html (36 linhas - estrutura base)
├── css/dashboard.css (556 linhas)
└── js/
    ├── utils/helpers.js (43 linhas)
    ├── components.js (2907 linhas)
    └── app.js (192 linhas)
```

### Responsabilidades
- **SPA (Single Page Application)** com navegação interna
- Visualizar pedidos em tempo real
- Criar novos pedidos
- Executar dispatch
- Visualizar lotes e rotas
- Gerenciar motoboys
- **Gestão de cardápio** (página integrada)
- **Gestão de clientes** (página integrada)

### Arquitetura

#### **index.html** (Estrutura Base - 36 linhas)
```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>MotoFlash - Dashboard</title>

    <!-- External Libraries -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/react@18/umd/react.development.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>

    <!-- Custom Styles -->
    <link rel="stylesheet" href="/static/css/dashboard.css">
</head>
<body>
    <div class="background">
        <img src="https://images.unsplash.com/photo-1558618666-fcd25c85cd64?q=80&w=2864" alt="Motoboy">
    </div>

    <div id="root"></div>

    <!-- Application Scripts -->
    <script type="text/babel" src="/static/js/utils/helpers.js"></script>
    <script type="text/babel" src="/static/js/components.js"></script>
    <script type="text/babel" src="/static/js/app.js"></script>
</body>
</html>
```

#### **helpers.js** (Utilitários - 43 linhas)
- Configuração (API_URL)
- Funções de autenticação (getToken, isLoggedIn, authFetch)
- Verificação de login automática

#### **components.js** (Componentes React - 2907 linhas)
- Timer, StatusBadge, StatsPanel
- AlertsPanel, NewOrderForm, OrdersList
- CouriersPanel, ActiveBatches, DispatchControl
- Sidebar, DashboardPage
- **CardapioPage** (gestão de cardápio integrada)
- **ClientesPage** (gestão de clientes integrada)
- PlaceholderPage (páginas futuras)

#### **app.js** (App Principal - 192 linhas)
- Componente MotoFlashApp
- Gerenciamento de estado (pedidos, motoboys, batches)
- Navegação entre páginas
- Polling de dados
- ReactDOM.render

---

### 1. Autenticação e Inicialização

```javascript
// index.html (React Component)
function App() {
  const [token, setToken] = useState(null);
  const [restaurant, setRestaurant] = useState(null);

  // Ao carregar página, busca token do localStorage
  useEffect(() => {
    const savedToken = localStorage.getItem('token');
    const savedRestaurant = localStorage.getItem('restaurant');

    if (!savedToken) {
      window.location.href = '/login';
      return;
    }

    setToken(savedToken);
    setRestaurant(JSON.parse(savedRestaurant));

    // Valida token
    validateToken(savedToken);
  }, []);

  async function validateToken(token) {
    try {
      const response = await fetch('/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        // Token inválido, redireciona para login
        localStorage.clear();
        window.location.href = '/login';
      }
    } catch (error) {
      console.error('Erro ao validar token:', error);
    }
  }

  return (
    <div>
      {/* Interface do dashboard */}
    </div>
  );
}
```

---

### 2. Buscar e Exibir Pedidos

```javascript
// index.html
function OrdersList() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const token = localStorage.getItem('token');

  // Busca pedidos ao carregar
  useEffect(() => {
    fetchOrders();

    // Polling: atualiza a cada 10 segundos
    const interval = setInterval(fetchOrders, 10000);
    return () => clearInterval(interval);
  }, []);

  async function fetchOrders() {
    try {
      const response = await fetch('/orders', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setOrders(data.orders);
      }
    } catch (error) {
      console.error('Erro ao buscar pedidos:', error);
    } finally {
      setLoading(false);
    }
  }

  // Filtrar pedidos por status
  const readyOrders = orders.filter(o => o.status === 'READY');
  const assignedOrders = orders.filter(o => o.status === 'ASSIGNED');
  const deliveredOrders = orders.filter(o => o.status === 'DELIVERED');

  return (
    <div className="grid grid-cols-3 gap-4">
      {/* Coluna READY */}
      <div>
        <h3>Prontos ({readyOrders.length})</h3>
        {readyOrders.map(order => (
          <OrderCard key={order.id} order={order} />
        ))}
      </div>

      {/* Coluna ASSIGNED */}
      <div>
        <h3>Atribuídos ({assignedOrders.length})</h3>
        {assignedOrders.map(order => (
          <OrderCard key={order.id} order={order} />
        ))}
      </div>

      {/* Coluna DELIVERED */}
      <div>
        <h3>Entregues ({deliveredOrders.length})</h3>
        {deliveredOrders.map(order => (
          <OrderCard key={order.id} order={order} />
        ))}
      </div>
    </div>
  );
}
```

---

### 3. Criar Novo Pedido

```javascript
// index.html
function CreateOrderModal({ isOpen, onClose, onOrderCreated }) {
  const [formData, setFormData] = useState({
    customer_name: '',
    customer_phone: '',
    address_text: '',
    address_complement: '',
    items: [],
    total: 0,
    payment_method: 'DINHEIRO',
    prep_type: 'LONG'
  });
  const token = localStorage.getItem('token');

  async function handleSubmit(e) {
    e.preventDefault();

    try {
      const response = await fetch('/orders', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        const newOrder = await response.json();
        onOrderCreated(newOrder); // Callback para atualizar lista
        onClose();
        alert('Pedido criado com sucesso!');
      } else {
        const error = await response.json();
        alert(`Erro: ${error.detail}`);
      }
    } catch (error) {
      console.error('Erro ao criar pedido:', error);
      alert('Erro ao criar pedido');
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Nome do cliente"
          value={formData.customer_name}
          onChange={(e) => setFormData({...formData, customer_name: e.target.value})}
          required
        />

        <input
          type="tel"
          placeholder="Telefone"
          value={formData.customer_phone}
          onChange={(e) => setFormData({...formData, customer_phone: e.target.value})}
          required
        />

        <input
          type="text"
          placeholder="Endereço completo"
          value={formData.address_text}
          onChange={(e) => setFormData({...formData, address_text: e.target.value})}
          required
        />

        {/* Outros campos... */}

        <button type="submit">Criar Pedido</button>
      </form>
    </Modal>
  );
}
```

---

### 4. Executar Dispatch

```javascript
// index.html
function DispatchButton() {
  const [loading, setLoading] = useState(false);
  const token = localStorage.getItem('token');

  async function handleDispatch() {
    if (!confirm('Deseja criar lotes para os pedidos prontos?')) {
      return;
    }

    setLoading(true);

    try {
      const response = await fetch('/dispatch/run', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const result = await response.json();
        alert(result.message);

        // Recarrega pedidos e lotes
        window.location.reload();
      } else {
        const error = await response.json();
        alert(`Erro: ${error.detail}`);
      }
    } catch (error) {
      console.error('Erro ao executar dispatch:', error);
      alert('Erro ao executar dispatch');
    } finally {
      setLoading(false);
    }
  }

  return (
    <button
      onClick={handleDispatch}
      disabled={loading}
      className="bg-orange-500 text-white px-4 py-2 rounded"
    >
      {loading ? 'Processando...' : 'Despachar Pedidos'}
    </button>
  );
}
```

---

### 5. Visualizar Rotas no Mapa (Leaflet)

```javascript
// index.html
function BatchMap({ batchId }) {
  const mapRef = useRef(null);
  const [map, setMap] = useState(null);

  useEffect(() => {
    // Inicializa mapa Leaflet
    if (!map && mapRef.current) {
      const leafletMap = L.map(mapRef.current).setView([-21.2020, -47.8130], 13);

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap'
      }).addTo(leafletMap);

      setMap(leafletMap);
    }
  }, []);

  useEffect(() => {
    if (map && batchId) {
      fetchAndDrawRoute(batchId);
    }
  }, [map, batchId]);

  async function fetchAndDrawRoute(batchId) {
    try {
      const response = await fetch(`/batches/${batchId}/polyline`);
      const data = await response.json();

      if (data.polyline) {
        // Decodifica polyline (Google encoded)
        const decoded = decodePolyline(data.polyline);

        // Desenha rota no mapa
        L.polyline(decoded, {
          color: '#ff6b00',
          weight: 4,
          opacity: 0.7
        }).addTo(map);

        // Adiciona marcadores dos pedidos
        data.orders.forEach((order, index) => {
          L.marker([order.lat, order.lng])
            .bindPopup(`
              <b>Parada ${index + 1}</b><br>
              ${order.address}
            `)
            .addTo(map);
        });

        // Ajusta zoom para mostrar toda a rota
        const bounds = L.latLngBounds(decoded);
        map.fitBounds(bounds);
      }
    } catch (error) {
      console.error('Erro ao buscar rota:', error);
    }
  }

  // Função auxiliar para decodificar polyline do Google
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

  return <div ref={mapRef} style={{ height: '500px' }} />;
}
```

---

## App Motoboy (motoboy.html)

### Localização
**URL:** `/motoboy`
**Arquivo:** `backend/static/motoboy.html`
**Tamanho:** ~80KB (React inline + PWA)

### Responsabilidades
- Login do motoboy
- Aceitar lotes de entrega
- Visualizar rota
- Marcar pedidos como entregues

---

### 1. Login do Motoboy

```javascript
// motoboy.html
function LoginScreen() {
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleLogin(e) {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch('/couriers/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ phone, password })
      });

      const data = await response.json();

      if (data.success) {
        // Salva dados do motoboy (NÃO usa JWT)
        localStorage.setItem('courier', JSON.stringify(data.courier));
        localStorage.setItem('restaurant_name', data.restaurant_name);

        // Redireciona para tela de lotes
        window.location.href = '/motoboy#batches';
      } else {
        alert(data.message);
      }
    } catch (error) {
      console.error('Erro ao fazer login:', error);
      alert('Erro ao fazer login');
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleLogin}>
      <input
        type="tel"
        placeholder="Celular"
        value={phone}
        onChange={(e) => setPhone(e.target.value)}
        required
      />

      <input
        type="password"
        placeholder="Senha"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
      />

      <button type="submit" disabled={loading}>
        {loading ? 'Entrando...' : 'Entrar'}
      </button>
    </form>
  );
}
```

---

### 2. Verificar Novos Lotes (Polling)

```javascript
// motoboy.html
function BatchesScreen() {
  const [currentBatch, setCurrentBatch] = useState(null);
  const [orders, setOrders] = useState([]);
  const courier = JSON.parse(localStorage.getItem('courier'));

  useEffect(() => {
    checkForBatch();

    // Polling: verifica novo lote a cada 30 segundos
    const interval = setInterval(checkForBatch, 30000);
    return () => clearInterval(interval);
  }, []);

  async function checkForBatch() {
    try {
      const response = await fetch(`/couriers/${courier.id}/batch`);

      if (response.ok) {
        const data = await response.json();

        if (data.batch) {
          setCurrentBatch(data.batch);
          setOrders(data.orders);

          // Notificação visual
          if (data.batch.status === 'ASSIGNED' && !currentBatch) {
            alert('Novo lote disponível!');
            playNotificationSound();
          }
        } else {
          setCurrentBatch(null);
          setOrders([]);
        }
      }
    } catch (error) {
      console.error('Erro ao verificar lote:', error);
    }
  }

  function playNotificationSound() {
    const audio = new Audio('/static/notification.mp3');
    audio.play().catch(e => console.error('Erro ao tocar som:', e));
  }

  if (!currentBatch) {
    return (
      <div className="text-center p-8">
        <h2>Aguardando novo lote...</h2>
        <p>Você será notificado quando houver entregas</p>
      </div>
    );
  }

  return (
    <div>
      <h2>Lote Atual</h2>
      <p>{orders.length} entregas</p>

      <BatchMap batchId={currentBatch.id} orders={orders} />

      <OrdersList orders={orders} onOrderDelivered={checkForBatch} />
    </div>
  );
}
```

---

### 3. Marcar Pedido como Entregue

```javascript
// motoboy.html
function OrderCard({ order, onDelivered }) {
  const [loading, setLoading] = useState(false);

  async function handleDeliver() {
    if (!confirm('Confirma entrega deste pedido?')) {
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(`/orders/${order.id}/deliver`, {
        method: 'POST'
      });

      if (response.ok) {
        alert('Pedido entregue com sucesso!');
        onDelivered(); // Callback para atualizar lista
      } else {
        alert('Erro ao marcar como entregue');
      }
    } catch (error) {
      console.error('Erro:', error);
      alert('Erro ao marcar como entregue');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="border p-4 rounded mb-2">
      <h3>Parada {order.stop_order}</h3>
      <p><strong>{order.customer_name}</strong></p>
      <p>{order.address_text}</p>
      <p>R$ {order.total.toFixed(2)}</p>

      {order.status !== 'DELIVERED' && (
        <button
          onClick={handleDeliver}
          disabled={loading}
          className="bg-green-500 text-white px-4 py-2 rounded mt-2"
        >
          {loading ? 'Salvando...' : 'Marcar como Entregue'}
        </button>
      )}
    </div>
  );
}
```

---

### 4. Finalizar Lote

```javascript
// motoboy.html
function CompleteBatchButton({ batchId, orders, courierId }) {
  const [loading, setLoading] = useState(false);

  // Verifica se todos pedidos foram entregues
  const allDelivered = orders.every(o => o.status === 'DELIVERED');

  async function handleComplete() {
    if (!allDelivered) {
      alert('Entregue todos os pedidos primeiro!');
      return;
    }

    if (!confirm('Finalizar este lote?')) {
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(`/couriers/${courierId}/batch-complete`, {
        method: 'POST'
      });

      if (response.ok) {
        alert('Lote finalizado! Aguardando próximo...');
        window.location.reload();
      } else {
        alert('Erro ao finalizar lote');
      }
    } catch (error) {
      console.error('Erro:', error);
      alert('Erro ao finalizar lote');
    } finally {
      setLoading(false);
    }
  }

  return (
    <button
      onClick={handleComplete}
      disabled={!allDelivered || loading}
      className="bg-blue-500 text-white px-4 py-2 rounded disabled:opacity-50"
    >
      {loading ? 'Finalizando...' : 'Finalizar Lote'}
    </button>
  );
}
```

---

## Autenticação (auth.html)

### Localização
**URL:** `/login`
**Arquivo:** `backend/static/auth.html`
**Tamanho:** ~52KB

### Responsabilidades
- Login de usuário (dashboard)
- Cadastro de restaurante (self-service)

---

### Tela Unificada (Login + Cadastro)

```javascript
// auth.html
function AuthPage() {
  const [mode, setMode] = useState('login'); // 'login' ou 'register'

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="bg-white p-8 rounded-lg shadow-lg max-w-md w-full">
        <h1 className="text-3xl font-bold mb-6 text-center">
          MotoFlash
        </h1>

        <div className="flex mb-4">
          <button
            onClick={() => setMode('login')}
            className={mode === 'login' ? 'flex-1 py-2 bg-orange-500 text-white' : 'flex-1 py-2'}
          >
            Login
          </button>
          <button
            onClick={() => setMode('register')}
            className={mode === 'register' ? 'flex-1 py-2 bg-orange-500 text-white' : 'flex-1 py-2'}
          >
            Cadastrar
          </button>
        </div>

        {mode === 'login' ? <LoginForm /> : <RegisterForm />}
      </div>
    </div>
  );
}

function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  async function handleSubmit(e) {
    e.preventDefault();

    const response = await fetch('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    if (response.ok) {
      const data = await response.json();

      // Verifica se está bloqueado (trial expirado)
      if (data.restaurant.blocked) {
        alert('Período de teste expirado. Entre em contato.');
        return;
      }

      // Salva token e dados
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('restaurant', JSON.stringify(data.restaurant));
      localStorage.setItem('user', JSON.stringify(data.user));

      // Redireciona
      window.location.href = '/dashboard';
    } else {
      const error = await response.json();
      alert(error.detail);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="email"
        placeholder="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
      />
      <input
        type="password"
        placeholder="Senha"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
      />
      <button type="submit">Entrar</button>
    </form>
  );
}
```

---

## Cardápio (cardapio.html)

### Responsabilidades
- Criar/editar categorias
- Criar/editar itens do menu
- Upload de imagens

---

### Upload de Imagem

```javascript
// cardapio.html
function ImageUpload({ onImageUploaded }) {
  const [uploading, setUploading] = useState(false);
  const token = localStorage.getItem('token');

  async function handleFileChange(e) {
    const file = e.target.files[0];

    if (!file) return;

    // Valida tamanho
    if (file.size > 5 * 1024 * 1024) {
      alert('Imagem muito grande (máx 5MB)');
      return;
    }

    setUploading(true);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        onImageUploaded(data.url);
      } else {
        alert('Erro ao fazer upload');
      }
    } catch (error) {
      console.error('Erro:', error);
      alert('Erro ao fazer upload');
    } finally {
      setUploading(false);
    }
  }

  return (
    <div>
      <input
        type="file"
        accept="image/*"
        onChange={handleFileChange}
        disabled={uploading}
      />
      {uploading && <p>Enviando...</p>}
    </div>
  );
}
```

---

## Padrões de Código

### 1. Requisição com Autenticação

```javascript
// Padrão para todas requisições autenticadas
async function fetchWithAuth(url, options = {}) {
  const token = localStorage.getItem('token');

  const response = await fetch(url, {
    ...options,
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      ...options.headers
    }
  });

  // Se 401, token expirou
  if (response.status === 401) {
    localStorage.clear();
    window.location.href = '/login';
    return;
  }

  return response;
}

// Uso
const response = await fetchWithAuth('/orders');
const data = await response.json();
```

---

### 2. Tratamento de Erros

```javascript
async function safeApiCall(apiFunction) {
  try {
    const result = await apiFunction();
    return { success: true, data: result };
  } catch (error) {
    console.error('Erro na API:', error);
    return { success: false, error: error.message };
  }
}

// Uso
const result = await safeApiCall(async () => {
  const response = await fetch('/orders');
  return await response.json();
});

if (result.success) {
  setOrders(result.data);
} else {
  alert('Erro ao buscar pedidos');
}
```

---

### 3. Loading States

```javascript
function DataComponent() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const response = await fetchWithAuth('/orders');
        const result = await response.json();
        setData(result);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  if (loading) return <div>Carregando...</div>;
  if (error) return <div>Erro: {error}</div>;
  if (!data) return <div>Nenhum dado</div>;

  return <div>{/* Renderiza dados */}</div>;
}
```

---

## 📝 Checklist de Integração

Ao adicionar nova funcionalidade, siga este checklist:

- [ ] **Frontend:** Cria estado React para os dados
- [ ] **Frontend:** Implementa função de fetch com `fetchWithAuth`
- [ ] **Frontend:** Trata loading/error states
- [ ] **Frontend:** Adiciona validação de formulário
- [ ] **Backend:** Cria endpoint na pasta `routers/`
- [ ] **Backend:** Adiciona validação de JWT (`Depends(get_current_user)`)
- [ ] **Backend:** Filtra por `restaurant_id` para multi-tenant
- [ ] **Backend:** Retorna erros HTTP apropriados (400, 404, etc.)
- [ ] **Teste:** Testa fluxo completo (frontend → backend → banco)

---

**Documentação Completa:**
- [ARQUITETURA.md](./ARQUITETURA.md) - Visão geral do sistema
- [API_ENDPOINTS.md](./API_ENDPOINTS.md) - Referência completa da API
- [FLUXOS.md](./FLUXOS.md) - Fluxos de dados detalhados
