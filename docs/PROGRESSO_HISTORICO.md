# 📜 MotoFlash - Histórico de Desenvolvimento

> Arquivo de referência. Para estado atual, veja `PROGRESSO_ATUAL.md`.

---

## Timeline de Versões

### v1.0.0 — Arquitetura Modular (Base)
- Refatoração do index.html de 3.732 → 36 linhas
- Separação em módulos: `css/dashboard.css`, `js/components.js`, `js/app.js`, `js/utils/helpers.js`
- SPA com navegação suave

### v1.0.1 a v1.0.4 — Testes Automatizados
- v1.0.1: 8 testes auth (login, registro, /me)
- v1.0.2: +15 testes pedidos (CRUD, QR Code, transições de status, multi-tenant)
- v1.0.3: +14 testes dispatch (agrupamento, limites, atribuição, multi-tenant)
- v1.0.4: +33 testes motoboys (auth, CRUD, status, lotes, GPS, senha, rotas)

### v1.0.5 — Estabilização + CI/CD
- Corrigidos 9 testes falhando (70/70 → 100%)
- Bugs: mensagens de erro auth, payload registro, imports, campos de modelo
- GitHub Actions configurado (push + PR)

### v1.1.0 — Previsão Híbrida de Motoboys
- Modelo `PadraoDemanda` (histórico por dia/hora)
- Serviço `prediction_service.py`: histórico + tempo real + teoria de filas
- Endpoints: `GET /dispatch/previsao`, `POST /dispatch/atualizar-padroes`, `GET /dispatch/padroes`
- +15 testes (85/85 total)

### v1.1.1 — Fix Motoboys Recomendados
- Bug: campo copiava `total_ativos` em vez de calcular recomendação
- Fix: retorna `None` quando sem dados, frontend mostra "-"

### v1.2.0 — IDs Amigáveis
- `short_id`: sequencial por restaurante (#1001, #1002...)
- `tracking_code`: único global (MF-XXXXXX)
- Endpoint público: `GET /orders/track/{tracking_code}`
- Serviço `order_service.py` criado
- +7 testes (92/92 total)

### v1.3.0 — Rastreamento para Atendente
- Busca multi-campo: nome, telefone, short_id, tracking_code (normalização sem acentos)
- `GET /orders/search?q={query}` + `GET /orders/{id}/tracking-details`
- TrackingModal: mapa Leaflet, polyline, marcadores numerados, GPS polling 10s, botão WhatsApp
- ~900 linhas de código novo (250 backend + 600 frontend + 50 CSS)

### v1.3.1 — Fix Ordem de Rotas FastAPI
- Bug: `/orders/search` retornava 404 (FastAPI interpretava "search" como `{order_id}`)
- Fix: rotas específicas ANTES de rotas genéricas com path params
- **Lição:** Ordem de rotas importa em FastAPI

### v1.3.2 — Fix Mapa Preto + Marcador Motoboy
- Bug 1: Mapa preto no modal (Leaflet criava mapa antes da animação CSS terminar)
- Fix 1: Delay 300ms + requestAnimationFrame recursivo + verificação `offsetHeight > 0` + state `mapReady` (6 tentativas até acertar)
- Bug 2: Marcador motoboy não aparecia (GPS não era enviado ao backend)
- Fix 2: Envio de GPS do motoboy.html via fetch + throttle

### v1.3.3 — GPS Tempo Real
- Bug: GPS parava quando motoboy minimizava app (watchPosition pausa em background)
- Fix: `setInterval` de 5s independente + retry 3x + envio imediato ao iniciar rota

### v1.4.0 a v1.4.2 — Melhorias Aba de Pedidos
- Filtros, busca, ações rápidas, cards melhorados
- 94/94 testes

### v1.4.3 — Aba Motoqueiros
- MotoqueiroPage: busca, agrupamento por status, cards de stats
- CourierMapModal: mapa Leaflet com GPS polling 10s
- Seguiu padrões do TrackingPage (debounce, requestAnimationFrame, mapReady)
- Fix: adicionado `last_lat/last_lng` ao `CourierResponse`

### v1.5.0 — App Nativo Capacitor (Android)
- Capacitor 5+ com plugins: geolocation, foreground-service, http
- GPS em background via Foreground Service (funciona minimizado)
- Detecção de ambiente: Capacitor vs navegador
- CORS configurado para origens Capacitor
- Problemas resolvidos: caminho com acento, Java 17/21, versões gradle, URL da API, CORS
- **Custo:** R$ 130 (conta Play Store)

---

## Bugs Notáveis e Lições

| Bug | Causa | Lição |
|-----|-------|-------|
| /search retorna 404 | Rota genérica `/{id}` antes da específica | Ordem de rotas importa em FastAPI |
| Mapa preto no modal | Leaflet cria antes do CSS terminar | Verificar `offsetHeight > 0` com requestAnimationFrame |
| GPS não atualiza | watchPosition pausa em background | Usar setInterval como backup |
| Marcador motoboy invisível | GPS não era enviado ao backend | Sempre verificar se dados chegam no servidor |
| motoboys_recomendados errado | Copiava total_ativos | Retornar None quando sem dados |
