"""
Configuração do banco de dados SQLite
"""
from sqlmodel import SQLModel, create_engine, Session

# SQLite - simples e portátil para MVP
DATABASE_URL = "sqlite:///./motoboy.db"

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
