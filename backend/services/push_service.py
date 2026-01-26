"""
Servico de Push Notifications com Firebase Cloud Messaging (FCM)

Envia notificacoes push para os celulares dos motoboys quando:
- Novo lote e atribuido
- Pedido urgente
- Outras notificacoes importantes

Usa o Firebase Admin SDK para enviar mensagens.
"""
from typing import Optional

from firebase_admin import messaging

from services.firebase_config import initialize_firebase, is_firebase_enabled


# Inicializa Firebase ao importar o modulo
initialize_firebase()


def send_push_notification(
    token: str,
    title: str,
    body: str,
    data: Optional[dict] = None
) -> bool:
    """
    Envia uma notificacao push generica para um dispositivo.

    Args:
        token: Token FCM do dispositivo
        title: Titulo da notificacao
        body: Corpo da mensagem
        data: Dados adicionais (opcional)

    Returns:
        True se enviado com sucesso, False caso contrario
    """
    if not is_firebase_enabled():
        print(f"Push: Firebase desativado - notificacao ignorada")
        return False

    if not token:
        print(f"Push: Token vazio - notificacao ignorada")
        return False

    try:
        # Configura a notificacao visivel
        notification = messaging.Notification(
            title=title,
            body=body
        )

        # Configuracoes Android (som, vibracao, prioridade)
        android_config = messaging.AndroidConfig(
            priority="high",
            notification=messaging.AndroidNotification(
                icon="ic_notification",
                color="#f97316",  # Laranja MotoFlash
                sound="default",
                default_vibrate_timings=True,
                default_sound=True,
                channel_id="motoflash_entregas"
            )
        )

        # Configuracoes iOS (APNs)
        apns_config = messaging.APNSConfig(
            payload=messaging.APNSPayload(
                aps=messaging.Aps(
                    sound="default",
                    badge=1
                )
            )
        )

        # Monta a mensagem
        message = messaging.Message(
            notification=notification,
            android=android_config,
            apns=apns_config,
            data=data or {},
            token=token
        )

        # Envia
        response = messaging.send(message)
        print(f"Push: Enviado com sucesso! ID: {response}")
        return True

    except messaging.UnregisteredError:
        print(f"Push: Token invalido ou dispositivo desregistrado")
        return False
    except Exception as e:
        print(f"Push: Erro ao enviar - {e}")
        return False


def notify_new_batch(token: str, order_count: int, batch_id: str) -> bool:
    """
    Notifica o motoboy sobre um novo lote de entregas.

    Args:
        token: Token FCM do motoboy
        order_count: Quantidade de pedidos no lote
        batch_id: ID do lote

    Returns:
        True se enviado com sucesso
    """
    plural = "entregas" if order_count > 1 else "entrega"
    title = "Novo Lote de Entregas!"
    body = f"Voce recebeu {order_count} {plural}. Abra o app para ver a rota."

    return send_push_notification(
        token=token,
        title=title,
        body=body,
        data={
            "type": "new_batch",
            "batch_id": batch_id,
            "order_count": str(order_count),
            "click_action": "OPEN_BATCH"
        }
    )


def notify_order_ready(token: str, customer_name: str) -> bool:
    """
    Notifica que um pedido esta pronto para coleta.

    Args:
        token: Token FCM do motoboy
        customer_name: Nome do cliente

    Returns:
        True se enviado com sucesso
    """
    return send_push_notification(
        token=token,
        title="Pedido Pronto!",
        body=f"O pedido de {customer_name} esta pronto para retirada.",
        data={
            "type": "order_ready",
            "click_action": "OPEN_ORDERS"
        }
    )


def notify_urgent(token: str, message: str) -> bool:
    """
    Envia uma notificacao urgente.

    Args:
        token: Token FCM do motoboy
        message: Mensagem urgente

    Returns:
        True se enviado com sucesso
    """
    return send_push_notification(
        token=token,
        title="URGENTE - MotoFlash",
        body=message,
        data={
            "type": "urgent",
            "click_action": "OPEN_APP"
        }
    )


def send_to_multiple(tokens: list, title: str, body: str, data: Optional[dict] = None) -> dict:
    """
    Envia notificacao para multiplos dispositivos de uma vez.

    Args:
        tokens: Lista de tokens FCM
        title: Titulo da notificacao
        body: Corpo da mensagem
        data: Dados adicionais (opcional)

    Returns:
        Dict com contagem de sucesso/falha
    """
    if not is_firebase_enabled():
        print(f"Push: Firebase desativado - notificacoes ignoradas")
        return {"success": 0, "failure": len(tokens)}

    if not tokens:
        return {"success": 0, "failure": 0}

    # Filtra tokens vazios
    valid_tokens = [t for t in tokens if t]
    if not valid_tokens:
        return {"success": 0, "failure": len(tokens)}

    try:
        notification = messaging.Notification(
            title=title,
            body=body
        )

        android_config = messaging.AndroidConfig(
            priority="high",
            notification=messaging.AndroidNotification(
                icon="ic_notification",
                color="#f97316",
                sound="default",
                channel_id="motoflash_entregas"
            )
        )

        # Cria mensagem multicast
        message = messaging.MulticastMessage(
            notification=notification,
            android=android_config,
            data=data or {},
            tokens=valid_tokens
        )

        response = messaging.send_each_for_multicast(message)

        print(f"Push Multicast: {response.success_count} sucesso, {response.failure_count} falha")

        return {
            "success": response.success_count,
            "failure": response.failure_count
        }

    except Exception as e:
        print(f"Push Multicast: Erro - {e}")
        return {"success": 0, "failure": len(valid_tokens)}
