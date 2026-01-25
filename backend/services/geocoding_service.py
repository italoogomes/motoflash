"""
Serviço de Geocoding usando Google Maps API
Converte endereços em coordenadas com alta precisão
"""
import os
import urllib.parse
from typing import Optional, Tuple
import httpx

# API Key do Google Maps (carregada de variável de ambiente)
GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError(
        "⚠️ GOOGLE_MAPS_API_KEY não configurada!\n"
        "Configure a variável de ambiente GOOGLE_MAPS_API_KEY com sua chave do Google Maps.\n"
        "Obtenha em: https://console.cloud.google.com/apis/credentials"
    )

# Cache local para economizar requests
_geocode_cache = {}


def geocode_address(address: str, city: str = "Ribeirão Preto", state: str = "SP") -> Optional[Tuple[float, float]]:
    """
    Converte um endereço em coordenadas (lat, lng) usando Google Maps API
    """
    # Monta o endereço completo
    full_address = f"{address}, {city}, {state}, Brasil"
    
    # Verifica cache primeiro
    cache_key = full_address.lower().strip()
    if cache_key in _geocode_cache:
        print(f"📍 Cache hit: {address}")
        return _geocode_cache[cache_key]
    
    # Chama Google Geocoding API
    try:
        encoded_address = urllib.parse.quote(full_address)
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={GOOGLE_API_KEY}"
        
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") == "OK" and data.get("results"):
                    location = data["results"][0]["geometry"]["location"]
                    lat = location["lat"]
                    lng = location["lng"]
                    
                    # Salva no cache
                    _geocode_cache[cache_key] = (lat, lng)
                    print(f"✅ Google Geocoding: {address} → ({lat}, {lng})")
                    return (lat, lng)
                else:
                    print(f"❌ Google Geocoding falhou: {data.get('status')} - {address}")
                    return None
            else:
                print(f"❌ Erro HTTP {response.status_code}")
                return None
                
    except Exception as e:
        print(f"❌ Erro no geocoding: {e}")
        return None


def geocode_address_detailed(address: str, city: str = "Ribeirão Preto", state: str = "SP") -> dict:
    """
    Versão detalhada que retorna mais informações
    """
    full_address = f"{address}, {city}, {state}, Brasil"
    
    coords = geocode_address(address, city, state)
    
    if coords:
        return {
            "found": True,
            "lat": coords[0],
            "lng": coords[1],
            "address_searched": full_address
        }
    else:
        return {
            "found": False, 
            "error": "Endereço não encontrado",
            "address_searched": full_address
        }


def clear_cache():
    """Limpa o cache de geocoding"""
    global _geocode_cache
    _geocode_cache = {}


def get_cache_size():
    """Retorna o tamanho do cache"""
    return len(_geocode_cache)
