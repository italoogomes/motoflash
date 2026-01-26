# 🏗️ Arquitetura do MotoFlash

**Versão:** 0.9.0
**Última atualização:** 2026-01-25

---

## 📊 Visão Geral

O MotoFlash é um **sistema SaaS multi-tenant** de gerenciamento de entregas para restaurantes com frota própria de motoboys. O sistema utiliza um algoritmo inteligente para agrupar pedidos próximos e otimizar rotas.

### Tipo de Arquitetura
- **Monolito Full-Stack** com API REST
- **Frontend:** HTML + React (CDN) + Tailwind CSS
- **Backend:** Python FastAPI
- **Banco:** SQLite (com suporte para migração para PostgreSQL)

---

## 🛠️ Stack Tecnológico

### Backend
| Tecnologia | Versão | Finalidade |
|------------|--------|-----------|
| **Python** | 3.11+ | Linguagem principal |
| **FastAPI** | 0.109+ | Framework web (REST API) |
| **SQLModel** | 0.0.14+ | ORM (SQLAlchemy + Pydantic) |
| **SQLite** | 3.x | Banco de dados (produção MVP) |
| **Uvicorn** | 0.27+ | ASGI server |
| **bcrypt** | 4.0+ | Hash de senhas |
| **python-jose** | 3.3+ | JWT tokens |
| **httpx** | 0.26+ | Cliente HTTP (Google Maps API) |
| **qrcode** | 7.4+ | Geração de QR Codes |
| **slowapi** | 0.1.9+ | Rate limiting |

### Frontend
| Tecnologia | Versão | Finalidade |
|------------|--------|-----------|
| **React** | 18 | UI library (via CDN) |
| **Babel Standalone** | 7.x | JSX compilation no browser |
| **Tailwind CSS** | 3.x | Framework CSS (via CDN) |
| **Leaflet.js** | 1.9+ | Mapas interativos |
| **Vanilla JavaScript** | ES6+ | Lógica do frontend |

### Serviços Externos
- **Google Maps API** (Geocoding + Directions)
- **Firebase Cloud Messaging** (Push notifications - planejado)

---

## 📁 Estrutura de Pastas

```
motoflash/
├── backend/                    # Aplicação FastAPI
│   ├── main.py                # Ponto de entrada (uvicorn)
│   ├── database.py            # Configuração do SQLite
│   ├── models.py              # Modelos de dados (SQLModel)
│   ├── requirements.txt       # Dependências Python
│   ├── .env.example          # Template de variáveis de ambiente
│   │
│   ├── routers/              # Endpoints da API (por domínio)
│   │   ├── auth.py           # Autenticação (login, register)
│   │   ├── orders.py         # Pedidos (CRUD + QR Code)
│   │   ├── couriers.py       # Motoboys (CRUD + login)
│   │   ├── dispatch.py       # Algoritmo de despacho
│   │   ├── menu.py           # Cardápio (categorias + itens)
│   │   ├── customers.py      # Clientes (cache de endereços)
│   │   ├── invites.py        # Convites para motoboys
│   │   └── settings.py       # Configurações (legacy)
│   │
│   ├── services/             # Lógica de negócio
│   │   ├── auth_service.py   # JWT + bcrypt
│   │   ├── dispatch_service.py # Algoritmo de agrupamento V0.9
│   │   ├── geocoding_service.py # Google Maps Geocoding
│   │   ├── alerts_service.py  # Sistema de alertas (não integrado)
│   │   ├── metrics_service.py # Métricas (não integrado)
│   │   ├── push_service.py    # Push notifications (stub)
│   │   └── qrcode_service.py  # Geração de QR Codes
│   │
│   ├── static/               # Frontend HTML/CSS/JS
│   │   ├── index.html        # Dashboard principal (React)
│   │   ├── motoboy.html      # App PWA dos motoboys
│   │   ├── auth.html         # Login/Cadastro
│   │   ├── cardapio.html     # Gestão de cardápio
│   │   ├── clientes.html     # Gestão de clientes
│   │   ├── convite.html      # Página de aceite de convite
│   │   ├── recuperar-senha.html # Reset de senha
│   │   ├── manifest.json     # PWA manifest
│   │   ├── sw.js            # Service Worker (offline)
│   │   └── icons/           # Ícones PWA
│   │
│   └── uploads/              # Imagens (não versionado)
│       └── .gitkeep
│
├── docs/                     # Documentação técnica
│   ├── ARQUITETURA.md       # Este arquivo
│   ├── API_ENDPOINTS.md     # Referência da API
│   ├── FLUXOS.md            # Fluxos de dados
│   └── FRONTEND_BACKEND.md  # Comunicação F↔B
│
├── RAILWAY_SETUP.md         # Guia de deploy no Railway
├── README.md                # Documentação principal
└── LICENSE                  # MIT License
```

---

## 🗄️ Arquitetura do Banco de Dados

### Tecnologia
- **SQLite** em produção (MVP)
- Arquivo: `/data/motoboy.db` (Railway/Render) ou local
- ORM: **SQLModel** (SQLAlchemy + Pydantic)

### Principais Tabelas

| Tabela | Descrição | Chave Estrangeira |
|--------|-----------|-------------------|
| `restaurants` | Dados dos restaurantes (multi-tenant) | - |
| `users` | Usuários do dashboard (OWNER/MANAGER) | `restaurant_id` |
| `couriers` | Motoboys | `restaurant_id` |
| `orders` | Pedidos de entrega | `restaurant_id`, `batch_id` |
| `batches` | Lotes de entrega | `restaurant_id`, `courier_id` |
| `customers` | Cache de clientes/endereços | `restaurant_id` |
| `categories` | Categorias do cardápio | `restaurant_id` |
| `menu_items` | Itens do cardápio | `restaurant_id`, `category_id` |
| `invites` | Códigos de convite para motoboys | `restaurant_id` |
| `password_resets` | Tokens de reset de senha | `courier_id` |

### Isolamento Multi-Tenant
**Estratégia:** Todos os endpoints filtram por `restaurant_id` automaticamente.

```python
# Exemplo de query com isolamento
orders = session.exec(
    select(Order).where(Order.restaurant_id == restaurant_id)
).all()
```

---

## 🔐 Autenticação e Autorização

### Autenticação
- **JWT Tokens** (JSON Web Token)
- **Algoritmo:** HS256
- **Expiração:** 24 horas
- **Storage:** localStorage (frontend)

### Fluxo JWT
1. Usuário faz login (`POST /auth/login`)
2. Backend valida credenciais (bcrypt)
3. Backend gera JWT token assinado
4. Frontend armazena token em `localStorage`
5. Todas requisições incluem header: `Authorization: Bearer <token>`

### Tipos de Usuário

| Tipo | Autenticação | Permissões |
|------|--------------|-----------|
| **User (OWNER)** | JWT token | Acesso total ao dashboard |
| **User (MANAGER)** | JWT token | Acesso limitado (sem configurações) |
| **Courier (Motoboy)** | Sem JWT* | Login por phone + senha |

*Motoboys usam um sistema de autenticação simplificado sem JWT (retorna dados diretamente).

---

## 🧩 Componentes Principais

### 1. Dashboard (index.html)
**URL:** `/` ou `/dashboard`
**Tecnologia:** React 18 (inline, via CDN)
**Responsabilidade:**
- Visualizar pedidos em tempo real
- Criar novos pedidos
- Executar dispatch (agrupar pedidos)
- Visualizar lotes em andamento
- Mapas com rotas (Leaflet.js)

### 2. App Motoboy (motoboy.html)
**URL:** `/motoboy`
**Tecnologia:** React 18 + PWA (offline-first)
**Responsabilidade:**
- Login de motoboy
- Aceitar lotes de entrega
- Visualizar rota no mapa
- Marcar pedidos como entregues
- GPS em tempo real

### 3. Gestão de Cardápio (cardapio.html)
**URL:** `/cardapio`
**Tecnologia:** React 18
**Responsabilidade:**
- Criar/editar categorias
- Criar/editar itens do menu
- Upload de imagens
- Controle de estoque (disponível/indisponível)

### 4. Gestão de Clientes (clientes.html)
**URL:** `/clientes`
**Tecnologia:** React 18
**Responsabilidade:**
- Listar clientes
- Adicionar novos clientes
- Cache de endereços com coordenadas

### 5. API REST (FastAPI)
**URL Base:** `/` (mesma origem)
**Documentação:** `/docs` (Swagger UI)
**Responsabilidade:**
- Endpoints CRUD
- Lógica de negócio
- Autenticação
- Dispatch inteligente

---

## 🚀 Algoritmo de Dispatch (Coração do Sistema)

**Localização:** `backend/services/dispatch_service.py`
**Versão:** V0.9

### Funcionamento

```
1. BUSCAR pedidos READY (prontos para sair)
2. BUSCAR motoboys AVAILABLE (disponíveis)
3. AGRUPAR pedidos do MESMO endereço (nunca separa)
4. AGRUPAR pedidos PRÓXIMOS (até 3km de raio)
5. CALCULAR distância REAL por rota (Google Directions API)
6. ORDENAR pedidos pela distância (mais perto primeiro)
7. ATRIBUIR lotes aos motoboys
8. ADICIONAR pedidos órfãos nas rotas existentes (otimização)
9. GERAR polyline da rota (Google Maps)
10. ATUALIZAR status: motoboy → BUSY, pedidos → ASSIGNED
```

### Configurações
```python
SAME_ADDRESS_THRESHOLD_KM = 0.05  # 50 metros
MAX_CLUSTER_RADIUS_KM = 3.0       # 3 km
PREFERRED_ORDERS_PER_COURIER = 4  # Ideal
MAX_ABSOLUTE_ORDERS = 6           # Máximo
```

---

## 🗺️ Integração Google Maps

### APIs Utilizadas
1. **Geocoding API** - Converte endereços → coordenadas
2. **Directions API** - Calcula rotas e distâncias reais
3. **Polyline Encoding** - Desenha rotas nos mapas

### Fluxo de Geocoding
```
Usuário insere endereço
    ↓
Backend: geocoding_service.py
    ↓
Cache local (verifica se já existe)
    ↓
Se não existe: chama Google Geocoding API
    ↓
Armazena lat/lng no banco (Order ou Customer)
```

### Otimização
- **Cache em memória** durante execução
- **Cache no banco** para endereços de clientes
- Evita chamadas repetidas à API do Google

---

## 🌐 PWA (Progressive Web App)

### Características
- **Instalável** em Android/iOS
- **Offline-first** com Service Worker
- **Ícones customizados** (192px, 512px)
- **Manifest.json** configurado

### Service Worker (sw.js)
```javascript
// Versão básica - cache de assets estáticos
// Permite uso offline do app motoboy
```

**Nota:** Sincronização offline não implementada (v0.9).

---

## 📊 Fluxo de Dados (Resumido)

### Criar Pedido
```
Dashboard → POST /orders → Backend valida → Geocoding → Salva no DB → QR Code gerado → Retorna pedido
```

### Executar Dispatch
```
Dashboard → POST /dispatch/run → Algoritmo agrupa pedidos → Cria batches → Atribui motoboys → Push notification
```

### Motoboy Entrega
```
App Motoboy → POST /orders/{id}/deliver → Atualiza status → Se último pedido → Finaliza batch → Motoboy fica AVAILABLE
```

---

## 🔒 Segurança

### Implementado
- ✅ JWT tokens com expiração
- ✅ Senhas com bcrypt (salt rounds)
- ✅ Rate limiting (10 logins/min)
- ✅ CORS configurável
- ✅ API keys em variáveis de ambiente
- ✅ Validação de entrada (Pydantic)
- ✅ Isolamento multi-tenant por restaurant_id

### A Implementar
- [ ] HTTPS obrigatório (Railway fornece)
- [ ] Validação de CNPJ
- [ ] Audit logging
- [ ] 2FA para usuários críticos

---

## 📈 Escalabilidade

### Limitações Atuais (SQLite)
- **Máx. restaurantes recomendado:** ~50
- **Máx. pedidos simultâneos:** ~500
- **Sem transações distribuídas**

### Migração Futura (PostgreSQL)
Quando necessário:
1. Trocar connection string
2. Ajustar tipos de dados específicos
3. Implementar migrations (Alembic)
4. Configurar connection pooling

---

## 🧪 Testes

**Status:** Não implementado (v0.9)

**Planejado:**
- Unit tests (pytest)
- Integration tests (TestClient FastAPI)
- E2E tests (Playwright/Selenium)

---

## 📦 Deploy

### Ambiente de Produção: Railway
- **Runtime:** Python 3.11
- **Banco:** SQLite em volume persistente (`/data`)
- **Build:** Automático via Nixpacks
- **Variáveis de ambiente:** 4 obrigatórias

Ver: [RAILWAY_SETUP.md](../RAILWAY_SETUP.md)

---

## 🔄 Versionamento

| Versão | Data | Mudanças |
|--------|------|----------|
| 0.9.0 | 2026-01 | Polyline de rotas + Segurança |
| 0.8.0 | 2025-12 | Algoritmo dispatch otimizado |
| 0.7.0 | 2025-11 | Multi-tenant + Trial system |
| 0.6.0 | 2025-10 | PWA motoboy |

---

## 📞 Contato Técnico

Para dúvidas sobre arquitetura, consulte:
- [API_ENDPOINTS.md](./API_ENDPOINTS.md) - Referência completa da API
- [FLUXOS.md](./FLUXOS.md) - Diagramas de fluxo
- [FRONTEND_BACKEND.md](./FRONTEND_BACKEND.md) - Comunicação F↔B
