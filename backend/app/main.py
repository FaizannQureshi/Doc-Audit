from fastapi import FastAPI
from app.auth import router as auth_router
from app.drive import router as drive_router
from app.audit import router as audit_router

app = FastAPI()

app.include_router(auth_router, prefix="/auth")
app.include_router(drive_router, prefix="/drive")
app.include_router(audit_router, prefix="/audit")

@app.get("/")
def root():
    return {"message": "Doc Audit System Running"}