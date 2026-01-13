"""
MotoFlash - Sistema de Despacho Inteligente para Entregas

MVP V0.1

Execute com: uvicorn main:app --reload
Docs: http://localhost:8000/docs
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from database import create_db_and_tables
from routers import orders_router, couriers_router, dispatch_router


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
    
    ## Fluxo
    
    1. Pedido é criado → QR Code gerado
    2. Cozinha bipa QR → Pedido fica PRONTO
    3. Dispatch agrupa pedidos por proximidade
    4. Motoqueiro recebe lote de entregas
    5. Motoqueiro finaliza → Disponível para novo lote
    """,
    version="0.1.0",
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
        "version": "0.1.0",
        "docs": "/docs",
        "status": "running"
    }


# Rota de health check
@app.get("/health", tags=["Root"])
def health():
    return {"status": "healthy"}


# Serve o frontend React (depois de buildar)
# Descomente quando tiver o build do React
# if os.path.exists("static"):
#     app.mount("/static", StaticFiles(directory="static"), name="static")
#     
#     @app.get("/{full_path:path}")
#     def serve_react(full_path: str):
#         return FileResponse("static/index.html")
