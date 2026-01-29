
// ============ COMPONENTES AUXILIARES ============

// Cronômetro
const Timer = ({ startTime }) => {
    const [elapsed, setElapsed] = useState(0);
    
    useEffect(() => {
        if (!startTime) return;
        
        let dateString = startTime;
        if (!dateString.endsWith('Z') && !dateString.includes('+')) {
            dateString = dateString + 'Z';
        }
        
        const start = new Date(dateString).getTime();
        
        const updateTimer = () => {
            const now = Date.now();
            const diff = Math.floor((now - start) / 1000);
            setElapsed(Math.max(0, diff));
        };
        
        updateTimer();
        const interval = setInterval(updateTimer, 1000);
        
        return () => clearInterval(interval);
    }, [startTime]);
    
    const minutes = Math.floor(elapsed / 60);
    const seconds = elapsed % 60;

    // Limita a 99:59 para evitar mostrar tempos absurdos com datas simuladas
    const displayMinutes = Math.min(minutes, 99);
    const isOverLimit = minutes >= 100;

    let colorClass = 'badge-success';
    if (minutes >= 15) colorClass = 'badge-warning';
    if (minutes >= 25) colorClass = 'badge-danger';

    return (
        <span className={`badge ${colorClass} font-mono`}>
            ⏱️ {String(displayMinutes).padStart(2, '0')}:{String(seconds).padStart(2, '0')}{isOverLimit ? '+' : ''}
        </span>
    );
};

// Badge de Status
const StatusBadge = ({ status }) => {
    const config = {
        created: { class: 'badge-gray', label: 'Criado' },
        preparing: { class: 'badge-warning', label: 'Preparando' },
        ready: { class: 'badge-success', label: 'Pronto' },
        assigned: { class: 'badge-info', label: 'Atribuído' },
        picked_up: { class: 'badge-purple', label: 'Coletado' },
        delivered: { class: 'badge-success', label: 'Entregue' },
        available: { class: 'badge-success', label: 'Disponível' },
        busy: { class: 'badge-warning', label: 'Em entrega' },
        offline: { class: 'badge-gray', label: 'Offline' },
    };
    
    const { class: badgeClass, label } = config[status] || { class: 'badge-gray', label: status };
    
    return <span className={`badge ${badgeClass}`}>{label}</span>;
};

// ============ COMPONENTE: STATS PANEL ============

const StatsPanel = ({ stats }) => {
    if (!stats) return null;
    
    const items = [
        { value: stats.orders?.ready || 0, label: 'Prontos', color: '#ff8c42' },
        { value: stats.orders?.assigned || 0, label: 'Em Rota', color: '#60a5fa' },
        { value: stats.couriers?.available || 0, label: 'Motoboys Livres', color: '#4ade80' },
        { value: stats.couriers?.busy || 0, label: 'Ocupados', color: '#a78bfa' },
        { value: stats.orders?.delivered || 0, label: 'Entregues Hoje', color: '#34d399' },
    ];
    
    return (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
            {items.map((item, idx) => (
                <div key={idx} className="stat-card">
                    <div className="stat-value" style={{ color: item.color }}>{item.value}</div>
                    <div className="stat-label">{item.label}</div>
                </div>
            ))}
        </div>
    );
};

// ============ COMPONENTE: ALERTS PANEL ============

const AlertsPanel = ({ alerts, recommendation }) => {
    if (!alerts) return null;
    
    const statusBgColors = {
        critico: '#ef4444',
        atencao: '#fbbf24',
        info: '#60a5fa',
        sucesso: '#4ade80',
    };
    
    return (
        <div className="glass-card p-5 mb-6">
            <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-white flex items-center gap-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
                    🧠 Inteligência MotoFlash
                </h3>
                {recommendation && (
                    <div className="flex items-center gap-2 text-sm">
                        <span style={{ color: 'rgba(255,255,255,0.5)' }}>Motoboys recomendados:</span>
                        <span
                            className="px-3 py-1 rounded-full font-bold text-white"
                            style={{ background: recommendation.motoboys_recomendados != null ? (statusBgColors[alerts.status_geral] || '#60a5fa') : 'rgba(255,255,255,0.2)' }}
                        >
                            {recommendation.motoboys_recomendados != null ? recommendation.motoboys_recomendados : '-'}
                        </span>
                    </div>
                )}
            </div>
            
            {/* Alertas */}
            <div className="space-y-2 mb-4">
                {alerts.alertas?.map((alerta, idx) => (
                    <div key={idx} className={`alert-item alert-${alerta.tipo}`}>
                        <div className="flex items-start gap-3">
                            <span className="text-xl">{alerta.icone}</span>
                            <div className="flex-1">
                                <div className="font-semibold text-white">{alerta.titulo}</div>
                                <div className="text-sm" style={{ color: 'rgba(255,255,255,0.7)' }}>{alerta.mensagem}</div>
                                {alerta.acao_sugerida && (
                                    <div className="text-sm mt-1 font-medium" style={{ color: '#fbbf24' }}>
                                        💡 {alerta.acao_sugerida}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                ))}
            </div>
            
            {/* Métricas */}
            {recommendation && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4" style={{ borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                    <div className="text-center">
                        <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: '12px' }}>Tempo preparo</div>
                        <div className="font-semibold text-white">
                            {recommendation.tempo_medio_preparo ? `${recommendation.tempo_medio_preparo} min` : '-'}
                        </div>
                    </div>
                    <div className="text-center">
                        <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: '12px' }}>Tempo rota</div>
                        <div className="font-semibold text-white">
                            {recommendation.tempo_medio_rota ? `${recommendation.tempo_medio_rota} min` : '-'}
                        </div>
                    </div>
                    <div className="text-center">
                        <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: '12px' }}>Pedidos/hora</div>
                        <div className="font-semibold text-white">{recommendation.pedidos_por_hora || '-'}</div>
                    </div>
                    <div className="text-center">
                        <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: '12px' }}>Capacidade/motoboy</div>
                        <div className="font-semibold text-white">
                            {recommendation.capacidade_por_motoboy ? `${recommendation.capacidade_por_motoboy}/h` : '-'}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

// ============ COMPONENTE: FORMULÁRIO DE NOVO PEDIDO ============

const NewOrderForm = ({ onOrderCreated, simulatedDate }) => {
    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState('');
    const [errorMsg, setErrorMsg] = useState('');
    
    // Campos do formulário
    const [phone, setPhone] = useState('');
    const [customerName, setCustomerName] = useState('');
    const [selectedItemId, setSelectedItemId] = useState('');
    
    // Campos de endereço
    const [cep, setCep] = useState('');
    const [street, setStreet] = useState('');
    const [number, setNumber] = useState('');
    const [neighborhood, setNeighborhood] = useState('');
    const [city, setCity] = useState('Ribeirão Preto');
    const [complement, setComplement] = useState('');
    const [loadingCep, setLoadingCep] = useState(false);
    
    // Cliente encontrado
    const [foundCustomer, setFoundCustomer] = useState(null);
    const [searchingCustomer, setSearchingCustomer] = useState(false);
    const [useOtherAddress, setUseOtherAddress] = useState(false);
    
    // Sugestões
    const [nameSuggestions, setNameSuggestions] = useState([]);
    const [showNameSuggestions, setShowNameSuggestions] = useState(false);
    
    // Autocomplete de endereço (Photon)
    const [streetSuggestions, setStreetSuggestions] = useState([]);
    const [showStreetSuggestions, setShowStreetSuggestions] = useState(false);
    const [neighborhoodSuggestions, setNeighborhoodSuggestions] = useState([]);
    const [showNeighborhoodSuggestions, setShowNeighborhoodSuggestions] = useState(false);
    
    // Cardápio
    const [menuData, setMenuData] = useState([]);
    const [loadingMenu, setLoadingMenu] = useState(true);
    
    // Formata telefone
    const formatPhone = (value) => {
        const numbers = value.replace(/\D/g, '');
        if (numbers.length <= 2) return `(${numbers}`;
        if (numbers.length <= 7) return `(${numbers.slice(0,2)}) ${numbers.slice(2)}`;
        return `(${numbers.slice(0,2)}) ${numbers.slice(2,7)}-${numbers.slice(7,11)}`;
    };
    
    // Formata CEP
    const formatCep = (value) => {
        const numbers = value.replace(/\D/g, '');
        if (numbers.length <= 5) return numbers;
        return `${numbers.slice(0,5)}-${numbers.slice(5,8)}`;
    };
    
    // Busca CEP
    const handleCepChange = async (e) => {
        const formatted = formatCep(e.target.value);
        setCep(formatted);
        
        const numbers = formatted.replace(/\D/g, '');
        
        if (numbers.length === 8) {
            setLoadingCep(true);
            try {
                const res = await fetch(`https://viacep.com.br/ws/${numbers}/json/`);
                if (res.ok) {
                    const data = await res.json();
                    if (!data.erro) {
                        setStreet(data.logradouro || '');
                        setNeighborhood(data.bairro || '');
                        setCity(data.localidade || '');
                        setTimeout(() => document.getElementById('numberInput')?.focus(), 100);
                    }
                }
            } catch (err) {
                console.error('Erro ViaCEP:', err);
            }
            setLoadingCep(false);
        }
    };
    
    // Remove acentos para API Photon
    const removeAccents = (str) => str.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    
    // Busca sugestões no Photon
    const searchPhoton = async (query, type) => {
        if (query.trim().length < 3) return [];
        
        try {
            const cleanQuery = removeAccents(query);
            const fullQuery = `${cleanQuery} ${removeAccents(city || 'Ribeirao Preto')}`;
            
            const res = await fetch(
                `https://photon.komoot.io/api/?q=${encodeURIComponent(fullQuery)}&limit=5&lat=-21.17&lon=-47.80`
            );
            
            if (res.ok) {
                const data = await res.json();
                if (data.features && data.features.length > 0) {
                    const values = new Set();
                    data.features.forEach(f => {
                        const p = f.properties;
                        if (type === 'street') {
                            const name = p.name || p.street;
                            if (name) values.add(name);
                        } else if (type === 'neighborhood') {
                            const bairro = p.suburb || p.district || p.locality || p.neighbourhood;
                            if (bairro && bairro !== p.city) values.add(bairro);
                        }
                    });
                    return Array.from(values);
                }
            }
        } catch (err) {
            console.error('Erro Photon:', err);
        }
        return [];
    };
    
    // Autocomplete de Rua
    const handleStreetChange = async (e) => {
        const value = e.target.value;
        setStreet(value);
        
        const suggestions = await searchPhoton(value, 'street');
        setStreetSuggestions(suggestions);
        setShowStreetSuggestions(suggestions.length > 0);
    };
    
    // Autocomplete de Bairro
    const handleNeighborhoodChange = async (e) => {
        const value = e.target.value;
        setNeighborhood(value);
        
        const suggestions = await searchPhoton(value, 'neighborhood');
        setNeighborhoodSuggestions(suggestions);
        setShowNeighborhoodSuggestions(suggestions.length > 0);
    };
    
    // Busca cliente por telefone
    const handlePhoneChange = async (e) => {
        const formatted = formatPhone(e.target.value);
        setPhone(formatted);
        
        const numbers = formatted.replace(/\D/g, '');
        
        if (numbers.length >= 10) {
            setSearchingCustomer(true);
            try {
                const res = await authFetch(`${API_URL}/customers/phone/${numbers}`);
                if (res.ok) {
                    const customer = await res.json();
                    selectCustomer(customer);
                    setStatus('✅ Cliente encontrado!');
                    setTimeout(() => setStatus(''), 2000);
                } else {
                    setFoundCustomer(null);
                    setUseOtherAddress(false);
                }
            } catch (err) {
                setFoundCustomer(null);
            }
            setSearchingCustomer(false);
        } else {
            setFoundCustomer(null);
            setUseOtherAddress(false);
        }
    };
    
    // Busca clientes por nome
    const handleNameChange = async (e) => {
        const value = e.target.value;
        setCustomerName(value);
        setFoundCustomer(null);
        
        if (value.trim().length >= 2) {
            try {
                const res = await authFetch(`${API_URL}/customers?search=${encodeURIComponent(value)}`);
                if (res.ok) {
                    const customers = await res.json();
                    setNameSuggestions(customers.slice(0, 5));
                    setShowNameSuggestions(customers.length > 0);
                }
            } catch (err) {
                setNameSuggestions([]);
            }
        } else {
            setNameSuggestions([]);
            setShowNameSuggestions(false);
        }
    };
    
    // Seleciona cliente
    const selectCustomer = (customer) => {
        setFoundCustomer(customer);
        setCustomerName(customer.name);
        setPhone(formatPhone(customer.phone));
        setComplement(customer.complement || '');
        setNameSuggestions([]);
        setShowNameSuggestions(false);
        setUseOtherAddress(false);
        
        if (customer.address) {
            parseAddress(customer.address);
        }
    };
    
    // Parseia endereço
    const parseAddress = (fullAddress) => {
        const dashParts = fullAddress.split(' - ');
        
        if (dashParts.length >= 2) {
            const ruaENumero = dashParts[0];
            const bairroECidade = dashParts.slice(1).join(' - ');
            
            const ruaParts = ruaENumero.split(',').map(p => p.trim());
            if (ruaParts.length >= 2) {
                setStreet(ruaParts[0]);
                setNumber(ruaParts[1]);
            } else {
                setStreet(ruaParts[0]);
            }
            
            const bairroParts = bairroECidade.split(',').map(p => p.trim());
            if (bairroParts.length >= 2) {
                setNeighborhood(bairroParts[0]);
                setCity(bairroParts[1]);
            } else if (bairroParts.length === 1) {
                setNeighborhood(bairroParts[0]);
            }
        } else {
            const parts = fullAddress.split(',').map(p => p.trim());
            if (parts.length >= 1) setStreet(parts[0]);
            if (parts.length >= 2) setNumber(parts[1]);
            if (parts.length >= 3) setNeighborhood(parts[2]);
            if (parts.length >= 4) setCity(parts[3]);
        }
    };
    
    // Monta endereço completo
    const getFullAddress = () => {
        let addr = street;
        if (number) addr += `, ${number}`;
        if (neighborhood) addr += ` - ${neighborhood}`;
        if (city) addr += `, ${city}`;
        return addr;
    };
    
    // Outro endereço
    const handleUseOtherAddress = () => {
        setUseOtherAddress(true);
        setCep('');
        setStreet('');
        setNumber('');
        setNeighborhood('');
        setCity('Ribeirão Preto');
        setComplement('');
    };
    
    const handleUseCadastroAddress = () => {
        setUseOtherAddress(false);
        if (foundCustomer?.address) {
            parseAddress(foundCustomer.address);
        }
        setComplement(foundCustomer?.complement || '');
    };
    
    // Busca cardápio
    useEffect(() => {
        const fetchMenu = async () => {
            try {
                const res = await authFetch(`${API_URL}/menu/full`);
                if (res.ok) {
                    const data = await res.json();
                    setMenuData(data);
                    setSelectedItemId('');
                }
            } catch (err) {
                console.error('Erro ao buscar cardápio:', err);
            }
            setLoadingMenu(false);
        };
        fetchMenu();
    }, []);
    
    const getSelectedItem = () => {
        for (const cat of menuData) {
            const item = cat.items.find(i => i.id === selectedItemId);
            if (item) return { ...item, categoryName: cat.name };
        }
        return null;
    };
    
    // Cria pedido
    const createOrder = async (e) => {
        e.preventDefault();
        
        if (!customerName.trim()) { setErrorMsg('Digite o nome do cliente'); return; }
        if (!selectedItemId) { setErrorMsg('Selecione um item do cardápio'); return; }
        if (!street.trim()) { setErrorMsg('Digite a rua'); return; }
        if (!number.trim()) { setErrorMsg('Digite o número'); return; }
        if (!city.trim()) { setErrorMsg('Digite a cidade'); return; }
        
        const fullAddress = getFullAddress();
        const selectedItem = getSelectedItem();
        
        setLoading(true);
        setErrorMsg('');
        setStatus('🔍 Buscando coordenadas...');
        
        try {
            // Se é cliente novo, salva primeiro
            if (!foundCustomer && phone.replace(/\D/g, '').length >= 10) {
                try {
                    await authFetch(`${API_URL}/customers`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            phone: phone.replace(/\D/g, ''),
                            name: customerName.trim(),
                            address: fullAddress,
                            complement: complement.trim() || null
                        })
                    });
                } catch (err) { }
            }
            
            // Cria pedido
            const res = await authFetch(`${API_URL}/orders`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    customer_name: customerName.trim(),
                    address_text: fullAddress + (complement ? ` - ${complement}` : ''),
                    item: selectedItem ? selectedItem.name : 'Pedido',
                    prep_type: 'short',
                    simulated_date: simulatedDate,
                }),
            });
            
            if (!res.ok) {
                const error = await res.json();
                throw new Error(error.detail || 'Erro ao criar pedido');
            }

            const newOrder = await res.json();

            // Mensagem de sucesso com short_id e tracking_code
            const orderInfo = newOrder.short_id ? `#${newOrder.short_id}` : '';
            const trackingInfo = newOrder.tracking_code ? ` | Rastreio: ${newOrder.tracking_code}` : '';
            setStatus(`✅ Pedido criado com sucesso! ${orderInfo}${trackingInfo}`);
            // Limpa formulário
            setPhone('');
            setCustomerName('');
            setCep('');
            setStreet('');
            setNumber('');
            setNeighborhood('');
            setCity('Ribeirão Preto');
            setComplement('');
            setFoundCustomer(null);
            setUseOtherAddress(false);
            setSelectedItemId('');
            onOrderCreated();
            
            setTimeout(() => setStatus(''), 3000);
            
        } catch (err) {
            console.error('Erro:', err);
            setErrorMsg(`❌ ${err.message}`);
        }
        
        setLoading(false);
    };
    
    const hasMenuItems = menuData.some(cat => cat.items.length > 0);
    const showAddressFields = !foundCustomer || useOtherAddress;
    
    return (
        <div className="glass-card p-5 mb-6">
            <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-white flex items-center gap-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
                    📦 Novo Pedido
                </h3>
                <span className="badge badge-success">Google Maps</span>
            </div>
            
            <form onSubmit={createOrder}>
                <div className="grid md:grid-cols-2 gap-4 mb-4">
                    {/* Telefone */}
                    <div>
                        <label className="block text-sm mb-2" style={{ color: 'rgba(255,255,255,0.6)' }}>
                            Telefone do Cliente
                            {searchingCustomer && <span className="ml-2" style={{ color: '#ff8c42' }}>🔍 Buscando...</span>}
                        </label>
                        <input
                            type="tel"
                            value={phone}
                            onChange={handlePhoneChange}
                            placeholder="(16) 99999-1234"
                            className="glass-input"
                            maxLength={15}
                            disabled={loading}
                        />
                    </div>
                    
                    {/* Nome */}
                    <div className="relative">
                        <label className="block text-sm mb-2" style={{ color: 'rgba(255,255,255,0.6)' }}>
                            Nome do Cliente
                        </label>
                        {foundCustomer && !useOtherAddress ? (
                            <div className="customer-found-card">
                                <div className="flex items-center gap-3">
                                    <span className="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold" style={{ background: '#22c55e' }}>
                                        {foundCustomer.name.charAt(0).toUpperCase()}
                                    </span>
                                    <div className="flex-1">
                                        <div className="font-semibold text-white">{foundCustomer.name}</div>
                                        <div className="text-sm" style={{ color: 'rgba(255,255,255,0.6)' }}>
                                            📍 {foundCustomer.address}
                                        </div>
                                    </div>
                                </div>
                                <button
                                    type="button"
                                    onClick={handleUseOtherAddress}
                                    className="mt-3 w-full py-2 text-sm rounded-lg transition-colors"
                                    style={{ background: 'rgba(255,107,0,0.2)', color: '#ff8c42' }}
                                >
                                    📍 Entregar em outro endereço
                                </button>
                            </div>
                        ) : (
                            <>
                                <input
                                    type="text"
                                    value={customerName}
                                    onChange={handleNameChange}
                                    onBlur={() => setTimeout(() => setShowNameSuggestions(false), 200)}
                                    onFocus={() => nameSuggestions.length > 0 && setShowNameSuggestions(true)}
                                    placeholder="Digite o nome..."
                                    className="glass-input"
                                    disabled={loading}
                                    autoComplete="off"
                                />
                                
                                {showNameSuggestions && nameSuggestions.length > 0 && (
                                    <div className="autocomplete-dropdown">
                                        {nameSuggestions.map(customer => (
                                            <div
                                                key={customer.id}
                                                onClick={() => selectCustomer(customer)}
                                                className="autocomplete-item flex items-center gap-3"
                                            >
                                                <span className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold" style={{ background: 'rgba(255,107,0,0.2)', color: '#ff8c42' }}>
                                                    {customer.name.charAt(0).toUpperCase()}
                                                </span>
                                                <div>
                                                    <div className="font-medium text-white">{customer.name}</div>
                                                    <div className="text-xs" style={{ color: 'rgba(255,255,255,0.5)' }}>📞 {customer.phone}</div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                                
                                {/* Mensagem cliente novo */}
                                {!foundCustomer && phone.replace(/\D/g, '').length >= 10 && (
                                    <p className="text-xs mt-2" style={{ color: '#60a5fa' }}>
                                        📝 Cliente novo - será cadastrado automaticamente
                                    </p>
                                )}
                            </>
                        )}
                    </div>
                </div>
                
                {/* Alerta outro endereço */}
                {foundCustomer && useOtherAddress && (
                    <div className="mb-4 p-3 rounded-lg" style={{ background: 'rgba(251,191,36,0.15)', border: '1px solid rgba(251,191,36,0.3)' }}>
                        <div className="flex items-center justify-between">
                            <span style={{ color: '#fbbf24' }}>⚠️ Entrega em endereço diferente do cadastro</span>
                            <button
                                type="button"
                                onClick={handleUseCadastroAddress}
                                className="text-sm"
                                style={{ color: '#60a5fa' }}
                            >
                                ↩️ Usar endereço do cadastro
                            </button>
                        </div>
                    </div>
                )}
                
                <div className="grid md:grid-cols-2 gap-4 mb-4">
                    {/* Item */}
                    <div>
                        <label className="block text-sm mb-2" style={{ color: 'rgba(255,255,255,0.6)' }}>Item</label>
                        {!hasMenuItems ? (
                            <div className="p-3 rounded-lg" style={{ background: 'rgba(251,191,36,0.15)', border: '1px solid rgba(251,191,36,0.3)' }}>
                                <span style={{ color: '#fbbf24' }}>⚠️ Nenhum item. </span>
                                <button onClick={() => setCurrentPage('cardapio')} style={{ color: '#60a5fa', background: 'none', border: 'none', cursor: 'pointer', textDecoration: 'underline' }}>Cadastrar cardápio</button>
                            </div>
                        ) : (
                            <select
                                value={selectedItemId}
                                onChange={(e) => setSelectedItemId(e.target.value)}
                                className="glass-select"
                                disabled={loading}
                            >
                                <option value="">Selecione um item...</option>
                                {menuData.map(cat => (
                                    <optgroup key={cat.id} label={cat.name}>
                                        {cat.items.map(item => (
                                            <option key={item.id} value={item.id}>
                                                {item.name}
                                            </option>
                                        ))}
                                    </optgroup>
                                ))}
                            </select>
                        )}
                    </div>
                    
                    {/* CEP */}
                    {showAddressFields && (
                        <div>
                            <label className="block text-sm mb-2" style={{ color: 'rgba(255,255,255,0.6)' }}>
                                CEP {loadingCep && <span style={{ color: '#ff8c42' }}>🔍</span>}
                            </label>
                            <input
                                type="text"
                                value={cep}
                                onChange={handleCepChange}
                                placeholder="14090-000"
                                className="glass-input"
                                maxLength={9}
                                disabled={loading}
                            />
                        </div>
                    )}
                </div>
                
                {/* Endereço */}
                {showAddressFields && (
                    <div className="grid md:grid-cols-3 gap-4 mb-4">
                        <div className="md:col-span-2 relative">
                            <label className="block text-sm mb-2" style={{ color: 'rgba(255,255,255,0.6)' }}>Rua</label>
                            <input
                                type="text"
                                value={street}
                                onChange={handleStreetChange}
                                onBlur={() => setTimeout(() => setShowStreetSuggestions(false), 200)}
                                onFocus={() => streetSuggestions.length > 0 && setShowStreetSuggestions(true)}
                                placeholder="Rua..."
                                className="glass-input"
                                disabled={loading}
                                autoComplete="off"
                            />
                            {showStreetSuggestions && streetSuggestions.length > 0 && (
                                <div className="autocomplete-dropdown">
                                    {streetSuggestions.map((suggestion, idx) => (
                                        <div
                                            key={idx}
                                            onClick={() => {
                                                setStreet(suggestion);
                                                setShowStreetSuggestions(false);
                                            }}
                                            className="autocomplete-item text-white"
                                        >
                                            📍 {suggestion}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                        <div>
                            <label className="block text-sm mb-2" style={{ color: 'rgba(255,255,255,0.6)' }}>Número</label>
                            <input
                                id="numberInput"
                                type="text"
                                value={number}
                                onChange={(e) => setNumber(e.target.value)}
                                placeholder="123"
                                className="glass-input"
                                disabled={loading}
                            />
                        </div>
                    </div>
                )}
                
                {showAddressFields && (
                    <div className="grid md:grid-cols-3 gap-4 mb-4">
                        <div className="relative">
                            <label className="block text-sm mb-2" style={{ color: 'rgba(255,255,255,0.6)' }}>Bairro</label>
                            <input
                                type="text"
                                value={neighborhood}
                                onChange={handleNeighborhoodChange}
                                onBlur={() => setTimeout(() => setShowNeighborhoodSuggestions(false), 200)}
                                onFocus={() => neighborhoodSuggestions.length > 0 && setShowNeighborhoodSuggestions(true)}
                                placeholder="Centro"
                                className="glass-input"
                                disabled={loading}
                                autoComplete="off"
                            />
                            {showNeighborhoodSuggestions && neighborhoodSuggestions.length > 0 && (
                                <div className="autocomplete-dropdown">
                                    {neighborhoodSuggestions.map((suggestion, idx) => (
                                        <div
                                            key={idx}
                                            onClick={() => {
                                                setNeighborhood(suggestion);
                                                setShowNeighborhoodSuggestions(false);
                                            }}
                                            className="autocomplete-item text-white"
                                        >
                                            🏘️ {suggestion}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                        <div>
                            <label className="block text-sm mb-2" style={{ color: 'rgba(255,255,255,0.6)' }}>Cidade</label>
                            <input
                                type="text"
                                value={city}
                                onChange={(e) => setCity(e.target.value)}
                                placeholder="Ribeirão Preto"
                                className="glass-input"
                                disabled={loading}
                            />
                        </div>
                        <div>
                            <label className="block text-sm mb-2" style={{ color: 'rgba(255,255,255,0.6)' }}>Complemento</label>
                            <input
                                type="text"
                                value={complement}
                                onChange={(e) => setComplement(e.target.value)}
                                placeholder="Apto, Bloco..."
                                className="glass-input"
                                disabled={loading}
                            />
                        </div>
                    </div>
                )}
                
                {/* Status e Erro */}
                {status && (
                    <div className="mb-4 p-3 rounded-lg" style={{ background: 'rgba(34,197,94,0.15)', border: '1px solid rgba(34,197,94,0.3)', color: '#4ade80' }}>
                        {status}
                    </div>
                )}
                
                {errorMsg && (
                    <div className="mb-4 p-3 rounded-lg" style={{ background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.3)', color: '#f87171' }}>
                        {errorMsg}
                    </div>
                )}
                
                {/* Botão */}
                <div className="flex justify-end">
                    <button type="submit" disabled={loading || !hasMenuItems} className="btn-primary">
                        {loading ? '⏳ Criando...' : 'Criar Pedido'}
                    </button>
                </div>
            </form>
        </div>
    );
};

// ============ COMPONENTE: LISTA DE PEDIDOS (3 COLUNAS) ============

const OrdersList = ({ orders, onRefresh }) => {
    const pendingOrders = orders.filter(o => ['created', 'preparing'].includes(o.status));
    const readyOrders = orders.filter(o => o.status === 'ready');
    const inRouteOrders = orders.filter(o => ['assigned', 'picked_up'].includes(o.status));
    
    const handleScan = async (orderId) => {
        try {
            await authFetch(`${API_URL}/orders/${orderId}/scan`, { method: 'POST' });
            onRefresh();
        } catch (err) {
            console.error('Erro ao bipar:', err);
        }
    };
    
    const OrderCard = ({ order, showScan = false }) => (
        <div className="p-3 rounded-xl flex items-center justify-between" style={{ background: 'rgba(255,255,255,0.06)' }}>
            <div className="flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                    {order.short_id && (
                        <span className="px-2 py-0.5 rounded text-xs font-bold" style={{ background: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa' }}>
                            #{order.short_id}
                        </span>
                    )}
                    <span className="font-medium text-white">{order.customer_name}</span>
                    {order.prep_type === 'long' && (
                        <span className="badge badge-warning text-xs">Demorado</span>
                    )}
                    {/* Cronômetro - mostra desde criação até ficar pronto */}
                    {['created', 'preparing'].includes(order.status) && order.created_at && (
                        <Timer startTime={order.created_at} />
                    )}
                    {/* Cronômetro - mostra tempo esperando motoboy */}
                    {order.status === 'ready' && order.ready_at && (
                        <Timer startTime={order.ready_at} />
                    )}
                </div>
                <div className="text-sm mt-1" style={{ color: 'rgba(255,255,255,0.5)' }}>
                    {order.address_text?.split(' - ')[0]}
                </div>
                {order.tracking_code && (
                    <div className="text-xs mt-1" style={{ color: 'rgba(255,255,255,0.3)' }}>
                        Rastreio: {order.tracking_code}
                    </div>
                )}
                {order.stop_order && (
                    <div className="text-xs mt-1" style={{ color: '#60a5fa' }}>Parada #{order.stop_order}</div>
                )}
            </div>
            {showScan && (
                <button 
                    onClick={() => handleScan(order.id)} 
                    className="ml-2 py-2 px-3 rounded-lg text-sm font-medium"
                    style={{ background: 'rgba(34, 197, 94, 0.15)', color: '#4ade80', border: '1px solid rgba(34, 197, 94, 0.3)' }}
                >
                    📱 Bipar
                </button>
            )}
        </div>
    );
    
    return (
        <div className="grid md:grid-cols-3 gap-4 mb-6">
            {/* Em Preparo */}
            <div className="glass-card p-4">
                <h3 className="font-semibold mb-3 flex items-center gap-2" style={{ color: '#fbbf24', fontFamily: 'Outfit, sans-serif' }}>
                    🧑‍🍳 Em Preparo ({pendingOrders.length})
                </h3>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                    {pendingOrders.length === 0 ? (
                        <p className="text-sm text-center py-4" style={{ color: 'rgba(255,255,255,0.4)' }}>Nenhum pedido</p>
                    ) : (
                        pendingOrders.map(order => (
                            <OrderCard key={order.id} order={order} showScan={true} />
                        ))
                    )}
                </div>
            </div>
            
            {/* Prontos */}
            <div className="glass-card p-4" style={{ borderColor: 'rgba(34, 197, 94, 0.3)', borderWidth: '2px' }}>
                <h3 className="font-semibold mb-3 flex items-center gap-2" style={{ color: '#4ade80', fontFamily: 'Outfit, sans-serif' }}>
                    ✅ Prontos ({readyOrders.length})
                </h3>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                    {readyOrders.length === 0 ? (
                        <p className="text-sm text-center py-4" style={{ color: 'rgba(255,255,255,0.4)' }}>Nenhum pedido</p>
                    ) : (
                        readyOrders.map(order => (
                            <OrderCard key={order.id} order={order} />
                        ))
                    )}
                </div>
            </div>
            
            {/* Em Rota */}
            <div className="glass-card p-4">
                <h3 className="font-semibold mb-3 flex items-center gap-2" style={{ color: '#60a5fa', fontFamily: 'Outfit, sans-serif' }}>
                    🏍️ Em Rota ({inRouteOrders.length})
                </h3>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                    {inRouteOrders.length === 0 ? (
                        <p className="text-sm text-center py-4" style={{ color: 'rgba(255,255,255,0.4)' }}>Nenhum pedido</p>
                    ) : (
                        inRouteOrders.map(order => (
                            <OrderCard key={order.id} order={order} />
                        ))
                    )}
                </div>
            </div>
        </div>
    );
};

// ============ COMPONENTE: PAINEL DE MOTOBOYS ============

const CouriersPanel = ({ couriers, batches, onRefresh }) => {
    const [showInviteModal, setShowInviteModal] = useState(false);
    const [inviteData, setInviteData] = useState(null);
    const [inviteLoading, setInviteLoading] = useState(false);
    const [copySuccess, setCopySuccess] = useState(false);
    
    // Menu de opções
    const [openMenuId, setOpenMenuId] = useState(null);
    
    // Fechar menu ao clicar fora
    useEffect(() => {
        const handleClickOutside = () => {
            if (openMenuId) setOpenMenuId(null);
        };
        document.addEventListener('click', handleClickOutside);
        return () => document.removeEventListener('click', handleClickOutside);
    }, [openMenuId]);
    
    // Modal de recuperação de senha
    const [showResetModal, setShowResetModal] = useState(false);
    const [resetData, setResetData] = useState(null);
    const [resetLoading, setResetLoading] = useState(false);
    const [resetCopySuccess, setResetCopySuccess] = useState(false);
    
    // Verifica se o motoboy está retornando (busy + todos pedidos entregues)
    const isReturning = (courierId) => {
        if (!batches || batches.length === 0) return false;
        const courierBatch = batches.find(b => b.courier_id === courierId);
        if (!courierBatch || !courierBatch.orders || courierBatch.orders.length === 0) return false;
        return courierBatch.orders.every(o => o.status === 'delivered');
    };
    
    const toggleStatus = async (courier) => {
        const endpoint = courier.status === 'available' 
            ? `${API_URL}/couriers/${courier.id}/offline`
            : `${API_URL}/couriers/${courier.id}/available`;
        try {
            await authFetch(endpoint, { method: 'POST' });
            onRefresh();
        } catch (err) {
            console.error('Erro:', err);
        }
    };
    
    const completeBatch = async (courierId) => {
        try {
            await authFetch(`${API_URL}/couriers/${courierId}/complete-batch`, { method: 'POST' });
            onRefresh();
            setOpenMenuId(null);
        } catch (err) {
            console.error('Erro:', err);
        }
    };
    
    const deleteCourier = async (courierId) => {
        if (!confirm('Tem certeza que deseja excluir este motoboy?')) return;
        try {
            await authFetch(`${API_URL}/couriers/${courierId}`, { method: 'DELETE' });
            onRefresh();
            setOpenMenuId(null);
        } catch (err) {
            console.error('Erro:', err);
            alert('Erro ao excluir motoboy');
        }
    };
    
    const createPasswordReset = async (courier) => {
        setResetLoading(true);
        setOpenMenuId(null);
        try {
            const res = await authFetch(`${API_URL}/couriers/${courier.id}/password-reset`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            if (res.ok) {
                const data = await res.json();
                setResetData(data);
                setShowResetModal(true);
            }
        } catch (err) {
            console.error('Erro ao gerar link:', err);
            alert('Erro ao gerar link de recuperação');
        }
        setResetLoading(false);
    };
    
    const copyResetLink = () => {
        if (resetData?.reset_url) {
            navigator.clipboard.writeText(resetData.reset_url);
            setResetCopySuccess(true);
            setTimeout(() => setResetCopySuccess(false), 2000);
        }
    };
    
    const shareResetWhatsApp = () => {
        if (resetData?.reset_url) {
            const text = `🔑 Link para redefinir sua senha no MotoFlash:\n\n${resetData.reset_url}\n\n⏱️ Válido por ${resetData.expires_in}`;
            window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, '_blank');
        }
    };
    
    const createInvite = async () => {
        setInviteLoading(true);
        try {
            const res = await authFetch(`${API_URL}/invites`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            if (res.ok) {
                const data = await res.json();
                setInviteData(data);
                setShowInviteModal(true);
            }
        } catch (err) {
            console.error('Erro ao criar convite:', err);
        }
        setInviteLoading(false);
    };
    
    const copyLink = () => {
        if (inviteData?.invite_url) {
            navigator.clipboard.writeText(inviteData.invite_url);
            setCopySuccess(true);
            setTimeout(() => setCopySuccess(false), 2000);
        }
    };
    
    const shareWhatsApp = () => {
        if (inviteData?.invite_url) {
            const text = `🏍️ Você foi convidado para fazer entregas!\n\nClique no link para entrar na equipe:\n${inviteData.invite_url}`;
            window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, '_blank');
        }
    };
    
    const getAvatarColor = (name) => {
        const colors = [
            'rgba(239, 68, 68, 0.15)',
            'rgba(59, 130, 246, 0.15)',
            'rgba(34, 197, 94, 0.15)',
            'rgba(168, 85, 247, 0.15)',
            'rgba(251, 191, 36, 0.15)',
        ];
        const textColors = ['#f87171', '#60a5fa', '#4ade80', '#a78bfa', '#fbbf24'];
        const index = name.charCodeAt(0) % colors.length;
        return { bg: colors[index], text: textColors[index] };
    };
    
    return (
        <div className="glass-card p-5 mb-6" style={{ position: 'relative', zIndex: openMenuId ? 100 : 1, overflow: 'visible' }}>
            <h3 className="font-semibold text-white flex items-center gap-2 mb-4" style={{ fontFamily: 'Outfit, sans-serif' }}>
                🏍️ Motoqueiros ({couriers.length})
            </h3>
            
            {/* Botão Convite */}
            <button
                onClick={createInvite}
                disabled={inviteLoading}
                className="w-full mb-4 py-3 px-4 rounded-xl font-semibold flex items-center justify-center gap-2 transition-all"
                style={{ background: 'linear-gradient(135deg, #22c55e, #16a34a)', color: '#fff' }}
            >
                {inviteLoading ? '⏳ Gerando...' : '🔗 Convidar Motoboy via Link'}
            </button>
            
            {/* Lista de motoboys */}
            <div className="space-y-3" style={{ overflow: 'visible' }}>
                {couriers.map(courier => {
                    const colors = getAvatarColor(courier.name);
                    const returning = courier.status === 'busy' && isReturning(courier.id);
                    return (
                        <div key={courier.id} className="p-3 rounded-xl flex items-center justify-between" style={{ background: 'rgba(255,255,255,0.04)', overflow: 'visible' }}>
                            <div className="flex items-center gap-3">
                                <div className="courier-avatar" style={{ background: colors.bg, color: colors.text }}>
                                    {courier.name.charAt(0).toUpperCase()}
                                </div>
                                <div>
                                    <div className="text-white font-medium">{courier.name}{courier.last_name ? ` ${courier.last_name}` : ''}</div>
                                    {returning ? (
                                        <span className="badge" style={{ background: 'rgba(255, 107, 0, 0.15)', color: '#ff8c42', border: '1px solid rgba(255, 107, 0, 0.25)' }}>Retornando</span>
                                    ) : (
                                        <StatusBadge status={courier.status} />
                                    )}
                                </div>
                            </div>
                            <div className="flex items-center gap-2" style={{ overflow: 'visible' }}>
                                {/* Botão Ativar/Pausar - desabilitado quando busy */}
                                <button
                                    onClick={() => toggleStatus(courier)}
                                    disabled={courier.status === 'busy'}
                                    className="text-sm py-1.5 px-4 rounded-lg font-medium transition-all"
                                    style={courier.status === 'busy'
                                        ? { background: 'rgba(255, 255, 255, 0.05)', color: 'rgba(255,255,255,0.3)', border: '1px solid rgba(255,255,255,0.1)', cursor: 'not-allowed' }
                                        : courier.status === 'available' 
                                            ? { background: 'rgba(255, 107, 0, 0.15)', color: '#ff8c42', border: '1px solid rgba(255, 107, 0, 0.3)' }
                                            : { background: 'rgba(34, 197, 94, 0.15)', color: '#4ade80', border: '1px solid rgba(34, 197, 94, 0.3)' }
                                    }
                                >
                                    {courier.status === 'offline' ? 'Ativar' : 'Pausar'}
                                </button>
                                
                                {/* Menu 3 pontinhos */}
                                <div className="relative">
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            setOpenMenuId(openMenuId === courier.id ? null : courier.id);
                                        }}
                                        className="w-8 h-8 rounded-lg flex items-center justify-center transition-all"
                                        style={{ background: 'rgba(255,255,255,0.08)' }}
                                    >
                                        <span style={{ color: 'rgba(255,255,255,0.6)' }}>⋮</span>
                                    </button>
                                    
                                    {openMenuId === courier.id && (
                                        <div 
                                            className="courier-menu-dropdown"
                                            onClick={(e) => e.stopPropagation()}
                                        >
                                            <button
                                                onClick={() => createPasswordReset(courier)}
                                                className="w-full px-4 py-3 text-left text-sm flex items-center gap-2 transition-all"
                                                style={{ color: 'rgba(255,255,255,0.8)' }}
                                                onMouseOver={(e) => e.target.style.background = 'rgba(255,255,255,0.1)'}
                                                onMouseOut={(e) => e.target.style.background = 'transparent'}
                                            >
                                                🔑 Recuperar Senha
                                            </button>
                                            <button
                                                onClick={() => courier.status === 'busy' && completeBatch(courier.id)}
                                                disabled={courier.status !== 'busy'}
                                                className="w-full px-4 py-3 text-left text-sm flex items-center gap-2 transition-all"
                                                style={{ 
                                                    color: courier.status === 'busy' ? '#4ade80' : 'rgba(255,255,255,0.3)',
                                                    cursor: courier.status === 'busy' ? 'pointer' : 'not-allowed'
                                                }}
                                                onMouseOver={(e) => courier.status === 'busy' && (e.target.style.background = 'rgba(255,255,255,0.1)')}
                                                onMouseOut={(e) => e.target.style.background = 'transparent'}
                                            >
                                                ✓ Finalizar Entrega
                                            </button>
                                            <button
                                                onClick={() => deleteCourier(courier.id)}
                                                className="w-full px-4 py-3 text-left text-sm flex items-center gap-2 transition-all"
                                                style={{ color: '#f87171' }}
                                                onMouseOver={(e) => e.target.style.background = 'rgba(255,255,255,0.1)'}
                                                onMouseOut={(e) => e.target.style.background = 'transparent'}
                                            >
                                                🗑️ Excluir
                                            </button>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    );
                })}
                
                {couriers.length === 0 && (
                    <p className="text-center py-4" style={{ color: 'rgba(255,255,255,0.4)' }}>
                        Nenhum motoboy cadastrado
                    </p>
                )}
            </div>
            
            {/* Modal de Recuperação de Senha */}
            {showResetModal && resetData && (
                <div className="modal-overlay" onClick={() => setShowResetModal(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()}>
                        <div className="text-center mb-4">
                            <div className="w-16 h-16 mx-auto mb-3 rounded-full flex items-center justify-center" style={{ background: 'rgba(59, 130, 246, 0.15)' }}>
                                <span className="text-3xl">🔑</span>
                            </div>
                            <h2 className="text-xl font-bold text-white" style={{ fontFamily: 'Outfit, sans-serif' }}>
                                Link de Recuperação
                            </h2>
                            <p className="text-sm mt-1" style={{ color: 'rgba(255,255,255,0.5)' }}>
                                Válido por {resetData.expires_in}
                            </p>
                        </div>
                        
                        <div className="p-3 rounded-lg mb-4" style={{ background: 'rgba(255,255,255,0.08)' }}>
                            <p className="text-xs mb-1" style={{ color: 'rgba(255,255,255,0.5)' }}>Link:</p>
                            <p className="text-sm font-mono break-all text-white">{resetData.reset_url}</p>
                        </div>
                        
                        <div className="space-y-2">
                            <button
                                onClick={shareResetWhatsApp}
                                className="w-full py-3 px-4 rounded-xl font-semibold flex items-center justify-center gap-2"
                                style={{ background: '#22c55e', color: '#fff' }}
                            >
                                📱 Enviar por WhatsApp
                            </button>
                            
                            <button
                                onClick={copyResetLink}
                                className="w-full py-3 px-4 rounded-xl font-semibold flex items-center justify-center gap-2 transition-all"
                                style={{ background: resetCopySuccess ? 'rgba(34,197,94,0.2)' : 'rgba(255,255,255,0.1)', color: resetCopySuccess ? '#4ade80' : '#fff' }}
                            >
                                {resetCopySuccess ? '✓ Link Copiado!' : '📋 Copiar Link'}
                            </button>
                            
                            <button
                                onClick={() => setShowResetModal(false)}
                                className="w-full py-2 text-sm"
                                style={{ color: 'rgba(255,255,255,0.5)' }}
                            >
                                Fechar
                            </button>
                        </div>
                    </div>
                </div>
            )}
            
            {/* Modal de Convite */}
            {showInviteModal && inviteData && (
                <div className="modal-overlay" onClick={() => setShowInviteModal(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()}>
                        <div className="text-center mb-4">
                            <div className="w-16 h-16 mx-auto mb-3 rounded-full flex items-center justify-center" style={{ background: 'rgba(34, 197, 94, 0.15)' }}>
                                <span className="text-3xl">🔗</span>
                            </div>
                            <h2 className="text-xl font-bold text-white" style={{ fontFamily: 'Outfit, sans-serif' }}>
                                Convite Criado!
                            </h2>
                            <p className="text-sm mt-1" style={{ color: 'rgba(255,255,255,0.5)' }}>
                                Válido por {inviteData.expires_in || '24 horas'}
                            </p>
                        </div>
                        
                        <div className="p-3 rounded-lg mb-4" style={{ background: 'rgba(255,255,255,0.08)' }}>
                            <p className="text-xs mb-1" style={{ color: 'rgba(255,255,255,0.5)' }}>Link:</p>
                            <p className="text-sm font-mono break-all text-white">{inviteData.invite_url}</p>
                        </div>
                        
                        <div className="space-y-2">
                            <button
                                onClick={shareWhatsApp}
                                className="w-full py-3 px-4 rounded-xl font-semibold flex items-center justify-center gap-2"
                                style={{ background: '#22c55e', color: '#fff' }}
                            >
                                📱 Enviar por WhatsApp
                            </button>
                            
                            <button
                                onClick={copyLink}
                                className="w-full py-3 px-4 rounded-xl font-semibold flex items-center justify-center gap-2 transition-all"
                                style={{ background: copySuccess ? 'rgba(34,197,94,0.2)' : 'rgba(255,255,255,0.1)', color: copySuccess ? '#4ade80' : '#fff' }}
                            >
                                {copySuccess ? '✓ Link Copiado!' : '📋 Copiar Link'}
                            </button>
                            
                            <button
                                onClick={() => setShowInviteModal(false)}
                                className="w-full py-2 text-sm"
                                style={{ color: 'rgba(255,255,255,0.5)' }}
                            >
                                Fechar
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

// ============ COMPONENTE: ROTAS ATIVAS ============

const ActiveBatches = ({ batches }) => {
    // Filtra batches que ainda têm pedidos pendentes (oculta quando está retornando)
    const activeBatches = (batches || []).filter(batch => {
        if (!batch.orders || batch.orders.length === 0) return false;
        // Mostra só se tiver pelo menos 1 pedido não entregue
        return batch.orders.some(o => o.status !== 'delivered');
    });
    
    if (activeBatches.length === 0) {
        return (
            <div className="glass-card p-5">
                <h3 className="font-semibold text-white flex items-center gap-2 mb-4" style={{ fontFamily: 'Outfit, sans-serif' }}>
                    🚀 Rotas Ativas
                </h3>
                <p className="text-center py-4" style={{ color: 'rgba(255,255,255,0.4)' }}>
                    Nenhuma rota ativa
                </p>
            </div>
        );
    }
    
    return (
        <div className="glass-card p-5">
            <h3 className="font-semibold text-white flex items-center gap-2 mb-4" style={{ fontFamily: 'Outfit, sans-serif' }}>
                🚀 Rotas Ativas ({activeBatches.length})
            </h3>
            <div className="space-y-3">
                {activeBatches.map(batch => {
                    const pendingOrders = batch.orders?.filter(o => o.status !== 'delivered') || [];
                    return (
                        <div key={batch.id} className="p-4 rounded-xl" style={{ background: 'rgba(255,255,255,0.04)' }}>
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-white font-medium">{batch.courier_name}</span>
                                <span className="badge badge-info">{pendingOrders.length} entregas</span>
                            </div>
                            <div className="text-sm" style={{ color: 'rgba(255,255,255,0.4)' }}>
                                📍 {pendingOrders.map(o => o.address_text?.split(',')[0]).join(' → ')}
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

// ============ COMPONENTE: DISPATCH CONTROL ============

const DispatchControl = ({ onDispatch, stats }) => {
    const [loading, setLoading] = useState(false);
    const [lastResult, setLastResult] = useState(null);
    
    // Auto-dismiss do resultado após 5 segundos
    useEffect(() => {
        if (lastResult) {
            const timer = setTimeout(() => setLastResult(null), 5000);
            return () => clearTimeout(timer);
        }
    }, [lastResult]);
    
    const runDispatch = async () => {
        setLoading(true);
        try {
            const res = await authFetch(`${API_URL}/dispatch/run`, { method: 'POST' });
            const result = await res.json();
            setLastResult(result);
            onDispatch();
        } catch (err) {
            setLastResult({ message: 'Erro ao executar dispatch' });
        }
        setLoading(false);
    };
    
    const canDispatch = stats && stats.orders?.ready > 0 && stats.couriers?.available > 0;
    
    return (
        <div className="glass-card p-5 mb-6" style={{ borderColor: 'rgba(255,107,0,0.3)', borderWidth: '2px' }}>
            <div className="flex items-center justify-between flex-wrap gap-4">
                <div>
                    <h3 className="font-semibold flex items-center gap-2" style={{ color: '#ff8c42', fontFamily: 'Outfit, sans-serif' }}>
                        🚀 Dispatch - Distribuir Pedidos
                    </h3>
                    <p className="text-sm mt-1" style={{ color: 'rgba(255,255,255,0.5)' }}>
                        {stats?.orders?.ready || 0} pronto(s) · {stats?.couriers?.available || 0} motoboy(s)
                    </p>
                </div>
                <button 
                    onClick={runDispatch} 
                    disabled={loading || !canDispatch}
                    className="btn-primary text-lg px-6 py-3"
                >
                    {loading ? '⏳...' : '🚀 Executar'}
                </button>
            </div>
            
            {lastResult && (
                <div 
                    className="mt-3 p-3 rounded-lg"
                    style={{ 
                        background: lastResult.batches_created > 0 ? 'rgba(34,197,94,0.15)' : 'rgba(255,255,255,0.08)',
                        color: lastResult.batches_created > 0 ? '#4ade80' : 'rgba(255,255,255,0.6)'
                    }}
                >
                    {lastResult.message}
                </div>
            )}
        </div>
    );
};

// ============ SIDEBAR ============

const Sidebar = ({ currentPage, setCurrentPage, restaurantName, onLogout, stats, sidebarOpen, setSidebarOpen }) => {
    const navItems = [
        { id: 'inicio', icon: '🏠', label: 'Início' },
        { id: 'pedidos', icon: '📦', label: 'Pedidos', badge: stats?.orders?.ready },
        { id: 'motoboys', icon: '🏍️', label: 'Motoqueiros' },
        { id: 'rastreamento', icon: '📍', label: 'Rastreamento' },
    ];
    
    const manageItems = [
        { id: 'cardapio', icon: '🍽️', label: 'Cardápio' },
        { id: 'clientes', icon: '👥', label: 'Clientes' },
        { id: 'relatorios', icon: '📊', label: 'Relatórios' },
    ];
    
    const systemItems = [
        { id: 'configuracoes', icon: '⚙️', label: 'Configurações' },
        { id: 'ajuda', icon: '❓', label: 'Ajuda' },
    ];
    
    const NavItem = ({ item }) => (
        <div
            onClick={() => {
                setCurrentPage(item.id);
                setSidebarOpen(false);
            }}
            className={`nav-item ${currentPage === item.id ? 'active' : ''}`}
        >
            <span className="nav-icon">{item.icon}</span>
            <span>{item.label}</span>
            {item.badge > 0 && <span className="nav-badge">{item.badge}</span>}
        </div>
    );
    
    return (
        <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
            {/* Logo */}
            <div className="sidebar-header">
                <div className="flex items-center gap-3">
                    <svg width="40" height="40" viewBox="0 0 80 80" fill="none">
                        <circle cx="40" cy="40" r="34" fill="#FF6B00"/>
                        <path d="M44 12 L28 40 L38 40 L32 68 L56 36 L44 36 L52 12 Z" fill="white"/>
                    </svg>
                    <div>
                        <h1 className="text-lg font-bold" style={{ fontFamily: 'Outfit, sans-serif' }}>
                            <span className="text-white">Moto</span>
                            <span className="text-gradient-orange">Flash</span>
                        </h1>
                        <p className="text-xs" style={{ color: 'rgba(255,255,255,0.4)' }}>Despacho Inteligente</p>
                    </div>
                </div>
            </div>
            
            {/* Navigation */}
            <nav className="sidebar-nav">
                <div className="nav-section">
                    <div className="nav-section-title">Principal</div>
                    {navItems.map(item => <NavItem key={item.id} item={item} />)}
                </div>
                
                <div className="nav-section">
                    <div className="nav-section-title">Gerenciar</div>
                    {manageItems.map(item => <NavItem key={item.id} item={item} />)}
                </div>
                
                <div className="nav-section">
                    <div className="nav-section-title">Sistema</div>
                    {systemItems.map(item => <NavItem key={item.id} item={item} />)}
                </div>
            </nav>
            
            {/* User Card */}
            <div className="sidebar-footer">
                <div className="user-card">
                    <div className="user-avatar">
                        {restaurantName.charAt(0).toUpperCase()}
                    </div>
                    <div className="user-info">
                        <div className="user-name">{restaurantName}</div>
                        <div className="user-status">
                            <span className="status-dot"></span>
                            Conectado
                        </div>
                    </div>
                    <button 
                        onClick={onLogout}
                        style={{ color: 'rgba(255,255,255,0.5)', background: 'none', border: 'none', cursor: 'pointer', fontSize: '12px' }}
                        title="Sair"
                    >
                        Sair
                    </button>
                </div>
            </div>
        </aside>
    );
};

// ============ PÁGINA: INÍCIO (DASHBOARD) ============

const DashboardPage = ({ stats, alerts, recommendation, orders, couriers, batches, fetchAll, simulatedDate }) => {
    return (
        <>
            <StatsPanel stats={stats} />
            <AlertsPanel alerts={alerts} recommendation={recommendation} />
            
            <div className="grid lg:grid-cols-3 gap-6 mb-6">
                <div className="lg:col-span-2">
                    <NewOrderForm onOrderCreated={fetchAll} simulatedDate={simulatedDate} />
                    <DispatchControl onDispatch={fetchAll} stats={stats} />
                </div>
                
                <div>
                    <CouriersPanel couriers={couriers} batches={batches} onRefresh={fetchAll} />
                    <ActiveBatches batches={batches} />
                </div>
            </div>
            
            {/* Lista de Pedidos em 3 colunas - ocupa toda a largura */}
            <OrdersList orders={orders} onRefresh={fetchAll} />
        </>
    );
};

// ============ PÁGINA: CARDÁPIO ============

// === FORMULÁRIO CATEGORIA (fora do CardapioPage para evitar re-render) ===
const CategoryForm = ({ category, onSave, onCancel }) => {
    const [name, setName] = useState(category?.name || '');
    const [order, setOrder] = useState(category?.order || 0);
    const [saving, setSaving] = useState(false);
    
    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!name.trim()) return;
        setSaving(true);
        await onSave({ name: name.trim(), order: parseInt(order) });
        setSaving(false);
    };
    
    return (
        <form onSubmit={handleSubmit}>
            <div className="mb-4">
                <label className="block text-sm mb-2" style={{ color: 'rgba(255,255,255,0.7)' }}>
                    Nome da Categoria
                </label>
                <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Ex: Hambúrgueres, Bebidas..."
                    className="glass-input w-full"
                    required
                    autoFocus
                />
            </div>
            <div className="mb-6">
                <label className="block text-sm mb-2" style={{ color: 'rgba(255,255,255,0.7)' }}>
                    Ordem de exibição
                </label>
                <input
                    type="number"
                    value={order}
                    onChange={(e) => setOrder(e.target.value)}
                    className="glass-input w-full"
                    min="0"
                />
            </div>
            <div className="flex gap-3">
                <button
                    type="button"
                    onClick={onCancel}
                    className="flex-1 px-4 py-3 rounded-xl font-medium transition-all"
                    style={{ background: 'rgba(255,255,255,0.1)', color: 'rgba(255,255,255,0.7)' }}
                >
                    Cancelar
                </button>
                <button
                    type="submit"
                    disabled={saving || !name.trim()}
                    className="flex-1 px-4 py-3 rounded-xl font-medium transition-all text-white disabled:opacity-50"
                    style={{ background: 'linear-gradient(135deg, #ff6b00 0%, #ff8c42 100%)' }}
                >
                    {saving ? 'Salvando...' : (category ? 'Atualizar' : 'Criar')}
                </button>
            </div>
        </form>
    );
};

// === FORMULÁRIO ITEM (fora do CardapioPage para evitar re-render) ===
const ItemForm = ({ item, categories, onSave, onCancel }) => {
    const [name, setName] = useState(item?.name || '');
    const [description, setDescription] = useState(item?.description || '');
    const [price, setPrice] = useState(item?.price || '');
    const [categoryId, setCategoryId] = useState(item?.category_id || categories[0]?.id || '');
    const [imageUrl, setImageUrl] = useState(item?.image_url || '');
    const [loading, setLoading] = useState(false);
    const [uploading, setUploading] = useState(false);
    
    // Faz upload da imagem
    const handleImageUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        // Verifica tamanho (5MB)
        if (file.size > 5 * 1024 * 1024) {
            alert('Imagem muito grande! Máximo: 5MB');
            return;
        }
        
        setUploading(true);
        
        try {
            // FormData é como um "envelope" pra enviar arquivos
            const formData = new FormData();
            formData.append('file', file);
            
            // Para upload com FormData, só adiciona o Authorization
            const token = getToken();
            const res = await fetch(`${API_URL}/upload`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData  // Não precisa de Content-Type, o browser configura
            });
            
            if (res.ok) {
                const data = await res.json();
                setImageUrl(data.url);  // Salva a URL retornada
            } else {
                const err = await res.json();
                alert(err.detail || 'Erro ao enviar imagem');
            }
        } catch (err) {
            alert('Erro de conexão');
        }
        
        setUploading(false);
    };
    
    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        
        try {
            const url = item 
                ? `${API_URL}/menu/items/${item.id}`
                : `${API_URL}/menu/items`;
            
            const res = await authFetch(url, {
                method: item ? 'PUT' : 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name,
                    description: description || null,
                    price: parseFloat(price),
                    category_id: categoryId,
                    image_url: imageUrl || null  // Inclui a URL da imagem
                })
            });
            
            if (res.ok) {
                onSave();
            } else {
                const err = await res.json();
                alert(err.detail || 'Erro ao salvar');
            }
        } catch (err) {
            alert('Erro de conexão');
        }
        
        setLoading(false);
    };
    
    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            {/* FOTO DO ITEM */}
            <div>
                <label className="block text-sm mb-2" style={{ color: 'rgba(255,255,255,0.7)' }}>
                    Foto do Item <span style={{ color: 'rgba(255,255,255,0.4)' }}>(opcional)</span>
                </label>
                
                <div className="flex items-start gap-4">
                    {/* Preview da imagem */}
                    <div 
                        className="w-24 h-24 rounded-lg overflow-hidden flex items-center justify-center"
                        style={{ background: 'rgba(255,255,255,0.1)', border: '2px dashed rgba(255,255,255,0.2)' }}
                    >
                        {imageUrl ? (
                            <img 
                                src={`${API_URL}${imageUrl}`} 
                                alt="Preview" 
                                className="w-full h-full object-cover"
                            />
                        ) : (
                            <span className="text-3xl" style={{ color: 'rgba(255,255,255,0.3)' }}>📷</span>
                        )}
                    </div>
                    
                    {/* Botão de upload */}
                    <div className="flex-1">
                        <label className={`
                            block w-full px-4 py-2 text-center rounded-lg cursor-pointer transition-all
                            ${uploading 
                                ? 'bg-white/5 text-white/40' 
                                : 'bg-orange-500/20 text-orange-400 hover:bg-orange-500/30'
                            }
                        `}>
                            {uploading ? '⏳ Enviando...' : imageUrl ? '🔄 Trocar foto' : '📤 Escolher foto'}
                            <input
                                type="file"
                                accept="image/jpeg,image/png,image/webp,image/gif"
                                onChange={handleImageUpload}
                                className="hidden"
                                disabled={uploading}
                            />
                        </label>
                        <p className="text-xs mt-1" style={{ color: 'rgba(255,255,255,0.4)' }}>JPG, PNG ou WebP. Máx: 5MB</p>
                        
                        {imageUrl && (
                            <button
                                type="button"
                                onClick={() => setImageUrl('')}
                                className="text-xs text-red-500 hover:text-red-400 mt-1"
                            >
                                🗑️ Remover foto
                            </button>
                        )}
                    </div>
                </div>
            </div>
            
            <div>
                <label className="block text-sm mb-2" style={{ color: 'rgba(255,255,255,0.7)' }}>Nome do Item</label>
                <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Ex: X-Burguer Especial"
                    className="glass-input w-full"
                    required
                />
            </div>
            <div>
                <label className="block text-sm mb-2" style={{ color: 'rgba(255,255,255,0.7)' }}>Descrição (opcional)</label>
                <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Pão, carne 180g, queijo, bacon, alface..."
                    className="glass-input w-full"
                    rows={2}
                />
            </div>
            <div>
                <label className="block text-sm mb-2" style={{ color: 'rgba(255,255,255,0.7)' }}>Preço (R$)</label>
                <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={price}
                    onChange={(e) => setPrice(e.target.value)}
                    placeholder="29.90"
                    className="glass-input w-full"
                    required
                />
            </div>
            <div>
                <label className="block text-sm mb-2" style={{ color: 'rgba(255,255,255,0.7)' }}>Categoria</label>
                <select
                    value={categoryId}
                    onChange={(e) => setCategoryId(e.target.value)}
                    className="glass-input w-full"
                    required
                >
                    {categories.map(cat => (
                        <option key={cat.id} value={cat.id}>{cat.name}</option>
                    ))}
                </select>
            </div>
            <div className="flex gap-3 pt-2">
                <button
                    type="button"
                    onClick={onCancel}
                    className="flex-1 px-4 py-3 rounded-xl font-medium transition-all"
                    style={{ background: 'rgba(255,255,255,0.1)', color: 'rgba(255,255,255,0.7)' }}
                >
                    Cancelar
                </button>
                <button
                    type="submit"
                    disabled={loading || !name.trim() || !price}
                    className="flex-1 px-4 py-3 rounded-xl font-medium transition-all text-white disabled:opacity-50"
                    style={{ background: 'linear-gradient(135deg, #ff6b00 0%, #ff8c42 100%)' }}
                >
                    {loading ? 'Salvando...' : item ? 'Atualizar' : 'Criar'}
                </button>
            </div>
        </form>
    );
};

// ============ FORMULÁRIO DE CLIENTE (copiado do clientes.html) ============

const CustomerForm = ({ customer, onSave, onCancel }) => {
    const [phone, setPhone] = useState(customer?.phone || '');
    const [name, setName] = useState(customer?.name || '');
    
    // Campos de endereço SEPARADOS
    const [cep, setCep] = useState('');
    const [street, setStreet] = useState('');
    const [number, setNumber] = useState('');
    const [neighborhood, setNeighborhood] = useState('');
    const [city, setCity] = useState('Ribeirão Preto');
    const [complement, setComplement] = useState(customer?.complement || '');
    const [loadingCep, setLoadingCep] = useState(false);
    
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    
    // Autocomplete Photon
    const [streetSuggestions, setStreetSuggestions] = useState([]);
    const [showStreetSuggestions, setShowStreetSuggestions] = useState(false);
    const [neighborhoodSuggestions, setNeighborhoodSuggestions] = useState([]);
    const [showNeighborhoodSuggestions, setShowNeighborhoodSuggestions] = useState(false);
    const [citySuggestions, setCitySuggestions] = useState([]);
    const [showCitySuggestions, setShowCitySuggestions] = useState(false);
    
    // Parseia endereço existente ao carregar
    useEffect(() => {
        if (customer?.address) {
            parseAddress(customer.address);
        }
    }, [customer]);
    
    // Tenta parsear endereço em campos separados
    const parseAddress = (fullAddress) => {
        const dashParts = fullAddress.split(' - ');
        
        if (dashParts.length >= 2) {
            const ruaENumero = dashParts[0];
            const bairroECidade = dashParts.slice(1).join(' - ');
            
            const ruaParts = ruaENumero.split(',').map(p => p.trim());
            if (ruaParts.length >= 2) {
                setStreet(ruaParts[0]);
                setNumber(ruaParts[1]);
            } else {
                setStreet(ruaParts[0]);
            }
            
            const bairroParts = bairroECidade.split(',').map(p => p.trim());
            if (bairroParts.length >= 2) {
                setNeighborhood(bairroParts[0]);
                setCity(bairroParts[1]);
            } else if (bairroParts.length === 1) {
                setNeighborhood(bairroParts[0]);
            }
        } else {
            const parts = fullAddress.split(',').map(p => p.trim());
            if (parts.length >= 1) setStreet(parts[0]);
            if (parts.length >= 2) setNumber(parts[1]);
            if (parts.length >= 3) setNeighborhood(parts[2]);
            if (parts.length >= 4) setCity(parts[3]);
        }
    };
    
    // Formata telefone
    const formatPhoneInput = (value) => {
        const numbers = value.replace(/\D/g, '');
        if (numbers.length <= 2) return `(${numbers}`;
        if (numbers.length <= 7) return `(${numbers.slice(0,2)}) ${numbers.slice(2)}`;
        return `(${numbers.slice(0,2)}) ${numbers.slice(2,7)}-${numbers.slice(7,11)}`;
    };
    
    const handlePhoneChange = (e) => {
        setPhone(formatPhoneInput(e.target.value));
    };
    
    // Formata CEP
    const formatCepInput = (value) => {
        const numbers = value.replace(/\D/g, '');
        if (numbers.length <= 5) return numbers;
        return `${numbers.slice(0,5)}-${numbers.slice(5,8)}`;
    };
    
    // Busca endereço pelo CEP (ViaCEP)
    const handleCepChange = async (e) => {
        const formatted = formatCepInput(e.target.value);
        setCep(formatted);
        
        const numbers = formatted.replace(/\D/g, '');
        
        if (numbers.length === 8) {
            setLoadingCep(true);
            try {
                const res = await fetch(`https://viacep.com.br/ws/${numbers}/json/`);
                if (res.ok) {
                    const data = await res.json();
                    if (!data.erro) {
                        setStreet(data.logradouro || '');
                        setNeighborhood(data.bairro || '');
                        setCity(data.localidade || '');
                        setTimeout(() => {
                            document.getElementById('customerNumberInput')?.focus();
                        }, 100);
                    }
                }
            } catch (err) {
                console.error('Erro ViaCEP:', err);
            }
            setLoadingCep(false);
        }
    };
    
    // Remove acentos
    const removeAccents = (str) => str.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    
    // Busca sugestões no Photon
    const searchPhoton = async (query, type) => {
        if (query.trim().length < 3) return [];
        
        try {
            const cleanQuery = removeAccents(query);
            const fullQuery = type === 'city' 
                ? `${cleanQuery} Brasil`
                : `${cleanQuery} ${removeAccents(city || 'Ribeirao Preto')}`;
            
            const res = await fetch(
                `https://photon.komoot.io/api/?q=${encodeURIComponent(fullQuery)}&limit=5&lat=-21.17&lon=-47.80`
            );
            
            if (res.ok) {
                const data = await res.json();
                if (data.features && data.features.length > 0) {
                    const values = new Set();
                    data.features.forEach(f => {
                        const p = f.properties;
                        if (type === 'street') {
                            const name = p.name || p.street;
                            if (name) values.add(name);
                        } else if (type === 'neighborhood') {
                            const bairro = p.suburb || p.district || p.locality || p.neighbourhood;
                            if (bairro && bairro !== p.city) values.add(bairro);
                        } else if (type === 'city') {
                            if (p.city) values.add(p.city);
                        }
                    });
                    return Array.from(values);
                }
            }
        } catch (err) {
            console.error('Erro Photon:', err);
        }
        return [];
    };
    
    // Handlers de autocomplete
    const handleStreetChange = async (e) => {
        const value = e.target.value;
        setStreet(value);
        const suggestions = await searchPhoton(value, 'street');
        setStreetSuggestions(suggestions);
        setShowStreetSuggestions(suggestions.length > 0);
    };
    
    const handleNeighborhoodChange = async (e) => {
        const value = e.target.value;
        setNeighborhood(value);
        const suggestions = await searchPhoton(value, 'neighborhood');
        setNeighborhoodSuggestions(suggestions);
        setShowNeighborhoodSuggestions(suggestions.length > 0);
    };
    
    const handleCityChange = async (e) => {
        const value = e.target.value;
        setCity(value);
        const suggestions = await searchPhoton(value, 'city');
        setCitySuggestions(suggestions);
        setShowCitySuggestions(suggestions.length > 0);
    };
    
    // Monta endereço completo
    const getFullAddress = () => {
        let addr = street;
        if (number) addr += `, ${number}`;
        if (neighborhood) addr += ` - ${neighborhood}`;
        if (city) addr += `, ${city}`;
        return addr;
    };
    
    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        
        if (!phone || phone.replace(/\D/g, '').length < 10) {
            setError('Telefone inválido');
            setLoading(false);
            return;
        }
        
        if (!name.trim()) {
            setError('Digite o nome');
            setLoading(false);
            return;
        }
        
        if (!street.trim()) {
            setError('Digite a rua');
            setLoading(false);
            return;
        }
        
        if (!number.trim()) {
            setError('Digite o número');
            setLoading(false);
            return;
        }
        
        if (!city.trim()) {
            setError('Digite a cidade');
            setLoading(false);
            return;
        }
        
        try {
            const url = customer 
                ? `${API_URL}/customers/${customer.id}`
                : `${API_URL}/customers`;
            
            const res = await authFetch(url, {
                method: customer ? 'PUT' : 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    phone: phone.replace(/\D/g, ''),
                    name: name.trim(),
                    address: getFullAddress(),
                    complement: complement.trim() || null
                })
            });
            
            if (res.ok) {
                onSave();
            } else {
                const err = await res.json();
                setError(err.detail || 'Erro ao salvar');
            }
        } catch (err) {
            setError('Erro de conexão');
        }
        
        setLoading(false);
    };
    
    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
                <div className="p-3 rounded-lg text-sm" style={{ background: 'rgba(239, 68, 68, 0.2)', color: '#ef4444' }}>
                    ⚠️ {error}
                </div>
            )}
            
            {/* Telefone */}
            <div>
                <label className="block text-sm mb-2" style={{ color: 'rgba(255,255,255,0.7)' }}>Telefone *</label>
                <input
                    type="tel"
                    value={phone}
                    onChange={handlePhoneChange}
                    placeholder="(16) 99999-1234"
                    className="glass-input w-full"
                    maxLength={15}
                />
            </div>
            
            {/* Nome */}
            <div>
                <label className="block text-sm mb-2" style={{ color: 'rgba(255,255,255,0.7)' }}>Nome *</label>
                <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="João Silva"
                    className="glass-input w-full"
                />
            </div>
            
            {/* CEP - só aparece em cadastro novo */}
            {!customer && (
                <div>
                    <label className="block text-sm mb-2" style={{ color: 'rgba(255,255,255,0.7)' }}>
                        CEP
                        {loadingCep && <span className="ml-2" style={{ color: '#ff8c42' }}>🔍 Buscando...</span>}
                    </label>
                    <input
                        type="text"
                        value={cep}
                        onChange={handleCepChange}
                        placeholder="14090-000"
                        className="glass-input w-full"
                        maxLength={9}
                    />
                    <p className="text-xs mt-1" style={{ color: 'rgba(255,255,255,0.4)' }}>💡 Digite o CEP para preencher automaticamente</p>
                </div>
            )}
            
            {/* Rua */}
            <div className="relative">
                <label className="block text-sm mb-2" style={{ color: 'rgba(255,255,255,0.7)' }}>Rua *</label>
                <input
                    type="text"
                    value={street}
                    onChange={handleStreetChange}
                    onBlur={() => setTimeout(() => setShowStreetSuggestions(false), 200)}
                    onFocus={() => streetSuggestions.length > 0 && setShowStreetSuggestions(true)}
                    placeholder="Ex: Rua Rangel Pestana"
                    className="glass-input w-full"
                    autoComplete="off"
                />
                {showStreetSuggestions && streetSuggestions.length > 0 && (
                    <div className="absolute z-20 w-full mt-1 rounded-lg shadow-lg max-h-40 overflow-y-auto" style={{ background: 'rgba(30, 30, 40, 0.95)', border: '1px solid rgba(255,255,255,0.1)' }}>
                        {streetSuggestions.map((s, i) => (
                            <button key={i} type="button" onClick={() => { setStreet(s); setShowStreetSuggestions(false); }}
                                className="w-full px-3 py-2 text-left text-sm text-white hover:bg-white/10 border-b border-white/5 last:border-0">
                                📍 {s}
                            </button>
                        ))}
                    </div>
                )}
            </div>
            
            {/* Número + Bairro */}
            <div className="grid grid-cols-3 gap-3">
                <div>
                    <label className="block text-sm mb-2" style={{ color: 'rgba(255,255,255,0.7)' }}>Número *</label>
                    <input
                        id="customerNumberInput"
                        type="text"
                        value={number}
                        onChange={(e) => setNumber(e.target.value)}
                        placeholder="834"
                        className="glass-input w-full"
                    />
                </div>
                
                <div className="col-span-2 relative">
                    <label className="block text-sm mb-2" style={{ color: 'rgba(255,255,255,0.7)' }}>Bairro</label>
                    <input
                        type="text"
                        value={neighborhood}
                        onChange={handleNeighborhoodChange}
                        onBlur={() => setTimeout(() => setShowNeighborhoodSuggestions(false), 200)}
                        onFocus={() => neighborhoodSuggestions.length > 0 && setShowNeighborhoodSuggestions(true)}
                        placeholder="Ex: Vila Virginia"
                        className="glass-input w-full"
                        autoComplete="off"
                    />
                    {showNeighborhoodSuggestions && neighborhoodSuggestions.length > 0 && (
                        <div className="absolute z-20 w-full mt-1 rounded-lg shadow-lg max-h-40 overflow-y-auto" style={{ background: 'rgba(30, 30, 40, 0.95)', border: '1px solid rgba(255,255,255,0.1)' }}>
                            {neighborhoodSuggestions.map((s, i) => (
                                <button key={i} type="button" onClick={() => { setNeighborhood(s); setShowNeighborhoodSuggestions(false); }}
                                    className="w-full px-3 py-2 text-left text-sm text-white hover:bg-white/10 border-b border-white/5 last:border-0">
                                    📍 {s}
                                </button>
                            ))}
                        </div>
                    )}
                </div>
            </div>
            
            {/* Cidade */}
            <div className="relative">
                <label className="block text-sm mb-2" style={{ color: 'rgba(255,255,255,0.7)' }}>Cidade *</label>
                <input
                    type="text"
                    value={city}
                    onChange={handleCityChange}
                    onBlur={() => setTimeout(() => setShowCitySuggestions(false), 200)}
                    onFocus={() => citySuggestions.length > 0 && setShowCitySuggestions(true)}
                    placeholder="Ex: Ribeirão Preto"
                    className="glass-input w-full"
                    autoComplete="off"
                />
                {showCitySuggestions && citySuggestions.length > 0 && (
                    <div className="absolute z-20 w-full mt-1 rounded-lg shadow-lg max-h-40 overflow-y-auto" style={{ background: 'rgba(30, 30, 40, 0.95)', border: '1px solid rgba(255,255,255,0.1)' }}>
                        {citySuggestions.map((s, i) => (
                            <button key={i} type="button" onClick={() => { setCity(s); setShowCitySuggestions(false); }}
                                className="w-full px-3 py-2 text-left text-sm text-white hover:bg-white/10 border-b border-white/5 last:border-0">
                                📍 {s}
                            </button>
                        ))}
                    </div>
                )}
            </div>
            
            {/* Complemento */}
            <div>
                <label className="block text-sm mb-2" style={{ color: 'rgba(255,255,255,0.7)' }}>
                    Complemento <span style={{ color: 'rgba(255,255,255,0.4)' }}>(opcional)</span>
                </label>
                <input
                    type="text"
                    value={complement}
                    onChange={(e) => setComplement(e.target.value)}
                    placeholder="Apto 45, Bloco B, Portão azul..."
                    className="glass-input w-full"
                />
            </div>
            
            <div className="flex gap-3 pt-2">
                <button
                    type="button"
                    onClick={onCancel}
                    className="flex-1 px-4 py-3 rounded-xl font-medium transition-all"
                    style={{ background: 'rgba(255,255,255,0.1)', color: 'rgba(255,255,255,0.7)' }}
                >
                    Cancelar
                </button>
                <button
                    type="submit"
                    disabled={loading}
                    className="flex-1 px-4 py-3 rounded-xl font-medium transition-all text-white disabled:opacity-50"
                    style={{ background: 'linear-gradient(135deg, #ff6b00 0%, #ff8c42 100%)' }}
                >
                    {loading ? 'Salvando...' : customer ? 'Atualizar' : 'Cadastrar'}
                </button>
            </div>
        </form>
    );
};

// ============ PÁGINA: CLIENTES ============

const ClientesPage = () => {
    const [customers, setCustomers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    
    // Modal
    const [showModal, setShowModal] = useState(false);
    const [editingCustomer, setEditingCustomer] = useState(null);
    
    const fetchCustomers = async () => {
        try {
            const url = search 
                ? `${API_URL}/customers?search=${encodeURIComponent(search)}`
                : `${API_URL}/customers`;
            
            const res = await authFetch(url);
            if (res.ok) {
                setCustomers(await res.json());
            }
        } catch (err) {
            console.error('Erro ao buscar clientes:', err);
        }
        setLoading(false);
    };
    
    useEffect(() => {
        fetchCustomers();
    }, [search]);
    
    const handleSave = () => {
        setShowModal(false);
        setEditingCustomer(null);
        fetchCustomers();
    };
    
    const handleDelete = async (customer) => {
        if (!confirm(`Excluir cliente "${customer.name}"?`)) return;
        
        try {
            const res = await authFetch(`${API_URL}/customers/${customer.id}`, {
                method: 'DELETE'
            });
            
            if (res.ok) {
                fetchCustomers();
            } else {
                const err = await res.json();
                alert(err.detail || 'Erro ao excluir');
            }
        } catch (err) {
            alert('Erro de conexão');
        }
    };
    
    const formatPhoneDisplay = (phone) => {
        if (!phone) return '';
        const numbers = phone.replace(/\D/g, '');
        if (numbers.length === 11) {
            return `(${numbers.slice(0,2)}) ${numbers.slice(2,7)}-${numbers.slice(7)}`;
        }
        if (numbers.length === 10) {
            return `(${numbers.slice(0,2)}) ${numbers.slice(2,6)}-${numbers.slice(6)}`;
        }
        return phone;
    };
    
    if (loading) {
        return (
            <div className="glass-card p-8 text-center">
                <div className="text-5xl mb-4">👥</div>
                <div style={{ color: 'rgba(255,255,255,0.5)' }}>Carregando clientes...</div>
            </div>
        );
    }
    
    return (
        <>
            {/* Header com stats */}
            <div className="glass-card p-4 mb-6">
                <div className="flex items-center justify-between flex-wrap gap-4">
                    <div className="flex items-center gap-4">
                        <span className="text-3xl">👥</span>
                        <div>
                            <h2 className="text-lg font-semibold text-white">Clientes</h2>
                            <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: '14px' }}>
                                {customers.length} cliente(s) cadastrado(s)
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={() => { setEditingCustomer(null); setShowModal(true); }}
                        className="px-4 py-2 rounded-xl font-medium text-white transition-all"
                        style={{ background: 'linear-gradient(135deg, #ff6b00 0%, #ff8c42 100%)' }}
                    >
                        + Novo Cliente
                    </button>
                </div>
            </div>
            
            {/* Busca */}
            <div className="glass-card p-4 mb-6">
                <div className="relative">
                    <input
                        type="text"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        placeholder="🔍 Buscar por nome ou telefone..."
                        className="glass-input w-full"
                    />
                    {search && (
                        <button 
                            onClick={() => setSearch('')}
                            className="absolute right-3 top-1/2 -translate-y-1/2"
                            style={{ color: 'rgba(255,255,255,0.4)' }}
                        >
                            ✕
                        </button>
                    )}
                </div>
            </div>
            
            {/* Lista de clientes */}
            <div className="glass-card p-4">
                {customers.length === 0 ? (
                    <div className="text-center py-12" style={{ color: 'rgba(255,255,255,0.5)' }}>
                        <div className="text-5xl mb-3">👥</div>
                        <p className="font-medium">Nenhum cliente {search ? 'encontrado' : 'cadastrado'}</p>
                        <p className="text-sm mt-1">{search ? 'Tente outro termo' : 'Cadastre seu primeiro cliente!'}</p>
                    </div>
                ) : (
                    <div className="space-y-2">
                        {customers.map(customer => (
                            <div 
                                key={customer.id} 
                                className="group flex items-center justify-between p-4 rounded-xl transition-all"
                                style={{ background: 'rgba(255,255,255,0.05)' }}
                            >
                                <div className="flex items-center gap-4">
                                    <div 
                                        className="w-12 h-12 rounded-full flex items-center justify-center font-bold text-lg"
                                        style={{ background: 'rgba(255, 107, 0, 0.2)', color: '#ff8c42' }}
                                    >
                                        {customer.name.charAt(0).toUpperCase()}
                                    </div>
                                    <div>
                                        <div className="font-medium text-white">{customer.name}</div>
                                        <div className="text-sm" style={{ color: 'rgba(255,255,255,0.5)' }}>{formatPhoneDisplay(customer.phone)}</div>
                                        <div className="text-xs mt-1" style={{ color: 'rgba(255,255,255,0.4)' }}>
                                            📍 {customer.address}
                                            {customer.complement && ` - ${customer.complement}`}
                                        </div>
                                    </div>
                                </div>
                                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <button 
                                        onClick={() => { setEditingCustomer(customer); setShowModal(true); }}
                                        className="p-2 rounded-lg hover:bg-white/10"
                                        title="Editar"
                                    >
                                        ✏️
                                    </button>
                                    <button 
                                        onClick={() => handleDelete(customer)}
                                        className="p-2 rounded-lg hover:bg-red-500/20"
                                        title="Excluir"
                                    >
                                        🗑️
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
            
            {/* Modal */}
            {showModal && (
                <div className="modal-overlay" onClick={() => { setShowModal(false); setEditingCustomer(null); }}>
                    <div className="modal-content" onClick={e => e.stopPropagation()}>
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="text-lg font-semibold text-white">
                                {editingCustomer ? 'Editar Cliente' : 'Novo Cliente'}
                            </h3>
                            <button 
                                onClick={() => { setShowModal(false); setEditingCustomer(null); }}
                                className="text-2xl"
                                style={{ color: 'rgba(255,255,255,0.5)' }}
                            >
                                ×
                            </button>
                        </div>
                        <CustomerForm 
                            customer={editingCustomer}
                            onSave={handleSave}
                            onCancel={() => { setShowModal(false); setEditingCustomer(null); }}
                        />
                    </div>
                </div>
            )}
        </>
    );
};

const CardapioPage = () => {
    const [categories, setCategories] = useState([]);
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedCategoryId, setSelectedCategoryId] = useState(null);
    
    // Modais
    const [showCategoryModal, setShowCategoryModal] = useState(false);
    const [showItemModal, setShowItemModal] = useState(false);
    const [editingCategory, setEditingCategory] = useState(null);
    const [editingItem, setEditingItem] = useState(null);
    
    // Mensagem de feedback
    const [message, setMessage] = useState(null);
    
    // Busca dados
    const fetchData = async () => {
        try {
            const [catRes, itemsRes] = await Promise.all([
                authFetch(`${API_URL}/menu/categories`),
                authFetch(`${API_URL}/menu/items`)
            ]);
            
            if (catRes.ok) setCategories(await catRes.json());
            if (itemsRes.ok) setItems(await itemsRes.json());
        } catch (err) {
            console.error('Erro ao carregar cardápio:', err);
        }
        setLoading(false);
    };
    
    useEffect(() => {
        fetchData();
    }, []);
    
    // Auto-dismiss mensagem
    useEffect(() => {
        if (message) {
            const timer = setTimeout(() => setMessage(null), 3000);
            return () => clearTimeout(timer);
        }
    }, [message]);
    
    // Filtra itens por categoria
    const filteredItems = selectedCategoryId 
        ? items.filter(i => i.category_id === selectedCategoryId)
        : items;
    
    // === CRUD CATEGORIA ===
    const handleSaveCategory = async (data) => {
        try {
            const url = editingCategory 
                ? `${API_URL}/menu/categories/${editingCategory.id}`
                : `${API_URL}/menu/categories`;
            
            const res = await authFetch(url, {
                method: editingCategory ? 'PUT' : 'POST',
                body: JSON.stringify(data)
            });
            
            if (res.ok) {
                setMessage({ type: 'success', text: editingCategory ? 'Categoria atualizada!' : 'Categoria criada!' });
                setShowCategoryModal(false);
                setEditingCategory(null);
                fetchData();
            } else {
                const err = await res.json();
                setMessage({ type: 'error', text: err.detail || 'Erro ao salvar' });
            }
        } catch (err) {
            setMessage({ type: 'error', text: 'Erro de conexão' });
        }
    };
    
    const handleDeleteCategory = async (category) => {
        if (!confirm(`Excluir categoria "${category.name}"?`)) return;
        
        try {
            const res = await authFetch(`${API_URL}/menu/categories/${category.id}`, {
                method: 'DELETE'
            });
            
            if (res.ok) {
                setMessage({ type: 'success', text: 'Categoria excluída!' });
                if (selectedCategoryId === category.id) setSelectedCategoryId(null);
                fetchData();
            } else {
                const err = await res.json();
                setMessage({ type: 'error', text: err.detail || 'Erro ao excluir' });
            }
        } catch (err) {
            setMessage({ type: 'error', text: 'Erro de conexão' });
        }
    };
    
    // === CRUD ITEM ===
    const handleSaveItem = () => {
        setShowItemModal(false);
        setEditingItem(null);
        fetchData();
    };
    
    const handleDeleteItem = async (item) => {
        if (!confirm(`Excluir item "${item.name}"?`)) return;
        
        try {
            const res = await authFetch(`${API_URL}/menu/items/${item.id}`, {
                method: 'DELETE'
            });
            
            if (res.ok) {
                setMessage({ type: 'success', text: 'Item excluído!' });
                fetchData();
            } else {
                const err = await res.json();
                setMessage({ type: 'error', text: err.detail || 'Erro ao excluir' });
            }
        } catch (err) {
            setMessage({ type: 'error', text: 'Erro de conexão' });
        }
    };
    
    const handleToggleStock = async (item) => {
        try {
            const res = await authFetch(`${API_URL}/menu/items/${item.id}/toggle-stock`, {
                method: 'POST'
            });
            
            if (res.ok) {
                setMessage({ type: 'success', text: item.out_of_stock ? 'Item disponível!' : 'Item esgotado!' });
                fetchData();
            }
        } catch (err) {
            setMessage({ type: 'error', text: 'Erro de conexão' });
        }
    };
    
    // Loading state
    if (loading) {
        return (
            <div className="glass-card p-8 text-center">
                <div className="text-5xl mb-4">🍽️</div>
                <div style={{ color: 'rgba(255,255,255,0.5)' }}>Carregando cardápio...</div>
            </div>
        );
    }
    
    const totalItems = items.length;
    const outOfStock = items.filter(i => i.out_of_stock).length;
    
    return (
        <>
            {/* Mensagem de feedback */}
            {message && (
                <div 
                    className="mb-4 p-4 rounded-xl flex items-center gap-3"
                    style={{ 
                        background: message.type === 'success' ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                        border: `1px solid ${message.type === 'success' ? 'rgba(34, 197, 94, 0.4)' : 'rgba(239, 68, 68, 0.4)'}`
                    }}
                >
                    <span>{message.type === 'success' ? '✅' : '❌'}</span>
                    <span className="text-white">{message.text}</span>
                </div>
            )}
            
            {/* Header com stats */}
            <div className="glass-card p-4 mb-6">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <span className="text-3xl">🍽️</span>
                        <div>
                            <h2 className="text-lg font-semibold text-white">Cardápio</h2>
                            <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: '14px' }}>
                                {categories.length} categoria(s) • {totalItems} item(ns)
                                {outOfStock > 0 && <span style={{ color: '#ef4444' }}> • {outOfStock} esgotado(s)</span>}
                            </p>
                        </div>
                    </div>
                </div>
            </div>
            
            {/* Grid principal */}
            <div className="grid lg:grid-cols-3 gap-6">
                {/* Coluna Categorias */}
                <div className="lg:col-span-1">
                    <div className="glass-card p-4">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="font-semibold text-white">📂 Categorias</h3>
                            <button
                                onClick={() => { setEditingCategory(null); setShowCategoryModal(true); }}
                                className="px-3 py-1.5 rounded-lg text-sm font-medium text-white transition-all"
                                style={{ background: 'linear-gradient(135deg, #ff6b00 0%, #ff8c42 100%)' }}
                            >
                                + Nova
                            </button>
                        </div>
                        
                        {/* Botão "Todos" */}
                        <button
                            onClick={() => setSelectedCategoryId(null)}
                            className="w-full text-left p-3 rounded-xl mb-2 transition-all"
                            style={{ 
                                background: selectedCategoryId === null ? 'rgba(255, 107, 0, 0.2)' : 'rgba(255,255,255,0.05)',
                                border: selectedCategoryId === null ? '1px solid rgba(255, 107, 0, 0.4)' : '1px solid transparent'
                            }}
                        >
                            <span className="font-medium text-white">📋 Todos os itens</span>
                            <span className="text-xs ml-2" style={{ color: 'rgba(255,255,255,0.5)' }}>({totalItems})</span>
                        </button>
                        
                        {/* Lista de categorias */}
                        <div className="space-y-2">
                            {categories.map(cat => (
                                <div
                                    key={cat.id}
                                    className="group p-3 rounded-xl transition-all cursor-pointer"
                                    style={{ 
                                        background: selectedCategoryId === cat.id ? 'rgba(255, 107, 0, 0.2)' : 'rgba(255,255,255,0.05)',
                                        border: selectedCategoryId === cat.id ? '1px solid rgba(255, 107, 0, 0.4)' : '1px solid transparent'
                                    }}
                                    onClick={() => setSelectedCategoryId(cat.id)}
                                >
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <span className="font-medium text-white">{cat.name}</span>
                                            <span className="text-xs ml-2" style={{ color: 'rgba(255,255,255,0.5)' }}>
                                                ({cat.items_count || 0})
                                            </span>
                                        </div>
                                        <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <button
                                                onClick={(e) => { e.stopPropagation(); setEditingCategory(cat); setShowCategoryModal(true); }}
                                                className="p-1.5 rounded-lg hover:bg-white/10"
                                                title="Editar"
                                            >
                                                ✏️
                                            </button>
                                            <button
                                                onClick={(e) => { e.stopPropagation(); handleDeleteCategory(cat); }}
                                                className="p-1.5 rounded-lg hover:bg-red-500/20"
                                                title="Excluir"
                                            >
                                                🗑️
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                        
                        {categories.length === 0 && (
                            <div className="text-center py-6" style={{ color: 'rgba(255,255,255,0.5)' }}>
                                <div className="text-3xl mb-2">📂</div>
                                <p className="text-sm">Nenhuma categoria</p>
                                <p className="text-xs">Crie sua primeira categoria</p>
                            </div>
                        )}
                    </div>
                </div>
                
                {/* Coluna Itens */}
                <div className="lg:col-span-2">
                    <div className="glass-card p-4">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="font-semibold text-white">
                                🍔 Itens
                                {selectedCategoryId && (
                                    <span className="ml-2" style={{ color: '#ff8c42' }}>
                                        - {categories.find(c => c.id === selectedCategoryId)?.name}
                                    </span>
                                )}
                            </h3>
                            <button
                                onClick={() => { setEditingItem(null); setShowItemModal(true); }}
                                disabled={categories.length === 0}
                                className="px-3 py-1.5 rounded-lg text-sm font-medium text-white transition-all disabled:opacity-50"
                                style={{ background: 'linear-gradient(135deg, #ff6b00 0%, #ff8c42 100%)' }}
                                title={categories.length === 0 ? 'Crie uma categoria primeiro' : ''}
                            >
                                + Novo Item
                            </button>
                        </div>
                        
                        {/* Lista de itens */}
                        <div className="space-y-2">
                            {filteredItems.map(item => (
                                <div
                                    key={item.id}
                                    className="group p-4 rounded-xl transition-all flex items-center gap-4"
                                    style={{ 
                                        background: 'rgba(255,255,255,0.05)',
                                        opacity: item.out_of_stock ? 0.6 : 1
                                    }}
                                >
                                    {/* Foto do item */}
                                    <div 
                                        className="w-16 h-16 rounded-xl overflow-hidden flex-shrink-0 flex items-center justify-center"
                                        style={{ background: 'rgba(255,255,255,0.1)' }}
                                    >
                                        {item.image_url ? (
                                            <img 
                                                src={`${API_URL}${item.image_url}`} 
                                                alt={item.name}
                                                className="w-full h-full object-cover"
                                            />
                                        ) : (
                                            <span className="text-2xl" style={{ opacity: 0.3 }}>🍽️</span>
                                        )}
                                    </div>
                                    
                                    {/* Informações */}
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2">
                                            <span className="font-medium text-white truncate">{item.name}</span>
                                            {item.out_of_stock && (
                                                <span className="px-2 py-0.5 rounded-full text-xs" style={{ background: 'rgba(239,68,68,0.2)', color: '#ef4444' }}>
                                                    Esgotado
                                                </span>
                                            )}
                                        </div>
                                        {item.description && (
                                            <p className="text-sm mt-1 truncate" style={{ color: 'rgba(255,255,255,0.5)' }}>
                                                {item.description}
                                            </p>
                                        )}
                                        <div className="flex items-center gap-3 mt-2">
                                            <span className="font-semibold" style={{ color: '#4ade80' }}>
                                                R$ {(item.price || 0).toFixed(2)}
                                            </span>
                                            <span className="text-xs px-2 py-0.5 rounded-full" style={{ background: 'rgba(255,255,255,0.1)', color: 'rgba(255,255,255,0.6)' }}>
                                                {item.category_name}
                                            </span>
                                        </div>
                                    </div>
                                    
                                    {/* Ações */}
                                    <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <button
                                            onClick={() => handleToggleStock(item)}
                                            className="p-2 rounded-lg hover:bg-white/10"
                                            title={item.out_of_stock ? 'Marcar como disponível' : 'Marcar como esgotado'}
                                        >
                                            {item.out_of_stock ? '✅' : '⛔'}
                                        </button>
                                        <button
                                            onClick={() => { setEditingItem(item); setShowItemModal(true); }}
                                            className="p-2 rounded-lg hover:bg-white/10"
                                            title="Editar"
                                        >
                                            ✏️
                                        </button>
                                        <button
                                            onClick={() => handleDeleteItem(item)}
                                            className="p-2 rounded-lg hover:bg-red-500/20"
                                            title="Excluir"
                                        >
                                            🗑️
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                        
                        {filteredItems.length === 0 && (
                            <div className="text-center py-8" style={{ color: 'rgba(255,255,255,0.5)' }}>
                                <div className="text-4xl mb-2">🍔</div>
                                <p>Nenhum item {selectedCategoryId ? 'nesta categoria' : 'cadastrado'}</p>
                                {categories.length === 0 && (
                                    <p className="text-sm mt-1">Crie uma categoria primeiro</p>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            </div>
            
            {/* Modal Categoria */}
            {showCategoryModal && (
                <div className="modal-overlay" onClick={() => { setShowCategoryModal(false); setEditingCategory(null); }}>
                    <div className="modal-content" onClick={e => e.stopPropagation()}>
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="text-lg font-semibold text-white">
                                {editingCategory ? 'Editar Categoria' : 'Nova Categoria'}
                            </h3>
                            <button 
                                onClick={() => { setShowCategoryModal(false); setEditingCategory(null); }}
                                className="text-2xl"
                                style={{ color: 'rgba(255,255,255,0.5)' }}
                            >
                                ×
                            </button>
                        </div>
                        <CategoryForm 
                            category={editingCategory}
                            onSave={handleSaveCategory}
                            onCancel={() => { setShowCategoryModal(false); setEditingCategory(null); }}
                        />
                    </div>
                </div>
            )}
            
            {/* Modal Item */}
            {showItemModal && (
                <div className="modal-overlay" onClick={() => { setShowItemModal(false); setEditingItem(null); }}>
                    <div className="modal-content" onClick={e => e.stopPropagation()}>
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="text-lg font-semibold text-white">
                                {editingItem ? 'Editar Item' : 'Novo Item'}
                            </h3>
                            <button 
                                onClick={() => { setShowItemModal(false); setEditingItem(null); }}
                                className="text-2xl"
                                style={{ color: 'rgba(255,255,255,0.5)' }}
                            >
                                ×
                            </button>
                        </div>
                        <ItemForm 
                            item={editingItem}
                            categories={categories}
                            onSave={handleSaveItem}
                            onCancel={() => { setShowItemModal(false); setEditingItem(null); }}
                        />
                    </div>
                </div>
            )}
        </>
    );
};

// ============ RASTREAMENTO DE PEDIDOS ============

// Helper: Decodifica polyline do Google Maps
const decodePolyline = (encoded) => {
    if (!encoded) return [];
    const points = [];
    let index = 0;
    const len = encoded.length;
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

        points.push([lat / 1e5, lng / 1e5]);
    }
    return points;
};

// Modal de Rastreamento com Mapa
const TrackingModal = ({ order, onClose, restaurantData }) => {
    const [trackingDetails, setTrackingDetails] = React.useState(null);
    const [loading, setLoading] = React.useState(true);
    const mapRef = React.useRef(null);
    const mapInstanceRef = React.useRef(null);
    const courierMarkerRef = React.useRef(null);
    const isFirstRenderRef = React.useRef(true);

    // Buscar detalhes do rastreamento
    const fetchTrackingDetails = React.useCallback(async () => {
        try {
            const res = await authFetch(`${API_URL}/orders/${order.id}/tracking-details`);
            if (res.ok) {
                const data = await res.json();
                setTrackingDetails(data);
                setLoading(false);
            }
        } catch (error) {
            console.error('Erro ao buscar detalhes:', error);
            setLoading(false);
        }
    }, [order.id]);

    // Polling para atualização em tempo real (10 segundos)
    React.useEffect(() => {
        fetchTrackingDetails();
        const interval = setInterval(fetchTrackingDetails, 10000);
        return () => clearInterval(interval);
    }, [fetchTrackingDetails]);

    // Inicializar mapa (apenas UMA VEZ)
    React.useEffect(() => {
        if (!mapRef.current || !trackingDetails || mapInstanceRef.current) return;

        // Criar mapa
        const map = L.map(mapRef.current).setView(
            [restaurantData.lat || -23.5505, restaurantData.lng || -46.6333],
            13
        );

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);

        mapInstanceRef.current = map;

        // Se tem rota, desenhar no mapa
        if (trackingDetails.route?.polyline) {
            const points = decodePolyline(trackingDetails.route.polyline);
            if (points.length > 0) {
                L.polyline(points, {
                    color: '#60A5FA',
                    weight: 4,
                    opacity: 0.7
                }).addTo(map);
            }
        }

        // Marcador do restaurante
        const restaurantIcon = L.divIcon({
            className: 'custom-marker',
            html: `<div style="background: #FF6B00; color: white; width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 18px; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);">🏪</div>`,
            iconSize: [36, 36],
            iconAnchor: [18, 18]
        });

        L.marker([restaurantData.lat, restaurantData.lng], { icon: restaurantIcon })
            .addTo(map)
            .bindPopup('<b>Restaurante</b><br/>' + restaurantData.name);

        // Marcadores dos pedidos do lote (numerados)
        if (trackingDetails.batch?.orders) {
            trackingDetails.batch.orders.forEach((o, index) => {
                const isCurrentOrder = o.id === order.id;
                const markerIcon = L.divIcon({
                    className: 'custom-marker',
                    html: `<div style="background: ${isCurrentOrder ? '#F59E0B' : '#8B5CF6'}; color: white; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: bold; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);">${index + 1}</div>`,
                    iconSize: [32, 32],
                    iconAnchor: [16, 16]
                });

                L.marker([o.lat, o.lng], { icon: markerIcon })
                    .addTo(map)
                    .bindPopup(`<b>${index + 1}. ${o.customer_name}</b><br/>${o.address_text}${isCurrentOrder ? '<br/><span style="color: #F59E0B; font-weight: bold;">← VOCÊ ESTÁ AQUI</span>' : ''}`);
            });
        }

        // Ajustar zoom inicial para mostrar todos os pontos (APENAS UMA VEZ)
        const allPoints = [];
        allPoints.push([restaurantData.lat, restaurantData.lng]);
        if (trackingDetails.courier?.current_lat) {
            allPoints.push([trackingDetails.courier.current_lat, trackingDetails.courier.current_lng]);
        }
        if (trackingDetails.batch?.orders) {
            trackingDetails.batch.orders.forEach(o => allPoints.push([o.lat, o.lng]));
        }
        if (allPoints.length > 0) {
            const bounds = L.latLngBounds(allPoints);
            map.fitBounds(bounds, { padding: [50, 50] });
        }

        isFirstRenderRef.current = false;

        // Cleanup
        return () => {
            if (mapInstanceRef.current) {
                mapInstanceRef.current.remove();
                mapInstanceRef.current = null;
            }
            if (courierMarkerRef.current) {
                courierMarkerRef.current = null;
            }
        };
    }, [trackingDetails, restaurantData, order.id]);

    // Atualizar marcador do motoboy (quando GPS muda, SEM resetar zoom)
    React.useEffect(() => {
        if (!mapInstanceRef.current || !trackingDetails) return;

        const map = mapInstanceRef.current;

        // Remover marcador antigo do motoboy se existir
        if (courierMarkerRef.current) {
            map.removeLayer(courierMarkerRef.current);
        }

        // Adicionar marcador atualizado do motoboy (se disponível)
        if (trackingDetails.courier?.current_lat && trackingDetails.courier?.current_lng) {
            const courierIcon = L.divIcon({
                className: 'custom-marker',
                html: `<div style="background: #3B82F6; color: white; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 20px; border: 3px solid white; box-shadow: 0 4px 12px rgba(59,130,246,0.5); animation: pulse 2s infinite;">🏍️</div>`,
                iconSize: [40, 40],
                iconAnchor: [20, 20]
            });

            courierMarkerRef.current = L.marker(
                [trackingDetails.courier.current_lat, trackingDetails.courier.current_lng],
                { icon: courierIcon }
            )
                .addTo(map)
                .bindPopup(`<b>Motoboy</b><br/>${trackingDetails.courier.name}`);
        }
    }, [trackingDetails]);

    // Função para enviar por WhatsApp
    const handleSendWhatsApp = () => {
        if (!trackingDetails) return;

        const statusText = {
            'created': 'Pedido recebido',
            'preparing': 'Em preparo',
            'ready': 'Pronto',
            'assigned': 'Saiu para entrega',
            'picked_up': 'Saiu para entrega',
            'delivered': 'Entregue'
        }[trackingDetails.order.status] || 'Em processamento';

        const trackingUrl = `${window.location.origin}/track/${trackingDetails.order.tracking_code}`;
        const message = `Olá! Seu pedido #${trackingDetails.order.short_id} está ${statusText}. Acompanhe em tempo real: ${trackingUrl}`;

        window.open(`https://wa.me/?text=${encodeURIComponent(message)}`, '_blank');
    };

    if (loading) {
        return (
            <div className="modal-overlay" onClick={onClose}>
                <div className="modal-content" style={{ maxWidth: '900px', height: '80vh' }} onClick={e => e.stopPropagation()}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                        <div style={{ color: 'white', fontSize: '18px' }}>Carregando detalhes...</div>
                    </div>
                </div>
            </div>
        );
    }

    if (!trackingDetails) {
        return (
            <div className="modal-overlay" onClick={onClose}>
                <div className="modal-content" style={{ maxWidth: '900px' }} onClick={e => e.stopPropagation()}>
                    <div style={{ color: 'white', textAlign: 'center', padding: '40px' }}>
                        Erro ao carregar detalhes do pedido.
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" style={{ maxWidth: '900px', height: '85vh', overflowY: 'auto' }} onClick={e => e.stopPropagation()}>
                {/* Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                    <h3 style={{ fontSize: '20px', fontWeight: '700', color: 'white', fontFamily: 'Outfit, sans-serif' }}>
                        Pedido #{trackingDetails.order.short_id}
                    </h3>
                    <button
                        onClick={onClose}
                        style={{ fontSize: '28px', color: 'rgba(255,255,255,0.5)', background: 'none', border: 'none', cursor: 'pointer' }}
                    >
                        ×
                    </button>
                </div>

                {/* Mapa */}
                <div ref={mapRef} style={{
                    height: '350px',
                    borderRadius: '12px',
                    marginBottom: '24px',
                    border: '2px solid rgba(255,255,255,0.1)'
                }}></div>

                {/* Detalhes do Pedido */}
                <div style={{
                    background: 'rgba(255,255,255,0.05)',
                    padding: '20px',
                    borderRadius: '12px',
                    marginBottom: '16px'
                }}>
                    <h4 style={{ color: 'white', fontSize: '16px', fontWeight: '600', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span>📦</span>
                        <span>Detalhes do Pedido</span>
                    </h4>
                    <div style={{ display: 'grid', gap: '8px', color: 'rgba(255,255,255,0.7)', fontSize: '14px' }}>
                        <div><strong>Cliente:</strong> {trackingDetails.order.customer_name}</div>
                        <div><strong>Endereço:</strong> {trackingDetails.order.address_text}</div>
                        <div><strong>Status:</strong> <StatusBadge status={trackingDetails.order.status} /></div>
                        <div><strong>Código de Rastreio:</strong> {trackingDetails.order.tracking_code}</div>
                    </div>
                </div>

                {/* Informações do Motoboy */}
                {trackingDetails.courier && (
                    <div style={{
                        background: 'rgba(59,130,246,0.1)',
                        padding: '20px',
                        borderRadius: '12px',
                        marginBottom: '16px'
                    }}>
                        <h4 style={{ color: 'white', fontSize: '16px', fontWeight: '600', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span>🏍️</span>
                            <span>Motoboy</span>
                        </h4>
                        <div style={{ display: 'grid', gap: '8px', color: 'rgba(255,255,255,0.7)', fontSize: '14px' }}>
                            <div><strong>Nome:</strong> {trackingDetails.courier.name}</div>
                            {trackingDetails.courier.phone && <div><strong>Telefone:</strong> {trackingDetails.courier.phone}</div>}
                            {trackingDetails.batch && (
                                <div><strong>Posição na rota:</strong> {trackingDetails.batch.position}ª parada de {trackingDetails.batch.total}</div>
                            )}
                        </div>
                    </div>
                )}

                {/* Lista de Entregas do Lote */}
                {trackingDetails.batch?.orders && trackingDetails.batch.orders.length > 0 && (
                    <div style={{
                        background: 'rgba(139,92,246,0.1)',
                        padding: '20px',
                        borderRadius: '12px',
                        marginBottom: '16px'
                    }}>
                        <h4 style={{ color: 'white', fontSize: '16px', fontWeight: '600', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span>📍</span>
                            <span>Entregas do Lote</span>
                        </h4>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                            {trackingDetails.batch.orders.map((o, index) => {
                                const isCurrentOrder = o.id === order.id;
                                const isDelivered = o.status === 'delivered';
                                return (
                                    <div key={o.id} style={{
                                        padding: '12px',
                                        background: isCurrentOrder ? 'rgba(245,158,11,0.2)' : 'rgba(255,255,255,0.05)',
                                        borderRadius: '8px',
                                        borderLeft: isCurrentOrder ? '4px solid #F59E0B' : '4px solid transparent',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '12px'
                                    }}>
                                        <div style={{
                                            width: '28px',
                                            height: '28px',
                                            borderRadius: '50%',
                                            background: isDelivered ? '#10B981' : isCurrentOrder ? '#F59E0B' : '#8B5CF6',
                                            color: 'white',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            fontSize: '13px',
                                            fontWeight: 'bold'
                                        }}>
                                            {isDelivered ? '✓' : index + 1}
                                        </div>
                                        <div style={{ flex: 1 }}>
                                            <div style={{ color: 'white', fontSize: '14px', fontWeight: '500' }}>
                                                {o.customer_name}
                                                {isCurrentOrder && <span style={{ color: '#F59E0B', marginLeft: '8px', fontSize: '12px' }}>← VOCÊ ESTÁ AQUI</span>}
                                            </div>
                                            <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: '12px' }}>
                                                {o.address_text}
                                            </div>
                                        </div>
                                        <StatusBadge status={o.status} />
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}

                {/* Botão WhatsApp */}
                <button
                    onClick={handleSendWhatsApp}
                    style={{
                        width: '100%',
                        padding: '14px 20px',
                        background: '#25D366',
                        color: 'white',
                        border: 'none',
                        borderRadius: '12px',
                        fontSize: '15px',
                        fontWeight: '600',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '10px',
                        transition: 'all 0.2s'
                    }}
                    onMouseOver={e => e.currentTarget.style.background = '#20BA5A'}
                    onMouseOut={e => e.currentTarget.style.background = '#25D366'}
                >
                    <span style={{ fontSize: '20px' }}>📱</span>
                    <span>Enviar Link de Rastreamento por WhatsApp</span>
                </button>
            </div>
        </div>
    );
};

// Página de Rastreamento Principal
const TrackingPage = ({ restaurantData }) => {
    const [query, setQuery] = React.useState('');
    const [searching, setSearching] = React.useState(false);
    const [results, setResults] = React.useState([]);
    const [selectedOrder, setSelectedOrder] = React.useState(null);
    const [showModal, setShowModal] = React.useState(false);
    const searchTimeoutRef = React.useRef(null);

    // Buscar pedidos (com debounce)
    const handleSearch = async (value) => {
        setQuery(value);

        if (searchTimeoutRef.current) {
            clearTimeout(searchTimeoutRef.current);
        }

        if (value.trim().length < 2) {
            setResults([]);
            return;
        }

        searchTimeoutRef.current = setTimeout(async () => {
            setSearching(true);
            try {
                const res = await authFetch(`${API_URL}/orders/search?q=${encodeURIComponent(value)}`);
                if (res.ok) {
                    const data = await res.json();
                    setResults(data);
                } else {
                    setResults([]);
                }
            } catch (error) {
                console.error('Erro na busca:', error);
                setResults([]);
            }
            setSearching(false);
        }, 300);
    };

    // Selecionar pedido para ver detalhes
    const handleSelectOrder = (order) => {
        setSelectedOrder(order);
        setShowModal(true);
    };

    return (
        <>
            <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
                {/* Header */}
                <div style={{ marginBottom: '32px' }}>
                    <h1 style={{
                        fontSize: '32px',
                        fontWeight: '700',
                        color: 'white',
                        marginBottom: '8px',
                        fontFamily: 'Outfit, sans-serif'
                    }}>
                        📍 Rastreamento de Pedidos
                    </h1>
                    <p style={{ color: 'rgba(255,255,255,0.6)', fontSize: '15px' }}>
                        Busque pedidos por nome, telefone, #ID ou código de rastreio
                    </p>
                </div>

                {/* Campo de Busca */}
                <div className="glass-card" style={{ marginBottom: '24px', padding: '24px' }}>
                    <div style={{ position: 'relative' }}>
                        <input
                            type="text"
                            placeholder="Digite o nome do cliente, telefone, #1234 ou MF-ABC123..."
                            value={query}
                            onChange={(e) => handleSearch(e.target.value)}
                            style={{
                                width: '100%',
                                padding: '16px 50px 16px 20px',
                                background: 'rgba(255,255,255,0.1)',
                                border: '2px solid rgba(255,255,255,0.2)',
                                borderRadius: '12px',
                                color: 'white',
                                fontSize: '16px',
                                outline: 'none',
                                transition: 'all 0.2s'
                            }}
                            onFocus={(e) => e.target.style.borderColor = 'rgba(255,255,255,0.4)'}
                            onBlur={(e) => e.target.style.borderColor = 'rgba(255,255,255,0.2)'}
                        />
                        <div style={{
                            position: 'absolute',
                            right: '20px',
                            top: '50%',
                            transform: 'translateY(-50%)',
                            fontSize: '20px'
                        }}>
                            {searching ? '⏳' : '🔍'}
                        </div>
                    </div>
                </div>

                {/* Resultados da Busca */}
                {results.length > 0 && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                        {results.map(order => (
                            <div
                                key={order.id}
                                className="glass-card"
                                style={{
                                    padding: '20px',
                                    cursor: 'pointer',
                                    transition: 'all 0.2s'
                                }}
                                onClick={() => handleSelectOrder(order)}
                                onMouseOver={(e) => {
                                    e.currentTarget.style.transform = 'translateY(-2px)';
                                    e.currentTarget.style.background = 'rgba(255,255,255,0.12)';
                                }}
                                onMouseOut={(e) => {
                                    e.currentTarget.style.transform = 'translateY(0)';
                                    e.currentTarget.style.background = 'rgba(255,255,255,0.08)';
                                }}
                            >
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                    <div style={{ flex: 1 }}>
                                        <div style={{
                                            fontSize: '18px',
                                            fontWeight: '600',
                                            color: 'white',
                                            marginBottom: '8px',
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '12px'
                                        }}>
                                            <span style={{
                                                color: '#FF6B00',
                                                fontSize: '16px',
                                                fontWeight: '700'
                                            }}>
                                                #{order.short_id}
                                            </span>
                                            <span>{order.customer_name}</span>
                                        </div>
                                        <div style={{ color: 'rgba(255,255,255,0.6)', fontSize: '14px', marginBottom: '12px' }}>
                                            {order.address_text}
                                        </div>
                                        <div style={{ display: 'flex', gap: '16px', alignItems: 'center', flexWrap: 'wrap' }}>
                                            <StatusBadge status={order.status} />
                                            {order.batch_id && order.stop_order && (
                                                <span style={{
                                                    color: 'rgba(255,255,255,0.7)',
                                                    fontSize: '13px',
                                                    background: 'rgba(59,130,246,0.2)',
                                                    padding: '4px 12px',
                                                    borderRadius: '12px'
                                                }}>
                                                    📍 {order.stop_order}ª parada
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                    <div style={{
                                        color: '#FF6B00',
                                        fontSize: '24px',
                                        marginLeft: '16px'
                                    }}>
                                        →
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {/* Mensagem quando não há resultados */}
                {query.length >= 2 && !searching && results.length === 0 && (
                    <div className="glass-card" style={{ padding: '40px', textAlign: 'center' }}>
                        <div style={{ fontSize: '48px', marginBottom: '16px' }}>🔍</div>
                        <div style={{ color: 'white', fontSize: '18px', fontWeight: '600', marginBottom: '8px' }}>
                            Nenhum pedido encontrado
                        </div>
                        <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: '14px' }}>
                            Tente buscar por nome do cliente, telefone, #ID ou código MF-
                        </div>
                    </div>
                )}

                {/* Mensagem inicial */}
                {query.length === 0 && (
                    <div className="glass-card" style={{ padding: '40px', textAlign: 'center' }}>
                        <div style={{ fontSize: '48px', marginBottom: '16px' }}>🔍</div>
                        <div style={{ color: 'white', fontSize: '18px', fontWeight: '600', marginBottom: '8px' }}>
                            Comece digitando para buscar
                        </div>
                        <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: '14px' }}>
                            Você pode buscar por:
                        </div>
                        <div style={{
                            color: 'rgba(255,255,255,0.7)',
                            fontSize: '14px',
                            marginTop: '12px',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '4px',
                            alignItems: 'center'
                        }}>
                            <div>• Nome do cliente (ex: "Maria Silva")</div>
                            <div>• Telefone (ex: "11999999999")</div>
                            <div>• ID do pedido (ex: "#1234")</div>
                            <div>• Código de rastreio (ex: "MF-ABC123")</div>
                        </div>
                    </div>
                )}
            </div>

            {/* Modal de Detalhes */}
            {showModal && selectedOrder && (
                <TrackingModal
                    order={selectedOrder}
                    restaurantData={restaurantData}
                    onClose={() => {
                        setShowModal(false);
                        setSelectedOrder(null);
                    }}
                />
            )}
        </>
    );
};

// ============ PÁGINAS PLACEHOLDER ============

const PlaceholderPage = ({ title, icon }) => (
    <div className="glass-card p-8 text-center">
        <div className="text-6xl mb-4">{icon}</div>
        <h2 className="text-2xl font-bold text-white mb-2" style={{ fontFamily: 'Outfit, sans-serif' }}>{title}</h2>
        <p style={{ color: 'rgba(255,255,255,0.5)' }}>
            Esta funcionalidade será implementada em breve!
        </p>
    </div>
);

// ============ APP PRINCIPAL ============

