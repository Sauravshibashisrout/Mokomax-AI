import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, JSONResponse
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config as StarletteConfig

from app.config import get_settings
from app.db.mongo import users_col

router = APIRouter()
logger = logging.getLogger(__name__)

cfg = get_settings()

_starlette_config = StarletteConfig(environ={
    "GOOGLE_CLIENT_ID": cfg.google_client_id,
    "GOOGLE_CLIENT_SECRET": cfg.google_client_secret,
})

oauth = OAuth(_starlette_config)
oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


@router.get("/auth/login")
async def login(request: Request):
    redirect_uri = cfg.google_redirect_uri
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/auth/callback")
async def auth_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo")
    if not user_info:
        return JSONResponse({"error": "OAuth failed"}, status_code=400)

    email = user_info["email"]
    await users_col().update_one(
        {"email": email},
        {"$set": {
            "email": email,
            "name": user_info.get("name"),
            "picture": user_info.get("picture"),
            "last_login": datetime.now(timezone.utc).isoformat(),
        }},
        upsert=True,
    )
    logger.info("User logged in: %s", email)

    # Redirect to frontend with user info as query params (simple approach)
    redirect = f"{cfg.frontend_url}?email={email}&name={user_info.get('name','')}"
    return RedirectResponse(redirect)


@router.get("/auth/me")
async def get_me(request: Request):
    # In production, validate a session token/JWT here
    return {"message": "Implement JWT session validation"}
