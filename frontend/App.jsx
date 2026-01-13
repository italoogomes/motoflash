import { useState, useEffect, useCallback } from 'react';

// ============ CONFIGURAÇÃO ============
const API_URL = 'http://localhost:8000';

// ============ COMPONENTES AUXILIARES ============

const StatusBadge = ({ status }) => {
  const colors = {
    created: 'bg-gray-500',
    preparing: 'bg-yellow-500',
    ready: 'bg-green-500',
    assigned: 'bg-blue-500',
    picked_up: 'bg-purple-500',
    delivered: 'bg-emerald-600',
    available: 'bg-green-500',
    busy: 'bg-orange-500',
    offline: 'bg-gray-400',
  };
  
  const labels = {
    created: 'Criado',
    preparing: 'Preparando',
    ready: 'Pronto',
    assigned: 'Atribuído',
    picked_up: 'Coletado',
    delivered: 'Entregue',
    available: 'Disponível',
    busy: 'Em entrega',
    offline: 'Offline',
  };
  
  return (
    <span className={`${colors[status] || 'bg-gray-500'} text-white text-xs px-2 py-1 rounded-full font-medium`}>
      {labels[status] || status}
    </span>
  );
};

const Card = ({ children, className = '' }) => (
  <div className={`bg-white rounded-xl shadow-sm border border-gray-100 ${className}`}>
    {children}
  </div>
);

const Button = ({ children, onClick, variant = 'primary', disabled = false, className = '' }) => {
  const variants = {
    primary: 'bg-orange-500 hover:bg-orange-600 text-white',
    secondary: 'bg-gray-100 hover:bg-gray-200 text-gray-700',
    success: 'bg-green-500 hover:bg-green-600 text-white',
    danger: 'bg-red-500 hover:bg-red-600 text-white',
  };
  
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${variants[variant]} ${className}`}
    >
      {children}
    </button>
  );
};

// ============ PAINEL DE ESTATÍSTICAS ============

const StatsPanel = ({ stats }) => {
  if (!stats) return null;
  
  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
      <Card className="p-4 text-center">
        <div className="text-3xl font-bold text-orange-500">{stats.orders?.ready || 0}</div>
        <div className="text-sm text-gray-500">Pedidos Prontos</div>
      </Card>
      <Card className="p-4 text-center">
        <div className="text-3xl font-bold text-blue-500">{stats.orders?.assigned || 0}</div>
        <div className="text-sm text-gray-500">Em Rota</div>
      </Card>
      <Card className="p-4 text-center">
        <div className="text-3xl font-bold text-green-500">{stats.couriers?.available || 0}</div>
        <div className="text-sm text-gray-500">Motoboys Livres</div>
      </Card>
      <Card className="p-4 text-center">
        <div className="text-3xl font-bold text-purple-500">{stats.couriers?.busy || 0}</div>
        <div className="text-sm text-gray-500">Motoboys Ocupados</div>
      </Card>
      <Card className="p-4 text-center">
        <div className="text-3xl font-bold text-emerald-600">{stats.orders?.delivered || 0}</div>
        <div className="text-sm text-gray-500">Entregues Hoje</div>
      </Card>
    </div>
  );
};

// ============ SIMULADOR DE PEDIDOS ============

const OrderSimulator = ({ onOrderCreated }) => {
  const [loading, setLoading] = useState(false);
  
  // Endereços de Ribeirão Preto para simulação
  const fakeAddresses = [
    // Centro de Ribeirão Preto
    { text: 'Av. Presidente Vargas, 500 - Centro', lat: -21.1780, lng: -47.8100 },
    { text: 'Rua General Osório, 800 - Centro', lat: -21.1760, lng: -47.8080 },
    { text: 'Rua Visconde de Inhaúma, 300 - Centro', lat: -21.1770, lng: -47.8120 },
    // Zona Sul (Fiúsa / Jardim Botânico)
    { text: 'Av. Professor João Fiúsa, 1200 - Jardim Botânico', lat: -21.2050, lng: -47.8200 },
    { text: 'Rua Minas Gerais, 600 - Jardim Sumaré', lat: -21.2000, lng: -47.8150 },
    { text: 'Av. Wladimir Meirelles Ferreira, 800 - Jardim Botânico', lat: -21.2100, lng: -47.8250 },
    // Zona Norte (Campos Elíseos / Ipiranga)
    { text: 'Av. Independência, 1500 - Campos Elíseos', lat: -21.1550, lng: -47.8050 },
    { text: 'Rua Capitão Salomão, 400 - Alto do Ipiranga', lat: -21.1500, lng: -47.8000 },
    // Zona Oeste (Ribeirânia / Califórnia)
    { text: 'Av. Costábile Romano, 2000 - Ribeirânia', lat: -21.1700, lng: -47.8400 },
    { text: 'Rua João Arcadepani, 300 - Jardim Califórnia', lat: -21.1650, lng: -47.8350 },
    // Zona Leste (Vila Tibério / Quintino)
    { text: 'Av. Jerônimo Gonçalves, 1000 - Vila Tibério', lat: -21.1800, lng: -47.7900 },
    { text: 'Rua Quintino Bocaiúva, 500 - Quintino Facci II', lat: -21.1850, lng: -47.7850 },
  ];
  
  const createRandomOrder = async () => {
    setLoading(true);
    const addr = fakeAddresses[Math.floor(Math.random() * fakeAddresses.length)];
    const names = ['João', 'Maria', 'Pedro', 'Ana', 'Carlos', 'Fernanda', 'Lucas', 'Julia'];
    const name = names[Math.floor(Math.random() * names.length)];
    const prepType = Math.random() > 0.3 ? 'short' : 'long';
    
    try {
      const res = await fetch(`${API_URL}/orders`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customer_name: name,
          address_text: addr.text,
          lat: addr.lat + (Math.random() - 0.5) * 0.01, // Pequena variação
          lng: addr.lng + (Math.random() - 0.5) * 0.01,
          prep_type: prepType,
        }),
      });
      if (res.ok) {
        onOrderCreated();
      }
    } catch (err) {
      console.error('Erro ao criar pedido:', err);
    }
    setLoading(false);
  };
  
  const createMultipleOrders = async (count) => {
    setLoading(true);
    for (let i = 0; i < count; i++) {
      await createRandomOrder();
      await new Promise(r => setTimeout(r, 200));
    }
    setLoading(false);
  };
  
  return (
    <Card className="p-4 mb-6">
      <h3 className="font-semibold text-gray-700 mb-3 flex items-center gap-2">
        🧪 Simulador de Pedidos
      </h3>
      <div className="flex flex-wrap gap-2">
        <Button onClick={createRandomOrder} disabled={loading}>
          + 1 Pedido
        </Button>
        <Button onClick={() => createMultipleOrders(3)} disabled={loading} variant="secondary">
          + 3 Pedidos
        </Button>
        <Button onClick={() => createMultipleOrders(5)} disabled={loading} variant="secondary">
          + 5 Pedidos
        </Button>
      </div>
      <p className="text-xs text-gray-400 mt-2">
        Cria pedidos com endereços aleatórios na região de SP para teste
      </p>
    </Card>
  );
};

// ============ LISTA DE PEDIDOS ============

const OrdersList = ({ orders, onScan, onRefresh }) => {
  const pendingOrders = orders.filter(o => ['created', 'preparing'].includes(o.status));
  const readyOrders = orders.filter(o => o.status === 'ready');
  const inRouteOrders = orders.filter(o => ['assigned', 'picked_up'].includes(o.status));
  
  const handleScan = async (orderId) => {
    try {
      await fetch(`${API_URL}/orders/${orderId}/scan`, { method: 'POST' });
      onRefresh();
    } catch (err) {
      console.error('Erro ao bipar:', err);
    }
  };
  
  const OrderCard = ({ order, showScan = false }) => (
    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="font-medium text-gray-800">{order.customer_name}</span>
          <StatusBadge status={order.status} />
          {order.prep_type === 'long' && (
            <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded">Demorado</span>
          )}
        </div>
        <div className="text-sm text-gray-500 mt-1">{order.address_text}</div>
        {order.stop_order && (
          <div className="text-xs text-blue-600 mt-1">Parada #{order.stop_order}</div>
        )}
      </div>
      {showScan && (
        <Button onClick={() => handleScan(order.id)} variant="success" className="ml-2">
          📱 Bipar QR
        </Button>
      )}
    </div>
  );
  
  return (
    <div className="grid md:grid-cols-3 gap-4 mb-6">
      {/* Em preparo */}
      <Card className="p-4">
        <h3 className="font-semibold text-gray-700 mb-3 flex items-center gap-2">
          🍳 Em Preparo ({pendingOrders.length})
        </h3>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {pendingOrders.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-4">Nenhum pedido em preparo</p>
          ) : (
            pendingOrders.map(order => (
              <OrderCard key={order.id} order={order} showScan={true} />
            ))
          )}
        </div>
      </Card>
      
      {/* Prontos */}
      <Card className="p-4 border-2 border-green-200">
        <h3 className="font-semibold text-green-700 mb-3 flex items-center gap-2">
          ✅ Prontos para Despacho ({readyOrders.length})
        </h3>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {readyOrders.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-4">Nenhum pedido pronto</p>
          ) : (
            readyOrders.map(order => (
              <OrderCard key={order.id} order={order} />
            ))
          )}
        </div>
      </Card>
      
      {/* Em rota */}
      <Card className="p-4">
        <h3 className="font-semibold text-blue-700 mb-3 flex items-center gap-2">
          🏍️ Em Rota ({inRouteOrders.length})
        </h3>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {inRouteOrders.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-4">Nenhum pedido em rota</p>
          ) : (
            inRouteOrders.map(order => (
              <OrderCard key={order.id} order={order} />
            ))
          )}
        </div>
      </Card>
    </div>
  );
};

// ============ PAINEL DE MOTOQUEIROS ============

const CouriersPanel = ({ couriers, onRefresh }) => {
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState('');
  
  const createCourier = async () => {
    if (!newName.trim()) return;
    setCreating(true);
    try {
      await fetch(`${API_URL}/couriers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newName }),
      });
      setNewName('');
      onRefresh();
    } catch (err) {
      console.error('Erro ao criar motoboy:', err);
    }
    setCreating(false);
  };
  
  const toggleStatus = async (courier) => {
    const endpoint = courier.status === 'available' 
      ? `${API_URL}/couriers/${courier.id}/offline`
      : `${API_URL}/couriers/${courier.id}/available`;
    
    try {
      await fetch(endpoint, { method: 'POST' });
      onRefresh();
    } catch (err) {
      console.error('Erro ao mudar status:', err);
    }
  };
  
  const completeBatch = async (courierId) => {
    try {
      await fetch(`${API_URL}/couriers/${courierId}/complete-batch`, { method: 'POST' });
      onRefresh();
    } catch (err) {
      console.error('Erro ao completar lote:', err);
    }
  };
  
  return (
    <Card className="p-4 mb-6">
      <h3 className="font-semibold text-gray-700 mb-3 flex items-center gap-2">
        🏍️ Motoqueiros ({couriers.length})
      </h3>
      
      {/* Criar novo */}
      <div className="flex gap-2 mb-4">
        <input
          type="text"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          placeholder="Nome do motoboy..."
          className="flex-1 px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
          onKeyPress={(e) => e.key === 'Enter' && createCourier()}
        />
        <Button onClick={createCourier} disabled={creating || !newName.trim()}>
          Adicionar
        </Button>
      </div>
      
      {/* Lista */}
      <div className="space-y-2">
        {couriers.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-4">
            Nenhum motoboy cadastrado. Adicione alguns para testar!
          </p>
        ) : (
          couriers.map(courier => (
            <div key={courier.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-orange-100 rounded-full flex items-center justify-center text-orange-600 font-bold">
                  {courier.name.charAt(0).toUpperCase()}
                </div>
                <div>
                  <div className="font-medium text-gray-800">{courier.name}</div>
                  <StatusBadge status={courier.status} />
                </div>
              </div>
              <div className="flex gap-2">
                {courier.status === 'busy' && (
                  <Button onClick={() => completeBatch(courier.id)} variant="success" className="text-sm">
                    ✓ Finalizar
                  </Button>
                )}
                <Button 
                  onClick={() => toggleStatus(courier)} 
                  variant="secondary"
                  className="text-sm"
                  disabled={courier.status === 'busy'}
                >
                  {courier.status === 'available' ? 'Pausar' : 'Ativar'}
                </Button>
              </div>
            </div>
          ))
        )}
      </div>
    </Card>
  );
};

// ============ CONTROLE DE DISPATCH ============

const DispatchControl = ({ onDispatch, stats }) => {
  const [loading, setLoading] = useState(false);
  const [lastResult, setLastResult] = useState(null);
  
  const runDispatch = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/dispatch/run`, { method: 'POST' });
      const result = await res.json();
      setLastResult(result);
      onDispatch();
    } catch (err) {
      console.error('Erro no dispatch:', err);
      setLastResult({ message: 'Erro ao executar dispatch' });
    }
    setLoading(false);
  };
  
  const canDispatch = stats && stats.orders?.ready > 0 && stats.couriers?.available > 0;
  
  return (
    <Card className="p-4 mb-6 border-2 border-orange-200 bg-orange-50">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-orange-700 flex items-center gap-2">
            🚀 Dispatch - Distribuir Pedidos
          </h3>
          <p className="text-sm text-orange-600 mt-1">
            {stats?.orders?.ready || 0} pedido(s) pronto(s) · {stats?.couriers?.available || 0} motoboy(s) disponível(is)
          </p>
        </div>
        <Button 
          onClick={runDispatch} 
          disabled={loading || !canDispatch}
          className="text-lg px-6 py-3"
        >
          {loading ? '⏳ Processando...' : '🚀 Executar Dispatch'}
        </Button>
      </div>
      
      {lastResult && (
        <div className={`mt-3 p-3 rounded-lg ${lastResult.batches_created > 0 ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
          {lastResult.message}
        </div>
      )}
    </Card>
  );
};

// ============ LOTES ATIVOS ============

const ActiveBatches = ({ batches }) => {
  if (!batches || batches.length === 0) return null;
  
  return (
    <Card className="p-4 mb-6">
      <h3 className="font-semibold text-gray-700 mb-3 flex items-center gap-2">
        📦 Lotes Ativos ({batches.length})
      </h3>
      <div className="space-y-3">
        {batches.map(batch => (
          <div key={batch.id} className="p-3 bg-blue-50 rounded-lg border border-blue-200">
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium text-blue-800">
                🏍️ {batch.courier_name}
              </span>
              <StatusBadge status={batch.status} />
            </div>
            <div className="space-y-1">
              {batch.orders.map((order, idx) => (
                <div key={order.id} className="text-sm text-gray-600 flex items-center gap-2">
                  <span className="w-5 h-5 bg-blue-200 rounded-full flex items-center justify-center text-xs font-bold text-blue-700">
                    {idx + 1}
                  </span>
                  {order.customer_name} - {order.address_text.split(' - ')[0]}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
};

// ============ APP PRINCIPAL ============

export default function MotoFlashApp() {
  const [orders, setOrders] = useState([]);
  const [couriers, setCouriers] = useState([]);
  const [batches, setBatches] = useState([]);
  const [stats, setStats] = useState(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState(null);
  
  const fetchAll = useCallback(async () => {
    try {
      const [ordersRes, couriersRes, batchesRes, statsRes] = await Promise.all([
        fetch(`${API_URL}/orders?limit=50`),
        fetch(`${API_URL}/couriers`),
        fetch(`${API_URL}/dispatch/batches`),
        fetch(`${API_URL}/dispatch/stats`),
      ]);
      
      if (ordersRes.ok) setOrders(await ordersRes.json());
      if (couriersRes.ok) setCouriers(await couriersRes.json());
      if (batchesRes.ok) setBatches(await batchesRes.json());
      if (statsRes.ok) setStats(await statsRes.json());
      
      setConnected(true);
      setError(null);
    } catch (err) {
      setConnected(false);
      setError('Não foi possível conectar ao servidor. Verifique se o backend está rodando.');
    }
  }, []);
  
  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 5000); // Atualiza a cada 5s
    return () => clearInterval(interval);
  }, [fetchAll]);
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-amber-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-orange-100">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-orange-500 rounded-xl flex items-center justify-center">
                <span className="text-white text-xl">🏍️</span>
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-800">MotoFlash</h1>
                <p className="text-xs text-gray-500">Despacho Inteligente v0.1</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
              <span className="text-sm text-gray-500">
                {connected ? 'Conectado' : 'Desconectado'}
              </span>
            </div>
          </div>
        </div>
      </header>
      
      {/* Main */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {error && (
          <div className="mb-6 p-4 bg-red-100 border border-red-200 rounded-lg text-red-700">
            <p className="font-medium">⚠️ Erro de conexão</p>
            <p className="text-sm mt-1">{error}</p>
            <p className="text-sm mt-2">
              Execute o backend com: <code className="bg-red-200 px-2 py-0.5 rounded">cd backend && uvicorn main:app --reload</code>
            </p>
          </div>
        )}
        
        {/* Stats */}
        <StatsPanel stats={stats} />
        
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Coluna principal */}
          <div className="lg:col-span-2">
            {/* Simulador */}
            <OrderSimulator onOrderCreated={fetchAll} />
            
            {/* Dispatch */}
            <DispatchControl onDispatch={fetchAll} stats={stats} />
            
            {/* Pedidos */}
            <OrdersList orders={orders} onRefresh={fetchAll} />
          </div>
          
          {/* Coluna lateral */}
          <div>
            {/* Motoqueiros */}
            <CouriersPanel couriers={couriers} onRefresh={fetchAll} />
            
            {/* Lotes ativos */}
            <ActiveBatches batches={batches} />
          </div>
        </div>
      </main>
      
      {/* Footer */}
      <footer className="text-center py-4 text-sm text-gray-400">
        MotoFlash MVP v0.1 - Sistema de Despacho Inteligente
      </footer>
    </div>
  );
}
