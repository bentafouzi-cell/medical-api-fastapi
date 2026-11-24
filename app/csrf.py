"""Protection contre le falsification de requete intersite (CSRF).

Principe : le serveur depose un cookie aleatoire, puis signe sa valeur avec
SECRET_KEY. Le jeton signe est le seul element a soumettre avec le formulaire.
Un site tiers peut bien faire envoyer le cookie par le navigateur, il ne peut
pas produire la signature : sans SECRET_KEY, le jeton est impossible a forger.

Pourquoi signer plutot que comparer simplement cookie et champ (double submit) :
si un autre service heberge sur le meme domaine parent peut ecrire un cookie,
il ecraserait la valeur mais resterait incapable de calculer la signature.
"""
import hashlib
import hmac
import secrets

from fastapi import HTTPException, Request

from .auth import COOKIE_SECURE, SECRET_KEY

NOM_COOKIE = "csrf"
NOM_CHAMP = "csrf_token"
NOM_EN_TETE = "X-CSRF-Token"
DUREE_COOKIE = 12 * 3600

METHODES_SANS_VERIFICATION = {"GET", "HEAD", "OPTIONS", "TRACE"}


def signer(valeur: str) -> str:
    return hmac.new(
        SECRET_KEY.encode("utf-8"), valeur.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def jeton_depuis_requete(request: Request) -> str:
    """Jeton a inserer dans les formulaires et a envoyer par JavaScript."""
    valeur = getattr(request.state, "csrf_valeur", "")
    return signer(valeur) if valeur else ""


class CsrfCookieMiddleware:
    """Garantit qu'un cookie CSRF existe avant tout traitement, y compris
    pour une page de connexion anonyme. Pose le cookie sur la reponse finale,
    ce qui fonctionne aussi avec une redirection."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        valeur = request.cookies.get(NOM_COOKIE)
        nouveau = not valeur
        if nouveau:
            valeur = secrets.token_urlsafe(32)
        scope.setdefault("state", {})["csrf_valeur"] = valeur

        async def send_avec_cookie(message):
            if nouveau and message["type"] == "http.response.start":
                entetes = list(message.get("headers", []))
                cookie = (
                    f"{NOM_COOKIE}={valeur}; Path=/; Max-Age={DUREE_COOKIE}; "
                    f"HttpOnly; SameSite=lax"
                )
                if COOKIE_SECURE:
                    cookie += "; Secure"
                entetes.append((b"set-cookie", cookie.encode("latin-1")))
                message = {**message, "headers": entetes}
            await send(message)

        await self.app(scope, receive, send_avec_cookie)


async def verifier_csrf(request: Request) -> None:
    """Dependance globale : rejette toute ecriture sans jeton valide.

    Le formulaire peut fournir le jeton par le champ cache csrf_token, ou par
    l'en-tete X-CSRF-Token pour les appels JavaScript.
    """
    if request.method in METHODES_SANS_VERIFICATION:
        return

    valeur_cookie = getattr(request.state, "csrf_valeur", "")
    fourni = request.headers.get(NOM_EN_TETE, "").strip()

    if not fourni:
        type_contenu = request.headers.get("content-type", "")
        if "form" in type_contenu:
            formulaire = await request.form()
            fourni = str(formulaire.get(NOM_CHAMP) or "").strip()

    # Un cookie absent (navigateur neuf) ne peut pas valider une ecriture : le
    # middleware vient de le creer, la page doit donc etre rechargee.
    if not valeur_cookie or not fourni or not hmac.compare_digest(fourni, signer(valeur_cookie)):
        raise HTTPException(
            status_code=403,
            detail=(
                "Jeton de securite manquant ou invalide. "
                "Rechargez la page puis recommencez."
            ),
        )
