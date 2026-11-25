from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database.session import get_db
from app.api.v1.emergency_requests import router as emergency_request_router
from app.api.v1 import routing
from app.api.v1 import notifications
from app.api.v1.dashboard_api import router as dashboard_router
from app.api.v1.tracking import router as tracking_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.ai import router as ai_router
from app.websocket.routes import router as websocket_router
from app import auth, users

import os

app = FastAPI(
    title="Green Corridor API",
    description="Emergency Ambulance Coordination System",
    version="1.0.0"
)

# ---------------------------------------------------------------------------
# CORS Middleware (for local development)
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Static files & Jinja2 templates
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# ---------------------------------------------------------------------------
# Existing API routers (kept intact)
# ---------------------------------------------------------------------------
# Phase 3 routers
app.include_router(auth.router)
app.include_router(users.router)

# Phase 4 router
app.include_router(emergency_request_router)

# Phase 5 router
app.include_router(routing.router)
app.include_router(notifications.router)

# Phase 6 – Dashboard API (simulated data)
app.include_router(dashboard_router)

# Phase 8 – Real-Time Tracking & WebSockets
app.include_router(tracking_router)
app.include_router(websocket_router)

# Phase 9 – Persistent Alerts & Fault-Tolerant Communication
app.include_router(alerts_router)

# Phase 10 – AI Mission Intelligence
app.include_router(ai_router)

# ---------------------------------------------------------------------------
# Template routes – serve HTML pages
# ---------------------------------------------------------------------------

@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")


@app.get("/control-room")
def control_room_page(request: Request):
    return templates.TemplateResponse(request=request, name="control_room.html")


@app.get("/ambulance-management")
def ambulance_management_page(request: Request):
    return templates.TemplateResponse(request=request, name="ambulance.html")


@app.get("/hospital-management")
def hospital_management_page(request: Request):
    return templates.TemplateResponse(request=request, name="hospital.html")


@app.get("/traffic-control")
def traffic_control_page(request: Request):
    return templates.TemplateResponse(request=request, name="traffic.html")


@app.get("/about")
def about_page(request: Request):
    return templates.TemplateResponse(request=request, name="about.html")


@app.get("/contact")
def contact_page(request: Request):
    return templates.TemplateResponse(request=request, name="contact.html")


@app.get("/mission/{mission_id}")
def mission_detail_page(request: Request, mission_id: str):
    return templates.TemplateResponse(
        request=request,
        name="mission_detail.html",
        context={"mission_id": mission_id},
    )


# ---------------------------------------------------------------------------
# Utility / health-check routes (kept intact)
# ---------------------------------------------------------------------------

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
