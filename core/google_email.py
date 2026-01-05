import base64
import logging
import time
from email.message import EmailMessage
from typing import Iterable, Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

_token_cache = {"access_token": None, "expires_at": 0.0}


class GoogleEmailError(Exception):
    pass


def _get_access_token() -> str:
    now = time.time()
    if _token_cache["access_token"] and _token_cache["expires_at"] - 30 > now:
        return _token_cache["access_token"]

    client_id = settings.GOOGLE_OAUTH_CLIENT_ID
    client_secret = settings.GOOGLE_OAUTH_CLIENT_SECRET
    refresh_token = settings.GOOGLE_OAUTH_REFRESH_TOKEN
    if not client_id or not client_secret or not refresh_token:
        raise GoogleEmailError("Faltan credenciales de Google OAuth (client_id/client_secret/refresh_token).")

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }
    try:
        resp = requests.post(token_url, data=data, timeout=15)
    except Exception as exc:  # pragma: no cover
        raise GoogleEmailError(f"Error de red al obtener token: {exc}") from exc

    if resp.status_code != 200:
        raise GoogleEmailError(f"Token Google fallo: {resp.status_code} {resp.text}")

    payload = resp.json()
    access_token = payload.get("access_token")
    expires_in = payload.get("expires_in", 0)
    if not access_token:
        raise GoogleEmailError("La respuesta de token no incluyo access_token.")

    _token_cache["access_token"] = access_token
    _token_cache["expires_at"] = now + int(expires_in)
    return access_token


def _normalize_addresses(addresses: Optional[Iterable[str] | str]) -> list[str]:
    if not addresses:
        return []
    if isinstance(addresses, str):
        return [addresses]
    return [addr for addr in addresses if addr]


def send_google_mail(
    to: str | Iterable[str],
    subject: str,
    html_body: Optional[str] = None,
    text_body: Optional[str] = None,
    cc: Optional[Iterable[str]] = None,
    bcc: Optional[Iterable[str]] = None,
) -> None:
    from_email = settings.GOOGLE_GMAIL_SENDER
    if not from_email:
        raise GoogleEmailError("GOOGLE_GMAIL_SENDER no esta configurado.")

    to_list = _normalize_addresses(to)
    cc_list = _normalize_addresses(cc)
    bcc_list = _normalize_addresses(bcc)
    if not to_list:
        raise GoogleEmailError("No se proporcionaron destinatarios.")

    msg = EmailMessage()
    msg["From"] = from_email
    msg["To"] = ", ".join(to_list)
    if cc_list:
        msg["Cc"] = ", ".join(cc_list)
    if bcc_list:
        msg["Bcc"] = ", ".join(bcc_list)
    msg["Subject"] = subject

    if html_body and text_body:
        msg.set_content(text_body)
        msg.add_alternative(html_body, subtype="html")
    elif html_body:
        msg.set_content(" ")
        msg.add_alternative(html_body, subtype="html")
    elif text_body:
        msg.set_content(text_body)
    else:
        raise GoogleEmailError("No se proporciono cuerpo del mensaje.")

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    access_token = _get_access_token()
    url = f"https://gmail.googleapis.com/gmail/v1/users/{from_email}/messages/send"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    payload = {"raw": raw}
    resp = requests.post(url, json=payload, headers=headers, timeout=15)
    if resp.status_code not in (200, 202):
        logger.error("Gmail send fallo: %s %s", resp.status_code, resp.text)
        raise GoogleEmailError(f"Gmail send fallo: {resp.status_code} {resp.text}")
