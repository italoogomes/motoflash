function MotoFlashApp() {
    const [currentPage, setCurrentPage] = useState('inicio');
    const [sidebarOpen, setSidebarOpen] = useState(false);
    
    // Dados
    const [orders, setOrders] = useState([]);
    const [couriers, setCouriers] = useState([]);
    const [batches, setBatches] = useState([]);
    const [stats, setStats] = useState(null);
    const [alerts, setAlerts] = useState(null);
    const [recommendation, setRecommendation] = useState(null);
    const [connected, setConnected] = useState(false);
    
    // Restaurante
    const [restaurantName, setRestaurantName] = useState(() => {
        const data = sessionStorage.getItem('motoflash_restaurant');
        if (data) {
            try {
                return JSON.parse(data).name || 'Restaurante';
            } catch { return 'Restaurante'; }
        }
        return 'Restaurante';
    });

    // Data simulada
    const [simulatedDate, setSimulatedDate] = useState(() => {
        return new Date().toISOString().split('T')[0];
    });

    const handleLogout = () => {
        sessionStorage.removeItem('motoflash_token');
        sessionStorage.removeItem('motoflash_user');
        sessionStorage.removeItem('motoflash_restaurant');
        window.location.href = '/login';
    };
    
    const fetchAll = useCallback(async () => {
        try {
            const [ordersRes, couriersRes, batchesRes, statsRes, alertsRes, recoRes] = await Promise.all([
                authFetch(`${API_URL}/orders?limit=50`),
                authFetch(`${API_URL}/couriers`),
                authFetch(`${API_URL}/dispatch/batches`),
                authFetch(`${API_URL}/dispatch/stats`),
                authFetch(`${API_URL}/dispatch/alerts`),
                authFetch(`${API_URL}/dispatch/recommendation`),
            ]);
            
            if (ordersRes.ok) setOrders(await ordersRes.json());
            if (couriersRes.ok) setCouriers(await couriersRes.json());
            if (batchesRes.ok) setBatches(await batchesRes.json());
            if (statsRes.ok) setStats(await statsRes.json());
            if (alertsRes.ok) setAlerts(await alertsRes.json());
            if (recoRes.ok) setRecommendation(await recoRes.json());
            
            setConnected(true);
        } catch (err) {
            if (err.message !== 'Não autenticado' && err.message !== 'Sessão expirada') {
                setConnected(false);
            }
        }
    }, []);
    
    useEffect(() => {
        fetchAll();
        const interval = setInterval(fetchAll, 5000);
        return () => clearInterval(interval);
    }, [fetchAll]);
    
    const getPageTitle = () => {
        const titles = {
            inicio: 'Dashboard',
            pedidos: 'Pedidos',
            motoboys: 'Motoqueiros',
            cardapio: 'Cardápio',
            clientes: 'Clientes',
            relatorios: 'Relatórios',
            configuracoes: 'Configurações',
            ajuda: 'Ajuda',
        };
        return titles[currentPage] || 'Dashboard';
    };
    
    const renderPage = () => {
        switch (currentPage) {
            case 'inicio':
                return (
                    <DashboardPage 
                        stats={stats}
                        alerts={alerts}
                        recommendation={recommendation}
                        orders={orders}
                        couriers={couriers}
                        batches={batches}
                        fetchAll={fetchAll}
                        simulatedDate={simulatedDate}
                    />
                );
            case 'pedidos':
                return <PlaceholderPage title="Pedidos" icon="📦" />;
            case 'motoboys':
                return <PlaceholderPage title="Motoqueiros" icon="🏍️" />;
            case 'cardapio':
                return <CardapioPage />;
            case 'clientes':
                return <ClientesPage />;
            case 'relatorios':
                return <PlaceholderPage title="Relatórios" icon="📊" />;
            case 'configuracoes':
                return <PlaceholderPage title="Configurações" icon="⚙️" />;
            case 'ajuda':
                return <PlaceholderPage title="Ajuda" icon="❓" />;
            default:
                return <DashboardPage {...{ stats, alerts, recommendation, orders, couriers, batches, fetchAll, simulatedDate }} />;
        }
    };
    
    return (
        <>
            <Sidebar 
                currentPage={currentPage}
                setCurrentPage={setCurrentPage}
                restaurantName={restaurantName}
                onLogout={handleLogout}
                stats={stats}
                sidebarOpen={sidebarOpen}
                setSidebarOpen={setSidebarOpen}
            />
            
            <div className="main-wrapper">
                {/* Header */}
                <header className="glass-header">
                    <div className="px-6 py-4">
                        <div className="flex items-center justify-between">
                            {/* Mobile menu */}
                            <button 
                                className="mobile-menu-btn"
                                onClick={() => setSidebarOpen(!sidebarOpen)}
                            >
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M3 12h18M3 6h18M3 18h18"/>
                                </svg>
                            </button>
                            
                            {/* Title */}
                            <div>
                                <h1 className="text-xl font-bold text-white" style={{ fontFamily: 'Outfit, sans-serif' }}>
                                    {getPageTitle()}
                                </h1>
                                <p className="text-sm" style={{ color: 'rgba(255,255,255,0.5)' }}>
                                    Visão geral das operações
                                </p>
                            </div>
                            
                            {/* Right side */}
                            <div className="flex items-center gap-4">
                                {/* Data simulada */}
                                <div className="hidden md:flex items-center gap-2 px-3 py-2 rounded-lg" style={{ background: 'rgba(255,107,0,0.15)', border: '1px solid rgba(255,107,0,0.3)' }}>
                                    <span style={{ color: '#ff8c42' }}>📅</span>
                                    <input
                                        type="date"
                                        value={simulatedDate}
                                        onChange={(e) => setSimulatedDate(e.target.value)}
                                        className="bg-transparent border-none text-white text-sm focus:outline-none"
                                        style={{ colorScheme: 'dark' }}
                                    />
                                </div>
                                
                                {/* Status */}
                                <div className="flex items-center gap-2">
                                    <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
                                    <span className="text-sm" style={{ color: 'rgba(255,255,255,0.5)' }}>
                                        {connected ? 'Online' : 'Offline'}
                                    </span>
                                </div>
                                
                                {/* Notificações */}
                                <button className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: 'rgba(255,255,255,0.08)' }}>
                                    🔔
                                </button>
                            </div>
                        </div>
                    </div>
                </header>
                
                {/* Main Content */}
                <main className="p-6">
                    {renderPage()}
                </main>
                
                {/* Footer */}
                <footer className="text-center py-6" style={{ color: 'rgba(255,255,255,0.25)' }}>
                    MotoFlash MVP v0.4 - Sistema de Despacho Inteligente
                </footer>
            </div>
        </>
    );
}

ReactDOM.createRoot(document.getElementById('root')).render(<MotoFlashApp />);
