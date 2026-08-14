"""
Camada de acesso a dados — configuração do engine SQLAlchemy.

MVP usa SQLite (arquivo local .db, sem servidor). A troca para Postgres/Supabase
no futuro exige apenas alterar DATABASE_URL abaixo (ex.:
"postgresql://user:pass@host:5432/gestorupa") — nenhuma lógica de negócio
em kpis/, pages/ ou simulador/ depende do dialeto do banco.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "gestorupa.db")

# Para migrar para Postgres/Supabase: troque apenas esta string de conexão.
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_session():
    """Retorna uma nova sessão de banco de dados."""
    return SessionLocal()


def init_db():
    """Cria todas as tabelas definidas em data/models.py, se ainda não existirem."""
    from data import models  # noqa: F401  (garante que os modelos sejam registrados)
    Base.metadata.create_all(bind=engine)


def reset_db():
    """Apaga e recria todas as tabelas. Usado apenas pela rotina de importação."""
    from data import models  # noqa: F401
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
