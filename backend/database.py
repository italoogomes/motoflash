"""
Configuração do banco de dados SQLite
"""
import os
from sqlmodel import SQLModel, create_engine, Session

# Verifica se está em produção (Render) ou desenvolvimento local
# No Render, usa /data para persistência
DATA_DIR = os.environ.get("DATA_DIR", ".")
DATABASE_PATH = os.path.join(DATA_DIR, "motoboy.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(
    DATABASE_URL, 
    echo=False,  # Mude para True se quiser ver as queries SQL
    connect_args={"check_same_thread": False}  # Necessário para SQLite com FastAPI
)


def create_db_and_tables():
    """Cria o banco e as tabelas"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Dependency para injetar sessão nas rotas"""
    with Session(engine) as session:
        yield session
