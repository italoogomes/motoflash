# 📝 Changelog - MotoFlash

Todas as mudanças notáveis do projeto serão documentadas neste arquivo.

---

## [1.4.2] - 2026-02-01

### 📋 Melhorias na Aba de Pedidos

#### ✅ Novas Funcionalidades

1. **❌ Cancelar Pedido**
   - Novo endpoint `POST /orders/{id}/cancel`
   - Status `CANCELLED` adicionado ao enum
   - Botão ✕ nos cards de pedido
   - Libera motoboy automaticamente se estava atribuído

2. **🔔 Notificação Sonora**
   - Som de beep quando novo pedido chega
   - Botão toggle no header (🔔/🔕)
   - Não toca no primeiro carregamento

3. **📅 Filtro de Histórico**
   - Parâmetros `date_from` e `date_to` no endpoint `/orders`
   - Botões: Hoje / Ontem / 7 dias / Tudo

4. **▦ Visualização Kanban**
   - Toggle entre Lista (☰) e Kanban (▦)
   - 4 colunas: Preparando → Pronto → Em Rota → Entregue
   - Cards compactos com ações rápidas

#### 🛠️ Arquivos Modificados
- `backend/models.py` - Status CANCELLED + campo cancelled_at
- `backend/routers/orders.py` - Endpoint /cancel + filtros de data
- `backend/static/js/components.js` - UI (cancelar, filtro, kanban)
- `backend/static/js/app.js` - Som de notificação
- `backend/tests/test_orders.py` - 2 novos testes

#### 📊 Testes
- **94/94 passando** (100%)

---

## [1.4.1] - 2026-02-01

### 📋 Simplificação do Fluxo de Pedidos

#### ✅ Mudanças
- Pedidos agora iniciam direto em **PREPARING** (removido status CREATED)
- Removido filtro "Criado" da aba de pedidos
- "Atribuído" renomeado para **"Em Rota"** (mais intuitivo)

#### 📊 Fluxo Simplificado

**Antes (6 status):**
```
Criado → Preparando → Pronto → Atribuído → Coletado → Entregue
```

**Depois (5 status):**
```
Preparando → Pronto → Em Rota → Coletado → Entregue
```

#### 🛠️ Arquivos Modificados
- `backend/routers/orders.py` - Status inicial = PREPARING
- `backend/static/js/components.js` - Removido filtro "Criado", renomeado "Atribuído"
- `backend/tests/*.py` - Testes ajustados para novo fluxo

#### 💡 Benefícios
- Menos cliques para o atendente
- Interface mais limpa
- Fluxo mais parecido com apps de delivery (iFood, etc.)

---

## [1.4.0] - 2026-02-01

### 🐘 Migração para PostgreSQL

#### ✅ Mudanças
- Migrado de SQLite para PostgreSQL (Railway)
- `database.py` detecta automaticamente qual banco usar
- Adicionado `psycopg2-binary` ao requirements.txt
- Testes continuam usando SQLite em memória

#### 📈 Escalabilidade

| Antes (SQLite) | Depois (PostgreSQL) |
|----------------|---------------------|
| ~10-15 restaurantes | 500+ restaurantes |
| ~50 motoboys | 2000+ motoboys |
| Lock único de escrita | Escritas paralelas |

#### 🛠️ Arquivos Modificados
- `backend/database.py` - Detecção automática de banco
- `backend/requirements.txt` - Driver PostgreSQL

---

## [1.3.3] - 2026-02-01

### 📍 GPS em Tempo Real do Motoboy

#### 🐛 Bug Corrigido
- **Problema:** GPS do motoboy não atualizava em tempo real durante entrega
- **Sintoma:** Posição ficava "travada" no restaurante mesmo com motoboy na metade do caminho
- **Causa Raiz:** Código dependia 100% do `watchPosition` do navegador, que:
  - Pausa quando tela em background
  - Não garante frequência de atualização
  - Para silenciosamente em economia de bateria

#### ✅ Solução Implementada

**Estratégia: Envio Independente com Intervalo Fixo**

1. **Nova ref `lastKnownPositionRef`** - Armazena última posição GPS conhecida
2. **Função `sendGPSToBackend()` com retry** - 3 tentativas com 1s de delay entre cada
3. **`setInterval` de 5 segundos** - Envia GPS independente do `watchPosition`
4. **Envio imediato ao iniciar rota** - GPS enviado quando clica "Iniciar Rota"

#### 🛠️ Modificado
- `backend/static/motoboy.html`
  - Adicionada ref `lastKnownPositionRef`
  - Criada função `sendGPSToBackend()` com retry
  - Adicionado `setInterval` de 5s para envio periódico
  - Modificada `startRoute()` para enviar GPS imediatamente

#### 📊 Comparação

| Antes | Depois |
|-------|--------|
| GPS só quando `watchPosition` dispara | GPS a cada 5s via `setInterval` |
| Throttle de 10 segundos | Intervalo fixo de 5 segundos |
| Sem retry em falha | 3 tentativas com 1s de delay |
| Pausa em background | Continua enviando |

#### 💡 Lição Aprendida
> Nunca dependa apenas de eventos do navegador para funções críticas!
> Use `setInterval` como backup para garantir envio de dados.

---

## [1.3.2] - 2026-01-29

### 🗺️ Correção Completa: Mapa Preto + Marcador do Motoboy

#### 🐛 Bugs Corrigidos

**1. Mapa Preto no TrackingModal**
- **Problema:** Mapa aparecia completamente preto após abrir modal
- **Causa:** Leaflet criava mapa quando container tinha `height: 0` (animação CSS)
- **Solução (6 tentativas):**
  - Delay inicial de 300ms (aguarda animação CSS)
  - Verificação recursiva com `requestAnimationFrame` (até 50 tentativas)
  - Só cria mapa quando `offsetHeight > 0`
  - State `mapReady` sincroniza mapa com marcadores

**2. Marcador do Motoboy Não Aparecia**
- **Problema:** Marcador 🏍️ azul do motoboy não aparecia no mapa
- **Causa:** App do motoboy (`motoboy.html`) NÃO enviava GPS para o backend
- **Solução:**
  - Adicionado `fetch` no `watchPosition` para enviar GPS a cada 10s
  - Corrigido erro "courierId undefined" usando `localStorage.getItem('motoboy_id')`

#### 🛠️ Modificado
- `backend/static/js/components.js` - TrackingModal
  - State `mapReady` para sincronização
  - Verificação recursiva de container visível
  - Logs detalhados para debug GPS

- `backend/static/motoboy.html` - App do Motoboy
  - GPS enviado para backend a cada 10 segundos
  - Usa `localStorage.getItem('motoboy_id')` para ID

#### 📊 Resultado
- ✅ **Mapa funciona 100%** (tiles carregam corretamente)
- ✅ **Marcador do motoboy aparece!** (🏍️ azul pulsante)
- ✅ **GPS em tempo real** (atualiza a cada 10s)
- ✅ **Zoom não reseta mais**
- ✅ **Polling funciona** sem quebrar mapa

#### 🔄 Commits (9 total)
```
# Correção do Mapa Preto (6 tentativas)
b766271 - Fix v1: Separar useEffect de criação/atualização
454997c - Fix v2: Replicar lógica do motoboy.html
56f43f9 - Fix v3: invalidateSize + aguardar dados
20202d5 - Fix v4: Remover dependência de dados
e2e9d26 - Fix v5: requestAnimationFrame recursivo
80d4cff - Fix v6: SOLUÇÃO DEFINITIVA ✅

# Correção do Marcador do Motoboy (3 commits)
d21039b - Debug: Logs detalhados para marcador
e6c6c2a - Fix: Enviar GPS do motoboy para backend
82c81d3 - Fix: Corrigir referência a courierId
```

#### 💡 Lições Técnicas
- Leaflet em modais requer aguardar animações CSS
- `requestAnimationFrame` + verificação de altura é a solução correta
- State `mapReady` evita race conditions
- **Sempre verificar se dados chegam no backend** (GPS era usado só localmente)

---

## [1.3.1] - 2026-01-29

### 🔍 Correção: Endpoint de Busca Retornava 404

#### 🐛 Bug Corrigido
- Endpoint `/orders/search` retornava 404 Not Found
- Causa: Ordem incorreta de rotas no FastAPI
- Rota específica `/search` estava APÓS rota genérica `/{order_id}`
- FastAPI interpretava "search" como um `order_id`

#### ✅ Solução
- Movido `@router.get("/search")` para ANTES de `@router.get("/{order_id}")`
- Rotas específicas devem sempre vir antes de rotas com path parameters

#### 🛠️ Modificado
- `backend/routers/orders.py` - Reordenação de rotas (110 linhas)

#### 📊 Resultado
- ✅ Busca por nome funciona (ex: "Ítalo Gomes")
- ✅ Busca por tracking code funciona (ex: "MF-HJGDG9")
- ✅ Busca por short_id funciona (ex: "#1003")
- ✅ Sistema de rastreamento totalmente funcional

---

## [1.3.0] - 2026-01-28

### 📍 Sistema de Rastreamento para Atendente

#### ✨ Funcionalidades
- **Busca Multi-Campo** - Nome, telefone, #short_id, tracking_code
- **Normalização de Texto** - Remove acentos, case-insensitive
- **Mapa Interativo** - Leaflet.js com marcadores customizados
- **Tempo Real** - Polling a cada 10 segundos
- **WhatsApp Integration** - Envia link de rastreio público

#### 🆕 Backend
- `GET /orders/search?q={query}` - Busca multi-campo
- `GET /orders/{order_id}/tracking-details` - Detalhes completos
- 6 novos schemas (OrderTrackingDetails, BatchInfo, CourierInfo, etc)

#### 🎨 Frontend
- Nova aba "📍 Rastreamento" na sidebar
- Componente TrackingPage com busca em tempo real
- Modal TrackingModal com mapa Leaflet
- Marcadores: 🏪 restaurante, 🏍️ motoboy, 1️⃣2️⃣3️⃣ pedidos

#### 💰 Custo Zero
- **NÃO gasta requisições extras** do Google Maps
- Reutiliza polyline já gerada no dispatch

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
