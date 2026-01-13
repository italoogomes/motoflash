# 🏍️ MotoFlash - Sistema de Despacho Inteligente

Sistema de despacho inteligente para restaurantes com entregadores próprios.

## 🎯 O que esse sistema faz

1. **Gerencia pedidos** com QR Code para rastrear quando ficam prontos
2. **Agrupa pedidos** por proximidade geográfica (clustering)
3. **Distribui automaticamente** para motoqueiros disponíveis
4. **Calcula rotas** otimizadas para cada entrega

## 🚀 Como rodar

### Passo 1: Instalar dependências do Python

```bash
cd backend
pip install -r requirements.txt
```

### Passo 2: Rodar o backend

```bash
cd backend
uvicorn main:app --reload
```

O servidor vai rodar em `http://localhost:8000`

- Documentação da API: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### Passo 3: Abrir o frontend

Basta abrir o arquivo `frontend/index.html` no navegador!

O frontend conecta automaticamente no backend em localhost:8000.

## 🧪 Como testar

1. **Adicione alguns motoboys** (ex: João, Maria, Pedro)
2. **Ative os motoboys** clicando em "Ativar"
3. **Crie alguns pedidos** usando o simulador
4. **Bipe os pedidos** (simula o QR code sendo lido quando fica pronto)
5. **Execute o Dispatch** para distribuir os pedidos para os motoboys
6. **Finalize as entregas** clicando em "Finalizar" no motoboy

## 📁 Estrutura do Projeto

```
motoboy-app/
├── backend/
│   ├── main.py              # Ponto de entrada FastAPI
│   ├── models.py            # Modelos de dados (Order, Courier, Batch)
│   ├── database.py          # Configuração SQLite
│   ├── requirements.txt     # Dependências Python
│   ├── routers/
│   │   ├── orders.py        # Endpoints de pedidos
│   │   ├── couriers.py      # Endpoints de motoqueiros
│   │   └── dispatch.py      # Endpoints do algoritmo de dispatch
│   └── services/
│       ├── qrcode_service.py    # Geração de QR Code
│       └── dispatch_service.py  # Algoritmo de distribuição
├── frontend/
│   ├── index.html           # Interface web (standalone)
│   └── App.jsx              # Componente React (para projeto completo)
└── README.md
```

## 🔧 API Endpoints

### Pedidos
- `POST /orders` - Criar pedido
- `GET /orders` - Listar pedidos
- `GET /orders/{id}` - Buscar pedido
- `GET /orders/{id}/qrcode` - Gerar QR Code
- `POST /orders/{id}/scan` - Bipar QR (marca como PRONTO)
- `POST /orders/{id}/pickup` - Marcar como coletado
- `POST /orders/{id}/deliver` - Marcar como entregue

### Motoqueiros
- `POST /couriers` - Cadastrar motoqueiro
- `GET /couriers` - Listar motoqueiros
- `POST /couriers/{id}/available` - Marcar como disponível
- `POST /couriers/{id}/offline` - Marcar como offline
- `GET /couriers/{id}/current-batch` - Ver entregas atuais
- `POST /couriers/{id}/complete-batch` - Finalizar entregas

### Dispatch
- `POST /dispatch/run` - Executar algoritmo de distribuição
- `GET /dispatch/batches` - Ver lotes ativos
- `GET /dispatch/stats` - Estatísticas do sistema

## ⚙️ Configurações do Algoritmo (V0.1)

No arquivo `backend/services/dispatch_service.py`:

```python
# Janela de tempo: pedidos prontos nos últimos X minutos
READY_WINDOW_MINUTES = 7

# Raio máximo para agrupar pedidos (km)
MAX_CLUSTER_RADIUS_KM = 3.0

# Máximo de pedidos por motoqueiro
MAX_ORDERS_PER_COURIER = 2

# Se tem motoboys sobrando, prefere 1 pedido por motoboy
PREFER_SINGLE_DELIVERY = True
```

## 🔮 Próximos passos (V0.2)

- [ ] App mobile para motoqueiro (React Native)
- [ ] Integração com Google Maps para rotas reais
- [ ] Tempo médio de preparo por tipo de pedido
- [ ] Alertas de fila cheia
- [ ] Dashboard com métricas históricas
- [ ] Leitor de QR Code real na câmera
- [ ] Integração com WhatsApp para pedidos

## 📝 Licença

Projeto pessoal - MVP para validação de ideia.
