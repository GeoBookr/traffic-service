from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

DATABASE_URL = settings.DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    echo=settings.DEBUG,
    connect_args={"sslmode": "disable"},
    isolation_level="SERIALIZABLE"
)
SessionLocal = sessionmaker(bind=engine)
