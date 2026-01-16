"""
MotoFlash - Sistema de Despacho Inteligente para Entregas

MVP V0.5

Execute com: uvicorn main:app --reload
Docs: http://localhost:8000/docs
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
import os

from database import create_db_and_tables
from routers import orders_router, couriers_router, dispatch_router
from services.geocoding_service import geocode_address_detailed


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Cria o banco de dados na inicialização"""
    create_db_and_tables()
    yield


app = FastAPI(
    title="MotoFlash",
    description="""
    Sistema de despacho inteligente para restaurantes com entregadores próprios.
    
    ## Funcionalidades
    
    - 📦 **Pedidos**: Criar, listar e gerenciar pedidos com QR Code
    - 🏍️ **Motoqueiros**: Gerenciar frota de entregadores
    - 🚀 **Dispatch**: Algoritmo inteligente de distribuição
    - 🗺️ **Geocoding**: Conversão automática de endereços em coordenadas
    
    ## Fluxo
    
    1. Pedido é criado → QR Code gerado
    2. Cozinha bipa QR → Pedido fica PRONTO
    3. Dispatch agrupa pedidos por proximidade
    4. Motoqueiro recebe lote de entregas
    5. Motoqueiro finaliza → Disponível para novo lote
    """,
    version="0.5.0",
    lifespan=lifespan
)

# CORS - permite que o React acesse a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique os domínios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra as rotas
app.include_router(orders_router)
app.include_router(couriers_router)
app.include_router(dispatch_router)


# Rota raiz
@app.get("/", tags=["Root"])
def root():
    return {
        "app": "MotoFlash",
        "version": "0.3.0",
        "docs": "/docs",
        "status": "running"
    }


# Rota de health check
@app.get("/health", tags=["Root"])
def health():
    return {"status": "healthy"}


# Endpoint de geocoding para testes
@app.get("/geocode", tags=["Utilidades"])
def geocode(address: str, city: str = "Ribeirão Preto", state: str = "SP"):
    """
    Converte um endereço em coordenadas (lat, lng)
    
    Usa o Nominatim (OpenStreetMap) - gratuito!
    
    Exemplo: /geocode?address=Rua Visconde de Inhaúma, 2235
    """
    result = geocode_address_detailed(address, city, state)
    return result


# ============ SERVE FRONTEND ============
# Permite acessar o app pelo mesmo servidor (só precisa 1 ngrok!)

@app.get("/motoboy", response_class=HTMLResponse, tags=["Frontend"])
@app.get("/motoboy.html", response_class=HTMLResponse, tags=["Frontend"])
def serve_motoboy():
    """App do Motoboy - acesse /motoboy no celular"""
    frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "motoboy.html")
    if os.path.exists(frontend_path):
        with open(frontend_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Arquivo não encontrado</h1><p>Coloque o frontend na pasta ../frontend/</p>", status_code=404)


@app.get("/dashboard", response_class=HTMLResponse, tags=["Frontend"])
@app.get("/index.html", response_class=HTMLResponse, tags=["Frontend"])
def serve_dashboard():
    """Dashboard do Restaurante - acesse /dashboard"""
    frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
    if os.path.exists(frontend_path):
        with open(frontend_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Arquivo não encontrado</h1><p>Coloque o frontend na pasta ../frontend/</p>", status_code=404)
