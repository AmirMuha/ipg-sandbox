"""OAuth2 code exchange service for GitHub and Google (004-launch-readiness-flows).

Uses httpx (already an engine dependency). Allowlisted in test_simulation_guard.py.
"""

from typing import Any
import httpx

from src.config import Settings


async def exchange_github_code(code: str, settings: Settings) -> dict[str, Any]:
    """Exchange OAuth authorization code with GitHub and retrieve user profile."""
    if not settings.github_client_id or not settings.github_client_secret:
        raise ValueError("GitHub OAuth credentials not configured")

    async with httpx.AsyncClient(timeout=10.0) as client:
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
                "redirect_uri": settings.github_redirect_uri,
            },
        )
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise ValueError(f"GitHub token exchange failed: {token_data}")

        user_resp = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "ipg-sandbox",
            },
        )
        user_data = user_resp.json()

        # If primary email is private, query /user/emails
        email = user_data.get("email")
        if not email:
            emails_resp = await client.get(
                "https://api.github.com/user/emails",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "ipg-sandbox",
                },
            )
            if emails_resp.status_code == 200:
                for entry in emails_resp.json():
                    if entry.get("primary") and entry.get("verified"):
                        email = entry.get("email")
                        break

        if not email:
            email = f"gh_{user_data.get('id')}@github.user"

        return {
            "oauth_id": str(user_data.get("id")),
            "email": email.lower(),
            "full_name": user_data.get("name") or user_data.get("login"),
            "provider": "github",
        }


async def exchange_google_code(code: str, settings: Settings) -> dict[str, Any]:
    """Exchange OAuth authorization code with Google and retrieve user profile."""
    if not settings.google_client_id or not settings.google_client_secret:
        raise ValueError("Google OAuth credentials not configured")

    async with httpx.AsyncClient(timeout=10.0) as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise ValueError(f"Google token exchange failed: {token_data}")

        user_resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        user_data = user_resp.json()
        email = user_data.get("email")
        if not email:
            raise ValueError("Google userinfo did not provide email")

        return {
            "oauth_id": str(user_data.get("id")),
            "email": email.lower(),
            "full_name": user_data.get("name"),
            "provider": "google",
        }
