from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Charge le fichier .env en local. Sur Render les variables existent deja :
# load_dotenv n'ecrase jamais une variable deja definie.
load_dotenv()

# Récupère l'URL de la DB depuis les variables d'environnement Render
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise Exception("❌ DATABASE_URL non configurée dans Render !")

# Création du moteur avec gestion automatique des déconnexions
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,       # ✅ Vérifie la connexion avant chaque utilisation (Ping)
    pool_recycle=3600,        # ✅ Recycle les connexions après 1h pour éviter les timeouts
    pool_size=5,              # Taille du pool (optionnel, ajuste selon tes besoins)
    max_overflow=10           # Overflow max (optionnel)
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dépendance pour obtenir une session DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()