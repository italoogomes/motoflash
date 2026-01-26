# 📚 Documentação Técnica - MotoFlash

Bem-vindo à documentação completa do MotoFlash! Esta pasta contém toda a documentação técnica necessária para entender, manter e expandir o sistema.

---

## 📖 Documentos Disponíveis

### 1. [ARQUITETURA.md](./ARQUITETURA.md)
**O que é:** Visão geral completa do sistema

**Você vai encontrar:**
- Stack tecnológico (Frontend + Backend)
- Estrutura de pastas detalhada
- Arquitetura do banco de dados
- Autenticação e autorização
- Algoritmo de dispatch (coração do sistema)
- Integração Google Maps
- PWA e service workers
- Segurança e escalabilidade

**Leia quando:** Começar a trabalhar no projeto ou precisar entender a arquitetura geral.

---

### 1.1 [ARQUITETURA_MODULAR.md](./ARQUITETURA_MODULAR.md) ⭐ NOVO
**O que é:** Arquitetura modular do frontend (Dashboard)

**Você vai encontrar:**
- Nova estrutura modular (index.html com 36 linhas!)
- Separação de responsabilidades (CSS, JS, componentes)
- Como trabalhar com módulos
- Guia de desenvolvimento
- Vantagens da arquitetura modular
- Troubleshooting

**Leia quando:** Precisar modificar o dashboard ou entender a nova estrutura do frontend.

---

### 2. [API_ENDPOINTS.md](./API_ENDPOINTS.md)
**O que é:** Referência completa de todos os endpoints da API

**Você vai encontrar:**
- Todos os endpoints organizados por domínio
- Request/Response de cada endpoint
- Headers necessários
- Exemplos de uso
- Códigos de erro
- Rate limiting

**Leia quando:** Precisar fazer requisições à API ou entender o contrato de cada endpoint.

---

### 3. [FLUXOS.md](./FLUXOS.md)
**O que é:** Fluxos de dados completos (Frontend ↔ Backend)

**Você vai encontrar:**
- Diagramas de fluxo detalhados
- Passo a passo de cada operação:
  - Cadastro de restaurante
  - Login
  - Criar pedido
  - Executar dispatch
  - Login motoboy
  - Entregar pedido
  - E muito mais...
- Código simplificado de cada fluxo
- Polling e real-time

**Leia quando:** Precisar entender como uma funcionalidade funciona do início ao fim.

---

### 4. [FRONTEND_BACKEND.md](./FRONTEND_BACKEND.md)
**O que é:** Como cada página do frontend se comunica com o backend

**Você vai encontrar:**
- Código real de cada página:
  - index.html (Dashboard)
  - motoboy.html (App PWA)
  - auth.html (Login/Cadastro)
  - cardapio.html (Gestão de cardápio)
  - clientes.html (Gestão de clientes)
- Exemplos de código React
- Padrões de requisições HTTP
- Tratamento de erros
- Loading states
- Autenticação com JWT

**Leia quando:** Precisar modificar ou criar páginas do frontend.

---

### 5. [FIREBASE.md](./FIREBASE.md)
**O que é:** Push Notifications com Firebase Cloud Messaging

**Você vai encontrar:**
- Configuração do Firebase Admin SDK
- Variáveis de ambiente necessárias
- Fluxo de registro de token
- Fluxo de envio de notificação
- Compatibilidade (Android/iOS)
- Troubleshooting

**Leia quando:** Precisar configurar ou debugar push notifications.

---

## 🎯 Guia Rápido - Por Tarefa

### Quero adicionar um novo endpoint
1. Leia: [ARQUITETURA.md](./ARQUITETURA.md) (seção "Estrutura de Pastas")
2. Crie endpoint em `backend/routers/`
3. Documente em: [API_ENDPOINTS.md](./API_ENDPOINTS.md)
4. Adicione fluxo em: [FLUXOS.md](./FLUXOS.md)

### Quero entender como funciona o dispatch
1. Leia: [ARQUITETURA.md](./ARQUITETURA.md) (seção "Algoritmo de Dispatch")
2. Leia: [FLUXOS.md](./FLUXOS.md) (seção "Executar Dispatch")
3. Código: `backend/services/dispatch_service.py`

### Quero modificar uma página do frontend
1. Leia: [FRONTEND_BACKEND.md](./FRONTEND_BACKEND.md) (seção da página)
2. Código: `backend/static/<pagina>.html`
3. Teste endpoint: [API_ENDPOINTS.md](./API_ENDPOINTS.md)

### Quero entender autenticação
1. Leia: [ARQUITETURA.md](./ARQUITETURA.md) (seção "Autenticação")
2. Leia: [FLUXOS.md](./FLUXOS.md) (seção "Login de Usuário")
3. Código: `backend/services/auth_service.py`

### Quero fazer deploy
1. Leia: [../RAILWAY_SETUP.md](../RAILWAY_SETUP.md)
2. Configure variáveis de ambiente
3. Push para repositório
4. Monitore logs

---

## 🔍 Índice Geral

### Conceitos Principais
- **Multi-tenant:** Todos os dados são isolados por `restaurant_id`
- **JWT Tokens:** Autenticação de usuários do dashboard
- **Dispatch V0.9:** Algoritmo inteligente de agrupamento de pedidos
- **PWA:** App mobile progressivo para motoboys
- **Geocoding:** Conversão automática de endereços em coordenadas
- **QR Codes:** Gerados automaticamente para cada pedido

### Tecnologias
- **Backend:** Python 3.11 + FastAPI + SQLModel + SQLite
- **Frontend:** React 18 (CDN) + Tailwind CSS + Leaflet.js
- **APIs Externas:** Google Maps (Geocoding + Directions)
- **Deploy:** Railway com volume persistente

---

## 📝 Convenções de Código

### Backend (Python)
```python
# Estrutura de router
@router.post("/endpoint")
def function_name(
    data: ModelCreate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    # 1. Validações
    # 2. Lógica de negócio
    # 3. Retorno
    pass
```

### Frontend (React)
```javascript
// Estrutura de componente
function ComponentName() {
  const [state, setState] = useState(null);

  useEffect(() => {
    // Fetch data
  }, []);

  async function handleAction() {
    // API call
  }

  return <div>{/* JSX */}</div>;
}
```

---

## 🆘 Troubleshooting

### Erro: "Token inválido ou expirado"
**Solução:** Token JWT expirou (24h). Faça login novamente.
**Código:** Frontend redireciona automaticamente para `/login`

### Erro: "GOOGLE_MAPS_API_KEY não configurada"
**Solução:** Configure variável de ambiente no Railway
**Doc:** [RAILWAY_SETUP.md](../RAILWAY_SETUP.md)

### Erro: "CORS blocked"
**Solução:** Configure `ALLOWED_ORIGINS` com URL do Railway
**Doc:** [RAILWAY_SETUP.md](../RAILWAY_SETUP.md)

### Pedido não aparece no mapa
**Solução:** Geocoding falhou. Verifique se endereço é válido
**Log:** Backend mostra `❌ Google Geocoding falhou`

---

## 🚀 Roadmap

Ver issues no GitHub para features planejadas:
- [x] Firebase Push Notifications (implementado!)
- [ ] Sistema de métricas e analytics
- [ ] Alertas automáticos
- [ ] Testes automatizados
- [ ] Migração para PostgreSQL

---

## 📧 Contato

Para dúvidas técnicas:
1. Consulte esta documentação primeiro
2. Verifique código fonte
3. Abra issue no GitHub

---

**Última atualização:** 2026-01-25
**Versão do Sistema:** 0.9.0
