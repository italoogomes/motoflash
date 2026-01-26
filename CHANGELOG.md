# 📝 Changelog - MotoFlash

Todas as mudanças notáveis do projeto serão documentadas neste arquivo.

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
