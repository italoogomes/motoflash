"""
Configuracao do Firebase Admin SDK

Carrega credenciais de variaveis de ambiente (mais seguro que arquivos JSON).
NUNCA commite credenciais no Git!

Variaveis necessarias no .env:
- FIREBASE_PROJECT_ID
- FIREBASE_PRIVATE_KEY_ID
- FIREBASE_PRIVATE_KEY
- FIREBASE_CLIENT_EMAIL
- FIREBASE_CLIENT_ID
"""
import os
from typing import Optional

import firebase_admin
from firebase_admin import credentials

# Flag para verificar se Firebase foi inicializado
_firebase_initialized = False


def get_firebase_credentials() -> Optional[dict]:
    """
    Monta as credenciais do Firebase a partir de variaveis de ambiente.
    Retorna None se as variaveis nao estiverem configuradas.
    """
    project_id = os.getenv("FIREBASE_PROJECT_ID")
    private_key_id = os.getenv("FIREBASE_PRIVATE_KEY_ID")
    private_key = os.getenv("FIREBASE_PRIVATE_KEY")
    client_email = os.getenv("FIREBASE_CLIENT_EMAIL")
    client_id = os.getenv("FIREBASE_CLIENT_ID")

    # Verifica se todas as variaveis obrigatorias estao presentes
    if not all([project_id, private_key, client_email]):
        return None

    # A private key vem com \n literal, precisa converter para quebras reais
    if private_key:
        private_key = private_key.replace("\\n", "\n")

    return {
        "type": "service_account",
        "project_id": project_id,
        "private_key_id": private_key_id or "",
        "private_key": private_key,
        "client_email": client_email,
        "client_id": client_id or "",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{client_email.replace('@', '%40')}"
    }


def initialize_firebase() -> bool:
    """
    Inicializa o Firebase Admin SDK.
    Retorna True se inicializado com sucesso, False caso contrario.

    Pode ser chamado multiplas vezes - so inicializa uma vez.
    """
    global _firebase_initialized

    if _firebase_initialized:
        return True

    creds_dict = get_firebase_credentials()

    if not creds_dict:
        print("Firebase: Credenciais nao configuradas (push notifications desativadas)")
        return False

    try:
        cred = credentials.Certificate(creds_dict)
        firebase_admin.initialize_app(cred)
        _firebase_initialized = True
        print("Firebase: Inicializado com sucesso!")
        return True
    except Exception as e:
        print(f"Firebase: Erro ao inicializar - {e}")
        return False


def is_firebase_enabled() -> bool:
    """Verifica se o Firebase esta habilitado e inicializado"""
    return _firebase_initialized
