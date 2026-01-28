"""
Serviço de Pedidos
Helper functions para geração de IDs amigáveis
"""
import random
import string
from sqlmodel import Session, select, func
from models import Order


def generate_short_id(restaurant_id: str, session: Session) -> int:
    """
    Gera um short_id sequencial para o restaurante

    Exemplo: 1001, 1002, 1003...

    Args:
        restaurant_id: ID do restaurante
        session: Sessão do banco de dados

    Returns:
        int: Próximo short_id disponível para o restaurante
    """
    # Busca o maior short_id do restaurante
    statement = select(func.max(Order.short_id)).where(
        Order.restaurant_id == restaurant_id
    )
    max_short_id = session.exec(statement).first()

    # Se não houver pedidos, começa em 1001
    # Se houver, incrementa o último
    if max_short_id is None or max_short_id == 0:
        return 1001
    else:
        return max_short_id + 1


def generate_tracking_code() -> str:
    """
    Gera um código de rastreio único alfanumérico

    Formato: MF-XXXXXX (6 caracteres aleatórios)
    Exemplo: MF-A3B7K9, MF-X2Y8Z5

    Returns:
        str: Código de rastreio único
    """
    # Gera 6 caracteres aleatórios (letras maiúsculas + números)
    random_part = ''.join(
        random.choices(string.ascii_uppercase + string.digits, k=6)
    )

    return f"MF-{random_part}"


def ensure_unique_tracking_code(session: Session) -> str:
    """
    Garante que o tracking_code gerado seja único

    Args:
        session: Sessão do banco de dados

    Returns:
        str: Código de rastreio único garantido
    """
    max_attempts = 10

    for _ in range(max_attempts):
        code = generate_tracking_code()

        # Verifica se já existe no banco
        statement = select(Order).where(Order.tracking_code == code)
        existing = session.exec(statement).first()

        if not existing:
            return code

    # Se após 10 tentativas não conseguiu gerar único, adiciona timestamp
    import time
    timestamp_suffix = str(int(time.time()))[-4:]  # Últimos 4 dígitos do timestamp
    return f"MF-{timestamp_suffix}{random.choice(string.ascii_uppercase)}{random.choice(string.digits)}"
