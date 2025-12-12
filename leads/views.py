import json
import logging
import os
from datetime import datetime

import requests
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt

from .models import MetaLead

logger = logging.getLogger(__name__)
META_VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN")
META_PAGE_TOKEN = os.getenv("META_PAGE_TOKEN")


def _normalize_key(name: str) -> str:
    return (name or "").strip().lower().replace(" ", "_")


def _split_field_data(field_data):
    raw_fields = {}
    normalized = {}

    for field in field_data or []:
        name = (field.get("name") or "").strip()
        values = field.get("values") or []

        if not name:
            continue

        value = values[0] if len(values) == 1 else values
        raw_fields[name] = value
        normalized[_normalize_key(name)] = value

    return raw_fields, normalized


def _pick_first(normalized_fields, candidates):
    for key in candidates:
        if key in normalized_fields:
            value = normalized_fields[key]
            if isinstance(value, list):
                return value[0] if value else None
            return value
    return None


def _parse_created_time(created_value, entry_time):
    if isinstance(created_value, str):
        try:
            return datetime.strptime(created_value, "%Y-%m-%dT%H:%M:%S%z")
        except ValueError:
            pass

    if isinstance(created_value, (int, float)):
        try:
            return datetime.fromtimestamp(created_value, tz=timezone.utc)
        except Exception:
            pass

    if entry_time:
        try:
            return datetime.fromtimestamp(int(entry_time) / 1000, tz=timezone.utc)
        except Exception:
            pass

    return timezone.now()


def fetch_and_save_meta_lead(leadgen_id: str):
    """
    Fetch full lead data from Meta Graph API and persist it.
    """
    if not META_PAGE_TOKEN:
        logger.error("META_PAGE_TOKEN no configurado; no se puede leer el lead %s", leadgen_id)
        return

    url = f"https://graph.facebook.com/v24.0/{leadgen_id}"
    params = {
        "access_token": META_PAGE_TOKEN,
        "fields": (
            "created_time,ad_id,ad_name,adset_id,adset_name,"
            "campaign_id,campaign_name,form_id,form_name,"
            "is_organic,platform,field_data"
        ),
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.HTTPError as exc:
        text = getattr(exc.response, "text", "") if hasattr(exc, "response") else ""
        logger.warning(
            "Meta Graph devolvio HTTP %s para lead %s. Body: %s",
            getattr(exc.response, "status_code", "unknown"),
            leadgen_id,
            (text or "")[:500],
        )
        return
    except Exception as exc:
        logger.exception("No se pudo obtener lead %s desde Meta: %s", leadgen_id, exc)
        return

    raw_fields = {}
    for field in data.get("field_data", []) or []:
        name = (field.get("name") or "").strip()
        values = field.get("values") or []
        if not name or not values:
            continue
        raw_fields[name] = values[0] if len(values) == 1 else values

    created_dt = parse_datetime(data.get("created_time") or "")
    if created_dt and timezone.is_naive(created_dt):
        created_dt = timezone.make_aware(created_dt, timezone.utc)

    defaults = {
        "created_time": created_dt or timezone.now(),
        "ad_id": data.get("ad_id") or "",
        "ad_name": data.get("ad_name") or "",
        "adset_id": data.get("adset_id") or "",
        "adset_name": data.get("adset_name") or "",
        "campaign_id": data.get("campaign_id") or "",
        "campaign_name": data.get("campaign_name") or "",
        "form_id": data.get("form_id") or "",
        "form_name": data.get("form_name") or "",
        "is_organic": data.get("is_organic") or False,
        "platform": data.get("platform") or "",
        "full_name": raw_fields.get("full_name"),
        "email": raw_fields.get("email"),
        "phone_number": raw_fields.get("phone_number"),
        "raw_fields": raw_fields,
        "raw_payload": data,
    }

    MetaLead.objects.update_or_create(
        leadgen_id=str(leadgen_id),
        defaults=defaults,
    )
    logger.info("Lead %s guardado desde Graph API", leadgen_id)


@login_required
def leads_lista(request):
    q = request.GET.get("q", "").strip()
    leads = MetaLead.objects.all().order_by("-created_time")

    if q:
        leads = leads.filter(
            Q(full_name__icontains=q)
            | Q(email__icontains=q)
            | Q(phone_number__icontains=q)
            | Q(campaign_name__icontains=q)
            | Q(form_name__icontains=q)
        )

    return render(request, "leads/lista.html", {"leads": leads, "q": q})


@csrf_exempt
def meta_lead_webhook(request):
    # Meta verification handshake
    if request.method == "GET":
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")

        if mode == "subscribe" and token == META_VERIFY_TOKEN:
            return HttpResponse(challenge)

        logger.warning("Webhook Meta verify failed: mode=%s token=%s", mode, token)
        return HttpResponse("Invalid verify token", status=403)

    if request.method == "POST":
        logger.info("Webhook Meta POST received: %s", request.body[:500])
        try:
            payload = json.loads(request.body.decode("utf-8", errors="ignore"))
        except Exception:
            logger.warning("Webhook Meta: JSON invalido o no parseable")
            return HttpResponse("ok")

        leadgen_ids = []
        if "entry" in payload:
            for entry in payload.get("entry", []):
                for change in entry.get("changes", []):
                    val = change.get("value") or {}
                    if val.get("leadgen_id"):
                        leadgen_ids.append(val.get("leadgen_id"))
        elif payload.get("field") == "leadgen":
            val = payload.get("value") or {}
            if val.get("leadgen_id"):
                leadgen_ids.append(val.get("leadgen_id"))

        for lgid in leadgen_ids:
            fetch_and_save_meta_lead(str(lgid))

        logger.info("Webhook Meta procesado; leadgen_ids=%s", leadgen_ids)
        return HttpResponse("ok")

    return HttpResponse(status=405)
