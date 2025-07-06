from fastapi import FastAPI
from app.authentication.router import router as router_auth
from app.files.router import router as router_files
from app.database import init_db, close_db

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.on_event("shutdown")
async def shutdown_event():
    await close_db()

@app.get("/healthcheck")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}

app.include_router(router_auth, prefix="")
app.include_router(router_files, prefix="/files")