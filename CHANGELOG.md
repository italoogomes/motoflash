# 📝 Changelog - MotoFlash

Todas as mudanças notáveis do projeto serão documentadas neste arquivo.

---

## [1.2.0] - 2026-01-28

### 🏷️ IDs Amigáveis para Pedidos

#### ✨ Adicionado
- **short_id** - Número sequencial por restaurante (#1001, #1002, ...)
  - Facilita comunicação com clientes
  - Exibido em destaque nos cards do dashboard
  - Sequencial e independente por restaurante

- **tracking_code** - Código único de rastreio (MF-ABC123)
  - Formato: "MF-" + 6 caracteres alfanuméricos
  - Único globalmente no sistema
  - Permite rastreamento público sem autenticação

- **Endpoint Público de Rastreio**
  - `GET /orders/track/{tracking_code}` - Rastreio sem autenticação
  - Retorna informações básicas do pedido (status, timestamps, cliente)
  - Ideal para compartilhar com clientes

#### 🛠️ Modificado
- `Order` model - Adicionados campos `short_id` e `tracking_code`
- `OrderResponse` schema - Inclui novos campos na API
- `OrderTrackingResponse` schema - Novo schema para rastreio público
- Frontend - Cards exibem #short_id e código de rastreio
- Mensagem de sucesso - Mostra IDs após criar pedido

#### 📦 Novos Arquivos
- `backend/services/order_service.py` - Funções helper para gerar IDs
  - `generate_short_id(restaurant_id, session)` - Gera short_id sequencial
  - `ensure_unique_tracking_code(session)` - Gera tracking_code único

#### 🧪 Testes
- **7 novos testes** adicionados (92 total)
  - Pedido criado com short_id
  - Pedido criado com tracking_code
  - Short_id sequencial por restaurante
  - Tracking_code único
  - Endpoint de rastreio público
  - Endpoint de rastreio com código inválido
  - Short_id independente por restaurante

#### 📚 Documentação
- Atualizado `CHANGELOG.md` com v1.2.0
- Atualizado `PROGRESSO_SESSAO.md` com implementação completa

---

## [1.1.0] - 2026-01-28

### 🔮 Sistema de Previsão Híbrida de Motoboys

#### ✨ Adicionado
- **Modelo Híbrido de Previsão**
  - Combina dados históricos (últimas 4 semanas) com situação em tempo real
  - Analisa padrões por dia da semana e hora
  - Balanceamento de fluxo (teoria de filas)

- **Novos Endpoints**
  - `GET /dispatch/previsao` - Previsão híbrida completa
  - `POST /dispatch/atualizar-padroes` - Atualiza padrões históricos
  - `GET /dispatch/padroes` - Lista padrões aprendidos

- **Novos Arquivos**
  - `backend/models.py` - Models `PadraoDemanda` e `PrevisaoHibrida`
  - `backend/services/prediction_service.py` - Serviço de previsão
  - `backend/tests/test_prediction.py` - 15 testes do sistema

#### 🎯 Funcionalidades
- **Aprendizado Histórico**: Analisa pedidos entregues das últimas 4 semanas
- **Balanceamento de Fluxo**: Detecta quando `taxa_preparo > taxa_entrega`
- **Alertas Inteligentes**: Avisa quando demanda está acima/abaixo do normal
- **Recomendação em Tempo Real**: Sugere quantidade ideal de motoboys

#### 🧪 Testes
- **15 novos testes** adicionados (85 total)
  - Endpoint de previsão (4 testes)
  - Atualização de padrões (3 testes)
  - Listagem de padrões (2 testes)
  - Isolamento multi-tenant (2 testes)
  - Balanceamento de fluxo (2 testes)
  - Comparação histórico vs atual (2 testes)

#### 📚 Documentação
- Atualizado `docs/API_ENDPOINTS.md` com novos endpoints
- Atualizado `docs/TESTES.md` com seção de testes de previsão
- Atualizado `PROGRESSO_SESSAO.md` com v1.1.0

---

## [1.0.5] - 2026-01-26

### ✅ Estabilidade dos Testes - 100% de Aprovação

#### 🐛 Corrigido
- **9 testes falhando corrigidos**
  - test_auth.py: 5 testes (mensagens de erro, payloads, estruturas de resposta)
  - test_dispatch.py: 2 testes (máximo de pedidos/lote, imports)
  - test_orders.py: 2 testes (slug obrigatório, campos de modelo)

#### 🎯 Resultado
- **70/70 testes passando (100%)**
- Tempo de execução: 47.93s
- Warnings: 37 deprecation warnings (não críticos)

#### 📚 Documentação
- Atualizado `docs/TESTES.md` com detalhes das correções
- Adicionado histórico de estabilidade
- Documentado cada correção com problema/solução

#### 🔧 Melhorias Técnicas
- Mensagens de erro mais seguras (não revelam se email existe)
- Validação de campos obrigatórios (`slug` em Restaurant)
- Correção de imports e nomes de funções
- Alinhamento de schemas com modelos do banco

---

## [1.0.4] - 2026-01-26

### 🧪 Testes de Motoboys

#### ✨ Adicionado
- **Testes de Motoboys** (33 testes)
  - `tests/test_couriers.py` - Testes completos de motoboys
  - Cobertura: autenticação, CRUD, status, lote atual, localização, recuperação de senha, rotas de entrega
  - Testes de isolamento multi-tenant

#### 🎯 Cobertura Expandida (70 testes total)
- ✅ **Autenticação** (6 testes): login com sucesso/erros, senha, telefone inválido
- ✅ **CRUD** (9 testes): criar, listar, buscar, excluir, filtros, isolamento
- ✅ **Status** (3 testes): available, offline, validação de entregas pendentes
- ✅ **Lote Atual** (4 testes): buscar, completar, validações
- ✅ **Localização** (3 testes): atualizar GPS, push token, dados do restaurante
- ✅ **Recuperação de Senha** (6 testes): gerar link, validar código, redefinir senha
- ✅ **Rotas de Entrega** (3 testes): coletar, entregar, validação de batch

#### 🔧 Correções
- Corrigido fixture `test_courier` em conftest.py (`password_hash` em vez de `hashed_password`)
- Corrigido testes para usar `password_hash` consistentemente

#### 📚 Documentação
- Atualizado `docs/TESTES.md` com seção completa de testes de motoboys
- Atualizado `CHANGELOG.md`, `README.md` e `docs/ARQUITETURA.md`
- Atualizado `PROGRESSO_SESSAO.md` com v1.0.4

---

## [1.0.3] - 2026-01-26

### 🧪 Testes de Dispatch

#### ✨ Adicionado
- **Testes de Dispatch** (14 testes)
  - `tests/test_dispatch.py` - Testes completos do algoritmo de dispatch
  - Fixtures `test_orders_ready` e `test_couriers_available` em conftest.py
  - Cobertura: execução básica, agrupamento, atribuição, isolamento multi-tenant

#### 🎯 Cobertura Expandida (38 testes total)
- ✅ Execução básica do dispatch (com/sem pedidos, com/sem motoboys, autenticação)
- ✅ Agrupamento de pedidos próximos (< 3km) e respeito ao limite de 6 por lote
- ✅ Atribuição de motoboys (status BUSY) e pedidos (status ASSIGNED)
- ✅ Criação de batches com dados corretos e ordem de paradas sequencial
- ✅ Isolamento multi-tenant (pedidos e motoboys de outros restaurantes)
- ✅ Endpoints de listagem e estatísticas

#### 📚 Documentação
- Atualizado `docs/TESTES.md` com documentação completa dos testes de dispatch
- Atualizado `CHANGELOG.md`, `README.md` e `docs/ARQUITETURA.md`

---

## [1.0.2] - 2026-01-26

### 🧪 Testes de Pedidos

#### ✨ Adicionado
- **Testes de Pedidos** (16 testes)
  - `tests/test_orders.py` - Testes completos de pedidos
  - Fixture `test_order` em conftest.py
  - Cobertura: criação, listagem, busca, QR Code, transições de status
  - Validação de isolamento multi-tenant

#### 🎯 Cobertura Expandida
- ✅ Criação de pedidos (com/sem coordenadas)
- ✅ Listagem e filtros
- ✅ Isolamento entre restaurantes
- ✅ Geração de QR Code
- ✅ Transições de status (CREATED → PREPARING → READY)
- ✅ Validação de transições inválidas

---

## [1.0.1] - 2026-01-26

### 🧪 Testes Automatizados

#### ✨ Adicionado
- **Framework pytest** configurado
  - `tests/conftest.py` - Fixtures compartilhadas
  - `tests/test_auth.py` - 8 testes de autenticação
  - `pytest>=7.4.0` + `pytest-asyncio>=0.21.0`

- **Documentação de Testes**
  - `docs/TESTES.md` - Guia completo de testes
  - Como executar testes
  - Como escrever novos testes
  - Boas práticas

#### 🎯 Cobertura
- ✅ Autenticação (login, registro, /me)
- ✅ Pedidos (16 testes)
- 🔄 Dispatch (planejado)
- 🔄 Motoboys (planejado)

---

## [1.0.0] - 2026-01-26

### 🎉 Arquitetura Modular Frontend

#### ✨ Adicionado
- **Estrutura modular** para o dashboard
  - `css/dashboard.css` - Todos os estilos (556 linhas)
  - `js/utils/helpers.js` - Funções utilitárias (43 linhas)
  - `js/components.js` - Componentes React (2907 linhas)
  - `js/app.js` - Componente App principal (192 linhas)

- **Nova documentação**
  - `docs/ARQUITETURA_MODULAR.md` - Guia completo da arquitetura modular
  - Seções atualizadas em ARQUITETURA.md e FRONTEND_BACKEND.md

#### 🔄 Modificado
- **index.html** - Refatorado de 3732 linhas para 36 linhas
- **main.py** - Removidas rotas obsoletas (/cardapio, /clientes)
- **Navegação** - Link interno corrigido para usar SPA

#### ❌ Removido
- `cardapio.html` - Integrado ao index.html
- `clientes.html` - Integrado ao index.html
- `cadastro.html` - Substituído por auth.html
- `login.html` - Substituído por auth.html
- `dashboard-preview.html` - Arquivo de teste removido

#### 📦 Deploy
- ✅ Compatível com Railway (sem mudanças necessárias)
- ✅ Mantém SPA (navegação suave)
- ✅ Cache de CSS/JS melhorado

---

## [0.9.0] - 2026-01

### ✨ Adicionado
- Polyline de rotas reais (Google Directions API)
- Melhorias de segurança

### 🔄 Modificado
- Algoritmo de dispatch otimizado com rotas reais

---

## [0.8.0] - 2025-12

### ✨ Adicionado
- Firebase Cloud Messaging (Push Notifications)
- Service Worker para notificações em background

### 🔄 Modificado
- Algoritmo de dispatch com agrupamento inteligente

---

## [0.7.0] - 2025-11

### ✨ Adicionado
- Sistema multi-tenant (SaaS)
- Trial de 14 dias para novos restaurantes
- Planos (TRIAL, BASIC, PRO)

### 🔄 Modificado
- Autenticação com JWT
- Isolamento de dados por restaurant_id

---

## [0.6.0] - 2025-10

### ✨ Adicionado
- PWA para motoboys (App instalável)
- Service Worker para offline
- Manifest.json

---

## Tipos de Mudança

- `✨ Adicionado` - Novas funcionalidades
- `🔄 Modificado` - Mudanças em funcionalidades existentes
- `🐛 Corrigido` - Correções de bugs
- `❌ Removido` - Funcionalidades removidas
- `🔒 Segurança` - Melhorias de segurança
- `📦 Deploy` - Mudanças relacionadas ao deploy
- `📚 Documentação` - Atualizações na documentação

---

**Formato baseado em:** [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/)
**Versionamento:** [Semantic Versioning](https://semver.org/lang/pt-BR/)
