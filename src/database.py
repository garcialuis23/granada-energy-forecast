from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.config import DATABASE_URL

# 1. Crear el motor de conexión
# pool_pre_ping=True es VITAL para Supabase: reconecta si la conexión se cae.
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# 2. Crear la fábrica de sesiones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# 3. Dependencia para inyectar en los endpoints (Tu get_db mejorado)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()