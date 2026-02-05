# 📋 MotoFlash - Estado Atual

**Versão:** 1.5.0 | **Data:** 2026-02-02 | **Testes:** 94/94 (100%)

---

## 🏗️ Stack

- **Backend:** FastAPI + PostgreSQL + SQLAlchemy
- **Frontend:** React 18 (CDN) + Tailwind + Leaflet.js (servido via `backend/static/`)
- **App Motoboy:** Capacitor (Android nativo) + PWA fallback
- **Deploy:** Railway (monolito — frontend dentro do backend por design)
- **CI/CD:** GitHub Actions (testes automáticos em push/PR)
- **APIs Externas:** Google Maps (Geocoding + Directions)

## 📊 Cobertura de Testes

| Módulo | Testes | Arquivo |
|--------|--------|---------|
| Auth | 8 | `tests/test_auth.py` |
| Pedidos | 22 | `tests/test_orders.py` |
| Dispatch | 14 | `tests/test_dispatch.py` |
| Motoboys | 33 | `tests/test_couriers.py` |
| Previsão | 15 | `tests/test_prediction.py` |
| **TOTAL** | **94** | **100% passando** |

## ✅ Funcionalidades Implementadas

### Core
- Autenticação JWT + rate limiting (desabilitado em testes via `TESTING=true`)
- CRUD de pedidos com `short_id` sequencial (#1001, #1002...) e `tracking_code` (MF-XXXXXX)
- Algoritmo de dispatch: agrupa pedidos próximos (<3km), max 6/lote, atribui motoboys
- Multi-tenant rigoroso (tudo filtrado por `restaurant_id`)
- Endpoint público de rastreio: `GET /orders/track/{tracking_code}`

### Dashboard (Restaurante)
- **Aba Pedidos:** Cards com status, filtros, ações rápidas
- **Aba Rastreamento:** Busca multi-campo (nome/telefone/short_id/tracking_code), mapa Leaflet com polyline, GPS motoboy em tempo real (polling 10s), botão WhatsApp
- **Aba Motoqueiros:** Cards por status, mapa com GPS em tempo real
- **Aba Dispatch:** Previsão híbrida de motoboys (histórico + tempo real + teoria de filas)

### App Motoboy (Capacitor Android)
- Login, mapa, lista de entregas
- GPS em background via Foreground Service (funciona minimizado)
- Envio GPS a cada 5s com retry (3 tentativas)
- Detecta ambiente: Capacitor (URL fixa) vs navegador (window.location.origin)

## ⚠️ Decisões Técnicas Importantes

- **Ordem de rotas FastAPI:** Rotas específicas (`/search`, `/track/{code}`) ANTES de genéricas (`/{id}`)
- **Leaflet em modais:** Precisa de delay 300ms + requestAnimationFrame + verificação `offsetHeight > 0` + state `mapReady`
- **GPS:** Nunca depender só de `watchPosition` — usar `setInterval` como backup
- **CORS:** Inclui origens Capacitor (`https://localhost`, `capacitor://localhost`)

## 🔜 Próximos Passos

**Status atual:** Aguardando verificação da conta Google Play Console (pode levar dias)

**Enquanto aguardamos, escolher uma das opções:**

1. **Preparar Assets da Play Store** 📸 (RECOMENDADO - rápido e deixa tudo pronto)
   - Criar ícone 512x512px
   - Screenshots do app funcionando
   - Descrição e textos promocionais
   - Banner da loja

2. **Gerar APK/AAB Assinado** 🔐
   - Criar keystore
   - Gerar `.aab` final
   - Testar em dispositivos reais

3. **Testar App em Produção** 🧪
   - GPS em background (minimizar app)
   - Verificar atualização do dashboard
   - Testar em diferentes dispositivos Android

4. **Implementar Novas Features** ✨
   - Nova Aba de Relatórios (visão geral, performance, horários de pico)
   - Aba de Configurações (dados da conta, horários, preferências)

5. **Melhorar Documentação** 📚
   - README com guia do app
   - Manual para motoboys
   - Documentar processo de publicação

## 📂 Estrutura Principal

```
motoflash/
├── backend/
│   ├── main.py              # FastAPI app + CORS
│   ├── models.py            # SQLAlchemy models + Pydantic schemas
│   ├── database.py          # PostgreSQL connection
│   ├── routers/             # auth, orders, dispatch, couriers, menu
│   ├── services/            # order_service, prediction_service, alerts_service
│   ├── static/              # Frontend (dashboard + motoboy PWA)
│   │   ├── index.html       # Dashboard SPA (36 linhas)
│   │   ├── motoboy.html     # App motoboy (PWA + Capacitor)
│   │   ├── css/dashboard.css
│   │   └── js/ (helpers, components, app)
│   └── tests/               # 94 testes
├── motoboy-app/             # Capacitor Android project
│   ├── capacitor.config.json
│   ├── build/index.html     # Cópia do motoboy.html com URL fixa
│   └── android/             # Projeto Android Studio
├── docs/                    # ARQUITETURA, API_ENDPOINTS, FLUXOS, TESTES, CI_CD
├── .github/workflows/       # GitHub Actions
└── CLAUDE.md                # Contexto para Claude Code
```

## 📝 Regras Para Contribuir

- **Testes:** 94/94 DEVEM passar sempre. Rodar `pytest` antes de commitar
- **Multi-tenant:** Todo novo endpoint DEVE filtrar por `restaurant_id`
- **Documentação:** Atualizar CHANGELOG.md a cada feature/fix
- **Banco:** PostgreSQL em produção, SQLite em memória nos testes
- **Commits:** Seguir padrão `Feat:`, `Fix:`, `Docs:` com versão semântica
