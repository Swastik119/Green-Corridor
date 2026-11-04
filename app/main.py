from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database.session import get_db

app = FastAPI(
    title="Green Corridor API",
    description="Emergency Ambulance Coordination System",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "Green Corridor Backend is Running!"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.get("/database-check")
def database_check(db: Session = Depends(get_db)):

    result = db.execute(
        text("SELECT current_database(), current_user")
    )

    row = result.fetchone()

    return {
        "database": row[0],
        "user": row[1],
        "connection": "successful"
    }