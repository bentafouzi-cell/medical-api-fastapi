from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from .database import engine, Base
from .routers import analyses

Base.metadata.create_all(bind=engine)

app = FastAPI(title="API Analyse Médicale SaaS")

# Configuration pour lire les fichiers HTML dans le dossier "templates"
templates = Jinja2Templates(directory="templates")

# On inclut les routes de l'API
app.include_router(analyses.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}

# NOUVELLE ROUTE : Afficher la page d'accueil (le tableau de bord)
@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})