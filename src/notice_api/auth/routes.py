import functools
from typing import Any, cast

import httpx
from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Request

from notice_api.core.config import settings

from .types import OnAfterTokenResponse, StarletteOAuthApp

router = APIRouter()

oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.GOOGLE_OAUTH_CLIENT_ID,
    client_secret=settings.GOOGLE_OAUTH_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    scope="openid email profile",
)
oauth.register(
    name="nycu",
    client_id=settings.NYCU_OAUTH_CLIENT_ID,
    client_secret=settings.NYCU_OAUTH_CLIENT_SECRET,
    authorize_url="https://id.nycu.edu.tw/o/authorize/",
    token_endpoint="https://id.nycu.edu.tw/o/token/",
    scope="profile",
)

after_token_hooks: dict[str, list[OnAfterTokenResponse]] = {}


def after_token_response(provider: str):
    @functools.wraps(after_token_response)
    def decorator(func: OnAfterTokenResponse):
        after_token_hooks.setdefault(provider, []).append(func)
        return func

    return decorator


@after_token_response("nycu")
async def fetch_ncyu_profile(token: dict[str, Any]):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://id.nycu.edu.tw/api/profile/",
            headers={"Authorization": f"Bearer {token['access_token']}"},
        )
        response.raise_for_status()
        token["userinfo"] = response.json()


@router.get("/api/auth/login/{provider}")
async def login(request: Request, provider: str):
    redirect_uri = request.url_for("oauth_callback", provider=provider)
    oauth_client = cast(StarletteOAuthApp, oauth.create_client(provider))
    return await oauth_client.authorize_redirect(request, redirect_uri)


@router.get("/api/auth/callback/{provider}")
async def oauth_callback(request: Request, provider: str):
    oauth_client = cast(StarletteOAuthApp, oauth.create_client(provider))
    token = await oauth_client.authorize_access_token(request)
    for hook in after_token_hooks[provider]:
        await hook(token)

    return token["userinfo"]
