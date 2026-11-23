FROM python:3.9-slim

# Logs visibles immediatement dans Render, pas de fichiers .pyc dans l'image
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONIOENCODING=utf-8 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependances d'abord : cette couche reste en cache tant que requirements.txt
# ne change pas. Les deploiements suivants ne reinstallent plus tout.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# .dockerignore exclut venv/, .env et les bases SQLite : ni secrets ni donnees
# patients ne doivent entrer dans l'image.
COPY . .

EXPOSE 8000

# Le module est app/main.py : "main:app" ne correspond a aucun fichier.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
