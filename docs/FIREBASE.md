# Firebase Cloud Messaging (FCM)

Push Notifications para o app do motoboy.

## Visao Geral

O MotoFlash usa Firebase Cloud Messaging para enviar notificacoes push aos motoboys quando:
- Novo lote de entregas e atribuido
- Pedido urgente
- Outras notificacoes importantes

## Arquitetura

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Backend   │────▶│   Firebase  │────▶│  Motoboy    │
│  (FastAPI)  │     │     FCM     │     │  (PWA/App)  │
└─────────────┘     └─────────────┘     └─────────────┘
```

## Arquivos Envolvidos

| Arquivo | Descricao |
|---------|-----------|
| `services/firebase_config.py` | Configuracao e inicializacao do Firebase Admin SDK |
| `services/push_service.py` | Funcoes para enviar notificacoes |
| `static/firebase-messaging-sw.js` | Service Worker para receber notificacoes em background |
| `static/motoboy.html` | Frontend com integracao FCM |

## Configuracao

### 1. Variaveis de Ambiente (Backend)

```env
FIREBASE_PROJECT_ID=motoflash-80f6a
FIREBASE_PRIVATE_KEY_ID=sua-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxx@projeto.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=123456789
```

**Onde obter:** Firebase Console > Configuracoes > Contas de servico > Gerar nova chave privada

### 2. Configuracao do Frontend

No `motoboy.html` e `firebase-messaging-sw.js`:

```javascript
const firebaseConfig = {
    apiKey: "AIzaSy...",
    authDomain: "projeto.firebaseapp.com",
    projectId: "projeto",
    storageBucket: "projeto.firebasestorage.app",
    messagingSenderId: "123456789",
    appId: "1:123456789:web:abc123"
};
```

**Onde obter:** Firebase Console > Configuracoes > Geral > Seus apps > Web

### 3. VAPID Key

```javascript
const VAPID_KEY = 'BJ...';
```

**Onde obter:** Firebase Console > Configuracoes > Cloud Messaging > Certificados de push da Web

## Fluxo de Funcionamento

### 1. Registro do Token

```
Motoboy faz login
      │
      ▼
App pede permissao de notificacao
      │
      ▼
Firebase gera token unico (FCM Token)
      │
      ▼
App envia token para backend
PUT /couriers/{id}/push-token
      │
      ▼
Backend salva token no banco (courier.push_token)
```

### 2. Envio de Notificacao

```
Dispatch cria novo lote
      │
      ▼
Backend busca push_token do motoboy
      │
      ▼
push_service.notify_new_batch(token, qtd, batch_id)
      │
      ▼
Firebase envia para o dispositivo
      │
      ▼
Service Worker recebe e mostra notificacao
```

## API de Push

### Funcoes Disponiveis

```python
from services.push_service import (
    notify_new_batch,      # Novo lote de entregas
    notify_order_ready,    # Pedido pronto
    notify_urgent,         # Mensagem urgente
    send_to_multiple       # Enviar para varios
)
```

### Exemplo de Uso

```python
# Notificar novo lote
notify_new_batch(
    token=courier.push_token,
    order_count=3,
    batch_id="batch-123"
)

# Notificacao customizada
send_push_notification(
    token=courier.push_token,
    title="Titulo",
    body="Mensagem",
    data={"tipo": "custom"}
)
```

## Endpoint

### PUT /couriers/{courier_id}/push-token

Salva o token FCM do motoboy.

**Request:**
```json
{
    "token": "FCM_TOKEN_AQUI"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Token salvo com sucesso"
}
```

## Compatibilidade

| Plataforma | Suporte |
|------------|---------|
| Android (Chrome) | Funciona direto no navegador |
| iOS Safari | Precisa instalar como PWA + iOS 16.4+ |
| Desktop Chrome | Funciona |
| Desktop Firefox | Funciona |

### iOS - Requisitos

1. Adicionar app na tela inicial (PWA)
2. iOS 16.4 ou superior
3. Abrir pelo icone da tela inicial

## Troubleshooting

### "Firebase: Credenciais nao configuradas"

Variaveis de ambiente nao estao definidas. Verifique:
- FIREBASE_PROJECT_ID
- FIREBASE_PRIVATE_KEY
- FIREBASE_CLIENT_EMAIL

### Notificacao nao chega no iOS

1. Verifique se esta usando como PWA (icone na tela inicial)
2. Verifique versao do iOS (precisa 16.4+)
3. Verifique permissoes em Ajustes > Notificacoes

### Token invalido / UnregisteredError

O token expirou ou o usuario desinstalou o app. O backend lida com isso automaticamente.

## Logs

O backend mostra logs do Firebase:

```
Firebase: Inicializado com sucesso!
Push: Token salvo para Joao
Push: Enviado com sucesso! ID: projects/xxx/messages/123
```

## Seguranca

- **NUNCA** commite credenciais no Git
- Use variaveis de ambiente
- A FIREBASE_PRIVATE_KEY e sensivel - trate como senha
- Tokens FCM sao por dispositivo, nao por usuario
