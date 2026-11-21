from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from .database import engine, Base
from .routers import analyses, auth, patients
from .auth import get_current_user
from . import models

Base.metadata.create_all(bind=engine)

app = FastAPI(title="API Analyse Médicale SaaS")
templates = Jinja2Templates(directory="templates")

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
def patients_page(request: Request):
    return templates.TemplateResponse("patients.html", {"request": request})
    
@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 401:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("error.html", {"request": request, "error": exc.detail})