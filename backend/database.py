"""
Configuração do banco de dados (PostgreSQL em produção, SQLite em desenvolvimento)
"""
import os
from sqlmodel import SQLModel, create_engine, Session

# Pega DATABASE_URL do ambiente (Railway define automaticamente para PostgreSQL)
DATABASE_URL = os.environ.get("DATABASE_URL")

# Detecta se é PostgreSQL ou SQLite
if DATABASE_URL and DATABASE_URL.startswith(("postgres://", "postgresql://")):
    # PostgreSQL (produção - Railway)
    # Railway usa 'postgres://' mas SQLAlchemy precisa de 'postgresql://'
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    engine = create_engine(
        DATABASE_URL,
        echo=False,  # Mude para True se quiser ver as queries SQL
        pool_pre_ping=True,  # Verifica conexão antes de usar
        pool_recycle=300,  # Recicla conexões a cada 5 minutos
    )
    print("🐘 Usando PostgreSQL")
else:
    # SQLite (desenvolvimento local)
    DATA_DIR = os.environ.get("DATA_DIR", ".")
    DATABASE_PATH = os.path.join(DATA_DIR, "motoboy.db")
    DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

    engine = create_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False}  # Necessário para SQLite com FastAPI
    )
    print("📁 Usando SQLite:", DATABASE_PATH)


def create_db_and_tables():
    """Cria o banco e as tabelas"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Dependency para injetar sessão nas rotas"""
    with Session(engine) as session:
        yield session
