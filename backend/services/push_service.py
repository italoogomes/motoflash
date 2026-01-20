"""
Serviço de Push Notifications (DESATIVADO)

O Firebase foi removido. Agora o app usa som + vibração no celular.
As funções abaixo são mantidas para não quebrar o código, mas não fazem nada.
"""


def send_push_notification(token: str, title: str, body: str, data: dict = None) -> bool:
    """Push desativado - usa som + vibração no app"""
    return True


def notify_new_batch(token: str, order_count: int, batch_id: str) -> bool:
    """Push desativado - usa som + vibração no app"""
    return True


def notify_order_ready(token: str, customer_name: str) -> bool:
    """Push desativado - usa som + vibração no app"""
    return True


def notify_urgent(token: str, message: str) -> bool:
    """Push desativado - usa som + vibração no app"""
    return True
