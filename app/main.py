from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.orm import Session
from .database import engine, Base, get_db
from .routers import analyses, auth, patients
from .auth import get_current_user
from . import models

# Création automatique des tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="API Analyse Médicale SaaS")
templates = Jinja2Templates(directory="templates")

# Inclusion des routeurs
app.include_router(analyses.router)
app.include_router(auth.router)
app.include_router(patients.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/forgot-password")
def forgot_password_page(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request})

@app.get("/reset-password")
def reset_password_page(request: Request):
    return templates.TemplateResponse("reset_password.html", {"request": request})

@app.get("/patients")
def patients_page(request: Request, current_user: models.UserDB = Depends(get_current_user)):
    return templates.TemplateResponse("patients.html", {"request": request})

# ROUTE RACINE SÉCURISÉE (Nécessite d'être connecté)
@app.get("/")
def read_root(request: Request, db: Session = Depends(get_db), current_user: models.UserDB = Depends(get_current_user)):
    patients_list = db.query(models.Patient).filter(models.Patient.labo_id == current_user.labo_id).all()
    analyses_list = db.query(models.AnalyseDB).filter(models.AnalyseDB.labo_id == current_user.labo_id).order_by(models.AnalyseDB.created_at.desc()).all()
    
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "patients": patients_list,
        "analyses": analyses_list
    })

# NOUVELLE ROUTE : DÉCONNEXION (Supprime le cookie et redirige)
@app.get("/logout")
def logout(request: Request):
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(key="access_token")
    return response

# Gestionnaire d'erreurs 401 (Redirige vers login si non autorisé)
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 401:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("error.html", {"request": request, "error": exc.detail})