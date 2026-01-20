"""
Serviço de Push Notifications (Firebase Cloud Messaging - API V1)

Envia notificações para o celular do motoboy quando:
- Novos pedidos são atribuídos a ele
- Pedido fica pronto para coleta
- Alertas importantes

COMO FUNCIONA:
1. Motoboy abre o app → app pede permissão de notificação
2. Firebase gera um TOKEN único pro dispositivo
3. App envia o token pro backend → salva no banco (courier.push_token)
4. Quando dispatch atribui lote → backend envia push usando o token
5. Celular recebe a notificação mesmo com app fechado!

USA A API V1 DO FIREBASE (a legada foi descontinuada em 2023)
"""
import json
import os
from typing import Optional
import httpx
from google.oauth2 import service_account
from google.auth.transport.requests import Request

# Caminho para o arquivo de credenciais do Firebase
CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), "..", "firebase-credentials.json")

# Project ID do Firebase
PROJECT_ID = "motoflash-80f6a"

# URL da API V1 do Firebase
FCM_URL = f"https://fcm.googleapis.com/v1/projects/{PROJECT_ID}/messages:send"

# Scopes necessários para FCM
SCOPES = ["https://www.googleapis.com/auth/firebase.messaging"]

# Cache do token de acesso
_cached_token = None
_token_expiry = None


def get_access_token() -> str:
    """
    Obtém um token de acesso OAuth2 para a API do Firebase
    Usa cache para evitar requisições desnecessárias
    """
    global _cached_token, _token_expiry
    
    from datetime import datetime, timedelta
    
    # Se tem token em cache e não expirou, usa ele
    if _cached_token and _token_expiry and datetime.now() < _token_expiry:
        return _cached_token
    
    try:
        # Carrega credenciais do arquivo JSON
        credentials = service_account.Credentials.from_service_account_file(
            CREDENTIALS_PATH,
            scopes=SCOPES
        )
        
        # Atualiza o token
        credentials.refresh(Request())
        
        # Guarda em cache (expira em 50 minutos para ter margem)
        _cached_token = credentials.token
        _token_expiry = datetime.now() + timedelta(minutes=50)
        
        return _cached_token
        
    except Exception as e:
        print(f"❌ Erro ao obter token Firebase: {e}")
        return None


def send_push_notification(
    token: str,
    title: str,
    body: str,
    data: Optional[dict] = None
) -> bool:
    """
    Envia uma notificação push para um dispositivo (API V1)
    
    Args:
        token: Token FCM do dispositivo (obtido no app)
        title: Título da notificação
        body: Texto da notificação
        data: Dados extras (opcional)
    
    Returns:
        True se enviou com sucesso, False se falhou
    """
    
    if not token:
        print("⚠️ Push: Token vazio, não enviando")
        return False
    
    access_token = get_access_token()
    if not access_token:
        print("❌ Push: Não conseguiu obter access token")
        return False
    
    # Monta o payload no formato da API V1
    message = {
        "message": {
            "token": token,
            "notification": {
                "title": title,
                "body": body
            },
            "webpush": {
                "notification": {
                    "icon": "/icons/icon-192.png",
                    "badge": "/icons/icon-96.png"
                },
                "fcm_options": {
                    "link": "/motoboy"
                }
            },
            "android": {
                "priority": "high",
                "notification": {
                    "icon": "ic_notification",
                    "color": "#f97316",
                    "sound": "default",
                    "click_action": "OPEN_MOTOBOY"
                }
            }
        }
    }
    
    # Adiciona dados extras se houver
    if data:
        message["message"]["data"] = {k: str(v) for k, v in data.items()}
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                FCM_URL,
                json=message,
                headers=headers
            )
            
            if response.status_code == 200:
                print(f"✅ Push enviado: {title}")
                return True
            else:
                error_detail = response.json() if response.text else response.text
                print(f"❌ Push falhou: {response.status_code} - {error_detail}")
                return False
                
    except Exception as e:
        print(f"❌ Push exception: {e}")
        return False


# ============ NOTIFICAÇÕES PRÉ-DEFINIDAS ============

def notify_new_batch(token: str, order_count: int, batch_id: str) -> bool:
    """Notifica motoboy sobre novo lote de entregas"""
    return send_push_notification(
        token=token,
        title="🏍️ Novas entregas!",
        body=f"Você tem {order_count} pedido(s) para entregar",
        data={"type": "new_batch", "batch_id": batch_id}
    )


def notify_order_ready(token: str, customer_name: str) -> bool:
    """Notifica que pedido está pronto para coleta"""
    return send_push_notification(
        token=token,
        title="✅ Pedido pronto!",
        body=f"Pedido de {customer_name} está pronto para retirar",
        data={"type": "order_ready"}
    )


def notify_urgent(token: str, message: str) -> bool:
    """Notificação urgente"""
    return send_push_notification(
        token=token,
        title="⚠️ Atenção!",
        body=message,
        data={"type": "urgent"}
    )
