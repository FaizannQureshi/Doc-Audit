from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers.audit import router as audit_router
from app.api.routers.auth import router as auth_router
from app.api.routers.drive import router as drive_router
from app.core.db import engine
from app.models import Base

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth")
app.include_router(drive_router, prefix="/drive")
app.include_router(audit_router, prefix="/audit")


@app.on_event("startup")
def _startup():
    # Phase 2 baseline: auto-create tables in dev.
    # In production, move this to Alembic migrations.
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"message": "Doc Audit System Running"}
