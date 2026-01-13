"""
Serviço de geração de QR Code
"""
import qrcode
import io
import base64
from typing import Optional


def generate_qrcode_base64(order_id: str, size: int = 200) -> str:
    """
    Gera QR Code do pedido e retorna como base64
    
    Args:
        order_id: ID do pedido
        size: Tamanho do QR em pixels
        
    Returns:
        String base64 da imagem PNG
    """
    # Cria o QR Code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2,
    )
    
    # O conteúdo do QR é apenas o ID do pedido
    # Quando bipado, o app faz POST /orders/{id}/scan
    qr.add_data(order_id)
    qr.make(fit=True)
    
    # Gera imagem
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Redimensiona se necessário
    img = img.resize((size, size))
    
    # Converte para base64
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_base64}"


def generate_qrcode_bytes(order_id: str) -> bytes:
    """
    Gera QR Code e retorna como bytes (para download direto)
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2,
    )
    
    qr.add_data(order_id)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    
    return buffer.getvalue()
