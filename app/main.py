import os
from urllib.parse import quote
from fastapi import FastAPI, Request, Depends, HTTPException, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, StreamingResponse, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from xhtml2pdf import pisa
from io import BytesIO
from .database import engine, Base, get_db, SessionLocal
from .routers import analyses, auth, patients, admin
from .auth import get_current_user, get_password_hash, COOKIE_SECURE
from . import models

Base.metadata.create_all(bind=engine)


def verifier_configuration():
    """Affiche dans les logs quelles variables sont presentes. Jamais les valeurs."""
    attendues = ["SECRET_KEY", "DATABASE_URL", "ADMIN_EMAIL", "ADMIN_PASSWORD",
                 "BREVO_API_KEY", "SENDER_EMAIL", "BASE_URL"]
    etat = " | ".join(
        f"{nom}: {'ok' if os.getenv(nom) else 'MANQUANT'}" for nom in attendues
    )
    print(f"[config] {etat}")


verifier_configuration()

app = FastAPI(title="API Analyse Médicale SaaS")
templates = Jinja2Templates(directory="templates")

# Inclusion des routeurs
app.include_router(analyses.router)
app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(admin.router)

class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

app.add_middleware(NoCacheMiddleware)

# Création de l'admin par défaut (sécurisé par variables d'environnement)
def creer_admin_par_defaut():
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")
    
    if not admin_email or not admin_password:
        print("⚠️ ADMIN_EMAIL ou ADMIN_PASSWORD non configurés. Admin non créé.")
        return

    db = SessionLocal()
    try:
        admin = db.query(models.UserDB).filter(models.UserDB.is_admin == True).first()
        if not admin:
            labo_admin = models.LaboDB(nom="MedicLab Admin")
            db.add(labo_admin)
            db.commit()
            db.refresh(labo_admin)
            
            admin_user = models.UserDB(
                email=admin_email,
                hashed_password=get_password_hash(admin_password),
                is_admin=True,
                labo_id=labo_admin.id
            )
            db.add(admin_user)
            db.commit()
            print(f"✅ Compte admin créé : {admin_email}")
        else:
            print(f"ℹ️ Compte admin existant : {admin.email}")
    finally:
        db.close()

creer_admin_par_defaut()

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/login")
def login_page(request: Request, next_url: str = Query("/", alias="next"), expired: int = 0):
    return templates.TemplateResponse("login.html", {
        "request": request,
        "next": next_url,
        "expired": expired,
    })

@app.get("/forgot-password")
def forgot_password_page(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request})

@app.get("/reset-password")
def reset_password_page(request: Request):
    return templates.TemplateResponse("reset_password.html", {"request": request})

@app.get("/patients")
def patients_page(request: Request, current_user: models.UserDB = Depends(get_current_user)):
    return templates.TemplateResponse("patients.html", {"request": request})

@app.get("/admin")
def admin_page(request: Request, current_user: models.UserDB = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Accès refusé")
    return templates.TemplateResponse("admin.html", {"request": request})

@app.get("/")
def read_root(request: Request, db: Session = Depends(get_db), current_user: models.UserDB = Depends(get_current_user)):
    patients_list = db.query(models.Patient).filter(models.Patient.labo_id == current_user.labo_id).all()
    analyses_list = db.query(models.AnalyseDB).filter(models.AnalyseDB.labo_id == current_user.labo_id).order_by(models.AnalyseDB.created_at.desc()).all()

    total_patients = db.query(models.Patient).filter(models.Patient.labo_id == current_user.labo_id).count()
    total_analyses = db.query(models.AnalyseDB).filter(models.AnalyseDB.labo_id == current_user.labo_id).count()
    analyses_en_cours = db.query(models.AnalyseDB).filter(models.AnalyseDB.labo_id == current_user.labo_id, models.AnalyseDB.statut == "En cours").count()
    analyses_terminees = db.query(models.AnalyseDB).filter(models.AnalyseDB.labo_id == current_user.labo_id, models.AnalyseDB.statut == "Terminé").count()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "patients": patients_list,
        "analyses": analyses_list,
        "total_patients": total_patients,
        "total_analyses": total_analyses,
        "analyses_en_cours": analyses_en_cours,
        "analyses_terminees": analyses_terminees
    })

@app.get("/logout")
def logout(request: Request):
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(key="access_token", path="/", samesite="lax", secure=COOKIE_SECURE)
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
    chemin = request.url.path
    est_api = chemin.startswith("/api/")

    # Les clients d'API doivent recevoir du JSON, pas une page HTML de connexion.
    if est_api:
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)

    if exc.status_code == 401:
        # On memorise la page demandee pour y revenir apres connexion.
        cible = "/login?expired=1&next=" + quote(chemin, safe="/")
        return RedirectResponse(url=cible, status_code=302)

    return templates.TemplateResponse(
        "error.html",
        {"request": request, "error": exc.detail},
        status_code=exc.status_code,
    )