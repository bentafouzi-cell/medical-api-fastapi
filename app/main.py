from fastapi import FastAPI
from .database import engine, Base
from .routers import analyses

Base.metadata.create_all(bind=engine)

app = FastAPI(title="API Analyse Médicale SaaS")

app.include_router(analyses.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}