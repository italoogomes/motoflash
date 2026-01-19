"""
MotoFlash - Sistema de Despacho Inteligente para Entregas

MVP V0.8

Execute com: uvicorn main:app --reload
Docs: http://localhost:8000/docs
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
import os
import uuid
import shutil
from pathlib import Path

from database import create_db_and_tables
from routers import orders_router, couriers_router, dispatch_router
from routers.menu import router as menu_router
from routers.customers import router as customers_router
from services.geocoding_service import geocode_address_detailed

# Pasta para uploads de imagens
UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)  # Cria a pasta se não existir


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
    version="0.8.0",
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

# Serve arquivos de upload como estáticos
# Exemplo: /uploads/abc123.jpg → backend/uploads/abc123.jpg
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Registra as rotas
app.include_router(orders_router)
app.include_router(couriers_router)
app.include_router(dispatch_router)
app.include_router(menu_router)
app.include_router(customers_router)


# ============ UPLOAD DE IMAGENS ============

@app.post("/upload", tags=["Utilidades"])
async def upload_image(file: UploadFile = File(...)):
    """
    Faz upload de uma imagem
    
    EXPLICAÇÃO SIMPLES:
    1. Recebe um arquivo (foto)
    2. Gera um nome único (pra não sobrescrever outras)
    3. Salva na pasta /uploads
    4. Retorna a URL pra acessar a imagem
    
    Exemplo de retorno:
    { "url": "/uploads/abc123.jpg" }
    """
    
    # 1. Verifica se é uma imagem
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Tipo de arquivo não permitido. Use: JPG, PNG, WebP ou GIF"
        )
    
    # 2. Limita tamanho (5MB)
    max_size = 5 * 1024 * 1024  # 5MB em bytes
    contents = await file.read()
    if len(contents) > max_size:
        raise HTTPException(
            status_code=400,
            detail="Arquivo muito grande. Máximo: 5MB"
        )
    
    # 3. Gera nome único
    # uuid4() gera algo como: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    unique_name = f"{uuid.uuid4()}.{extension}"
    
    # 4. Salva o arquivo
    file_path = UPLOAD_DIR / unique_name
    with open(file_path, "wb") as f:
        f.write(contents)
    
    # 5. Retorna a URL
    return {"url": f"/uploads/{unique_name}"}


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


@app.get("/cardapio", response_class=HTMLResponse, tags=["Frontend"])
@app.get("/cardapio.html", response_class=HTMLResponse, tags=["Frontend"])
def serve_cardapio():
    """Gerenciamento de Cardápio - acesse /cardapio"""
    frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "cardapio.html")
    if os.path.exists(frontend_path):
        with open(frontend_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Arquivo não encontrado</h1><p>Coloque o frontend na pasta ../frontend/</p>", status_code=404)


@app.get("/clientes", response_class=HTMLResponse, tags=["Frontend"])
@app.get("/clientes.html", response_class=HTMLResponse, tags=["Frontend"])
def serve_clientes():
    """Cadastro de Clientes - acesse /clientes"""
    frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "clientes.html")
    if os.path.exists(frontend_path):
        with open(frontend_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Arquivo não encontrado</h1><p>Coloque o frontend na pasta ../frontend/</p>", status_code=404)
