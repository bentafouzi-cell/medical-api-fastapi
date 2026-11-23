from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, StreamingResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from xhtml2pdf import pisa
from io import BytesIO
from .database import engine, Base, get_db
from .routers import analyses, auth, patients
from .auth import get_current_user
from . import models

Base.metadata.create_all(bind=engine)

app = FastAPI(title="API Analyse Médicale SaaS")
templates = Jinja2Templates(directory="templates")

app.include_router(analyses.router)
app.include_router(auth.router)
app.include_router(patients.router)


class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response


app.add_middleware(NoCacheMiddleware)


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


@app.get("/")
def read_root(request: Request, db: Session = Depends(get_db), current_user: models.UserDB = Depends(get_current_user)):
    patients_list = db.query(models.Patient).filter(models.Patient.labo_id == current_user.labo_id).all()
    analyses_list = db.query(models.AnalyseDB).filter(models.AnalyseDB.labo_id == current_user.labo_id).order_by(models.AnalyseDB.created_at.desc()).all()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "patients": patients_list,
        "analyses": analyses_list
    })


@app.get("/logout")
def logout(request: Request):
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(key="access_token")
    return response


@app.get("/analyse/{analyse_id}")
def analyse_detail_page(analyse_id: int, request: Request, db: Session = Depends(get_db), current_user: models.UserDB = Depends(get_current_user)):
    analyse = db.query(models.AnalyseDB).filter(
        models.AnalyseDB.id == analyse_id,
        models.AnalyseDB.labo_id == current_user.labo_id
    ).first()
    if not analyse:
        raise HTTPException(status_code=404, detail="Analyse non trouvée")
    return templates.TemplateResponse("detail.html", {"request": request, "analyse": analyse})


@app.get("/analyse/{analyse_id}/pdf")
def generate_analyse_pdf(analyse_id: int, db: Session = Depends(get_db), current_user: models.UserDB = Depends(get_current_user)):
    analyse = db.query(models.AnalyseDB).filter(
        models.AnalyseDB.id == analyse_id,
        models.AnalyseDB.labo_id == current_user.labo_id
    ).first()
    if not analyse:
        raise HTTPException(status_code=404, detail="Analyse non trouvée")

    html = templates.env.get_template("rapport_pdf.html").render(analyse=analyse)

    buffer = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=buffer)
    if pisa_status.err:
        raise HTTPException(status_code=500, detail="Erreur lors de la génération du PDF")

    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=Rapport_MedicLab_{analyse.id}.pdf"}
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 401:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("error.html", {"request": request, "error": exc.detail})