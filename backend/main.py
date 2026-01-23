"""
MotoFlash - Sistema de Despacho Inteligente para Entregas

MVP V0.9 - Polyline da rota real (Google)

Execute com: uvicorn main:app --reload
Docs: http://localhost:8000/docs
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, Response
import os
import uuid
import shutil
from pathlib import Path

from database import create_db_and_tables, get_session
from sqlmodel import Session
from fastapi import Depends
from routers import orders_router, couriers_router, dispatch_router
from routers.menu import router as menu_router
from routers.customers import router as customers_router
from routers.settings import router as settings_router
from routers.auth import router as auth_router
from routers.invites import router as invites_router
from services.geocoding_service import geocode_address_detailed
from services.dispatch_service import get_batch_route_polyline

# Pasta para uploads de imagens
# Em produção (Railway), usa /data/uploads para persistência
DATA_DIR = os.environ.get("DATA_DIR", "/data")
# Se /data não existir, usa a pasta local
if not os.path.exists(DATA_DIR):
    DATA_DIR = str(Path(__file__).parent)

UPLOAD_DIR = Path(DATA_DIR) / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)  # Cria a pasta se não existir

# Pasta do frontend (agora em static/)
STATIC_DIR = Path(__file__).parent / "static"


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
    version="0.9.0",
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

# Serve ícones do PWA
# Exemplo: /icons/icon-192.png → static/icons/icon-192.png
ICONS_DIR = STATIC_DIR / "icons"
if ICONS_DIR.exists():
    app.mount("/icons", StaticFiles(directory=str(ICONS_DIR)), name="icons")

# Serve arquivos estáticos (CSS, JS, etc)
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Registra as rotas
app.include_router(orders_router)
app.include_router(couriers_router)
app.include_router(dispatch_router)
app.include_router(menu_router)
app.include_router(customers_router)
app.include_router(settings_router)
app.include_router(auth_router)
app.include_router(invites_router)


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
        "version": "0.9.0",
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


# ============ POLYLINE DA ROTA (V0.9) ============

@app.get("/batches/{batch_id}/polyline", tags=["Dispatch"])
def get_polyline(batch_id: str, session: Session = Depends(get_session)):
    """
    Retorna a polyline da rota do batch para desenhar no mapa.
    
    Usa Google Directions API para obter a rota REAL
    (seguindo as ruas, não linha reta).
    
    Retorna:
    - polyline: string encoded (formato Google)
    - start: coordenadas do restaurante
    - orders: lista de coordenadas dos pedidos
    
    O frontend decodifica a polyline e desenha no mapa Leaflet.
    """
    result = get_batch_route_polyline(session, batch_id)
    if not result:
        raise HTTPException(status_code=404, detail="Batch não encontrado ou sem pedidos")
    return result


# ============ SERVE FRONTEND ============
# Agora os arquivos estão em static/

# PWA - Manifest
@app.get("/manifest.json", tags=["PWA"])
def serve_manifest():
    """Manifest do PWA"""
    manifest_path = STATIC_DIR / "manifest.json"
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            return Response(content=f.read(), media_type="application/manifest+json")
    return Response(content="{}", media_type="application/json", status_code=404)

# PWA - Service Worker
@app.get("/sw.js", tags=["PWA"])
def serve_service_worker():
    """Service Worker do PWA"""
    sw_path = STATIC_DIR / "sw.js"
    if sw_path.exists():
        with open(sw_path, "r", encoding="utf-8") as f:
            return Response(content=f.read(), media_type="application/javascript")
    return Response(content="// Service Worker not found", media_type="application/javascript", status_code=404)

@app.get("/motoboy", response_class=HTMLResponse, tags=["Frontend"])
@app.get("/motoboy.html", response_class=HTMLResponse, tags=["Frontend"])
def serve_motoboy():
    """App do Motoboy - acesse /motoboy no celular"""
    motoboy_path = STATIC_DIR / "motoboy.html"
    if motoboy_path.exists():
        with open(motoboy_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Arquivo não encontrado</h1><p>Coloque motoboy.html na pasta static/</p>", status_code=404)


@app.get("/dashboard", response_class=HTMLResponse, tags=["Frontend"])
@app.get("/index.html", response_class=HTMLResponse, tags=["Frontend"])
def serve_dashboard():
    """Dashboard do Restaurante - acesse /dashboard"""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Arquivo não encontrado</h1><p>Coloque index.html na pasta static/</p>", status_code=404)


@app.get("/cardapio", response_class=HTMLResponse, tags=["Frontend"])
@app.get("/cardapio.html", response_class=HTMLResponse, tags=["Frontend"])
def serve_cardapio():
    """Gerenciamento de Cardápio - acesse /cardapio"""
    cardapio_path = STATIC_DIR / "cardapio.html"
    if cardapio_path.exists():
        with open(cardapio_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Arquivo não encontrado</h1><p>Coloque cardapio.html na pasta static/</p>", status_code=404)


@app.get("/clientes", response_class=HTMLResponse, tags=["Frontend"])
@app.get("/clientes.html", response_class=HTMLResponse, tags=["Frontend"])
def serve_clientes():
    """Cadastro de Clientes - acesse /clientes"""
    clientes_path = STATIC_DIR / "clientes.html"
    if clientes_path.exists():
        with open(clientes_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Arquivo não encontrado</h1><p>Coloque clientes.html na pasta static/</p>", status_code=404)


# ============ AUTENTICAÇÃO (MULTI-RESTAURANTE) ============

@app.get("/cadastro", tags=["Autenticação"])
@app.get("/cadastro.html", tags=["Autenticação"])
def serve_cadastro():
    """Redireciona para /login (cadastro agora é na mesma tela)"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/login")


@app.get("/login", response_class=HTMLResponse, tags=["Autenticação"])
@app.get("/login.html", response_class=HTMLResponse, tags=["Autenticação"])
def serve_login():
    """Login e Cadastro - acesse /login"""
    # Novo arquivo unificado: auth.html (login + cadastro)
    auth_path = STATIC_DIR / "auth.html"
    if auth_path.exists():
        with open(auth_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Arquivo não encontrado</h1><p>Coloque auth.html na pasta static/</p>", status_code=404)


@app.get("/convite/{code}", response_class=HTMLResponse, tags=["Convites"])
def serve_convite(code: str):
    """
    Página de convite para motoboy
    
    O motoboy acessa esse link (recebido por WhatsApp) para entrar na equipe.
    A página valida o código e permite o cadastro.
    """
    convite_path = STATIC_DIR / "convite.html"
    if convite_path.exists():
        with open(convite_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Arquivo não encontrado</h1><p>Coloque convite.html na pasta static/</p>", status_code=404)


@app.get("/recuperar-senha/{code}", response_class=HTMLResponse, tags=["Autenticação"])
def serve_recuperar_senha(code: str):
    """
    Página de recuperação de senha para motoboy
    
    O motoboy acessa esse link (recebido por WhatsApp) para redefinir a senha.
    """
    recuperar_path = STATIC_DIR / "recuperar-senha.html"
    if recuperar_path.exists():
        with open(recuperar_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Arquivo não encontrado</h1><p>Coloque recuperar-senha.html na pasta static/</p>", status_code=404)