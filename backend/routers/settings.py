"""
Rotas de Configurações do Restaurante

Aqui ficam as configurações do restaurante:
- Nome, telefone, endereço
- Coordenadas (lat/lng) já salvas - NÃO chama Geocoding toda vez!

O Geocoding só é chamado quando o DONO atualiza o endereço.
Depois disso, o app do motoboy só pega as coordenadas prontas.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from database import get_session
from models import Settings, SettingsUpdate, SettingsResponse
from services.geocoding_service import geocode_address

router = APIRouter(prefix="/settings", tags=["Configurações"])


def get_or_create_settings(session: Session) -> Settings:
    """
    Pega as configurações ou cria se não existir
    
    Essa tabela sempre tem só UMA linha com id="default"
    """
    settings = session.get(Settings, "default")
    
    if not settings:
        # Primeira vez - cria com valores padrão
        settings = Settings(
            id="default",
            restaurant_name="Meu Restaurante",
            address="",
            lat=None,
            lng=None
        )
        session.add(settings)
        session.commit()
        session.refresh(settings)
    
    return settings


@router.get("", response_model=SettingsResponse)
def get_settings(session: Session = Depends(get_session)):
    """
    Retorna as configurações do restaurante
    
    O app do motoboy chama isso para pegar a localização
    do restaurante SEM precisar chamar Geocoding!
    
    Fluxo:
    1. Motoboy abre app
    2. App chama GET /settings
    3. Retorna lat/lng já salvos
    4. Mostra no mapa - SEM CUSTO!
    """
    settings = get_or_create_settings(session)
    
    return SettingsResponse(
        id=settings.id,
        restaurant_name=settings.restaurant_name,
        phone=settings.phone,
        address=settings.address,
        lat=settings.lat,
        lng=settings.lng,
        updated_at=settings.updated_at
    )


@router.put("", response_model=SettingsResponse)
def update_settings(data: SettingsUpdate, session: Session = Depends(get_session)):
    """
    Atualiza as configurações do restaurante
    
    Se o endereço mudar, chama Geocoding UMA VEZ para
    pegar as coordenadas e salvar no banco.
    
    Depois disso, o motoboy sempre pega do banco!
    
    Fluxo:
    1. Dono atualiza endereço
    2. Geocoding busca lat/lng (custo R$ 0,02)
    3. Salva no banco
    4. Motoboy pega do banco (custo R$ 0,00)
    5. Motoboy pega do banco (custo R$ 0,00)
    6. ... para sempre grátis!
    """
    settings = get_or_create_settings(session)
    
    # Atualiza campos que vieram
    if data.restaurant_name is not None:
        settings.restaurant_name = data.restaurant_name
    
    if data.phone is not None:
        settings.phone = data.phone
    
    # Se mudou o endereço, recalcula coordenadas
    if data.address is not None and data.address != settings.address:
        settings.address = data.address
        
        # Chama Geocoding só aqui - UMA VEZ!
        if data.address.strip():
            coords = geocode_address(data.address)
            if coords:
                settings.lat, settings.lng = coords
                print(f"✅ Settings: Endereço geocodificado: {data.address} → ({settings.lat}, {settings.lng})")
            else:
                print(f"⚠️ Settings: Não encontrou coordenadas para: {data.address}")
        else:
            settings.lat = None
            settings.lng = None
    
    settings.updated_at = datetime.now()
    
    session.add(settings)
    session.commit()
    session.refresh(settings)
    
    return SettingsResponse(
        id=settings.id,
        restaurant_name=settings.restaurant_name,
        phone=settings.phone,
        address=settings.address,
        lat=settings.lat,
        lng=settings.lng,
        updated_at=settings.updated_at
    )
