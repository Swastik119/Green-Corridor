from sqlalchemy.orm import sessionmaker
from app.database.connection import engine


# Create a reusable session factory
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)


# Provide a database session to API endpoints
def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()