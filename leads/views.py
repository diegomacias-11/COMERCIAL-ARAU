import json
import logging
import os
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import MetaLead

logger = logging.getLogger(__name__)
MARKETING_GROUP_NAME = "Marketing"
META_VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN")


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

        return HttpResponse("Invalid verify token", status=403)

    if request.method == "POST":
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            logger.warning("Webhook Meta: JSON invalido: %s", request.body[:500])
            return JsonResponse({"error": "invalid_json"}, status=400)

        processed = []

        values = []
        if "entry" in payload:
            for entry in payload.get("entry", []):
                entry_time = entry.get("time")
                for change in entry.get("changes", []):
                    values.append((change.get("value") or {}, entry_time))
        elif payload.get("field") == "leadgen" and "value" in payload:
            values.append((payload.get("value") or {}, payload.get("time")))

        for value, entry_time in values:
            leadgen_id = value.get("leadgen_id")
            if not leadgen_id:
                continue

            raw_fields, normalized_fields = _split_field_data(value.get("field_data"))

            defaults = {
                "created_time": _parse_created_time(value.get("created_time"), entry_time),
                "ad_id": str(value.get("ad_id") or ""),
                "ad_name": value.get("ad_name") or "",
                "adset_id": str(value.get("adset_id") or value.get("adgroup_id") or ""),
                "adset_name": value.get("adset_name") or value.get("adgroup_name") or "",
                "campaign_id": str(value.get("campaign_id") or ""),
                "campaign_name": value.get("campaign_name") or "",
                "form_id": str(value.get("form_id") or ""),
                "form_name": value.get("form_name") or "",
                "is_organic": bool(value.get("is_organic")),
                "platform": value.get("platform") or value.get("channel") or "",
                "full_name": _pick_first(
                    normalized_fields,
                    ["full_name", "nombre_completo", "nombre", "name"],
                ),
                "email": _pick_first(normalized_fields, ["email", "correo", "correo_electronico"]),
                "phone_number": _pick_first(
                    normalized_fields,
                    ["phone_number", "telefono", "celular", "mobile_phone", "phone"],
                ),
                "raw_fields": raw_fields,
                "raw_payload": value,
            }

            lead, created = MetaLead.objects.update_or_create(
                leadgen_id=str(leadgen_id),
                defaults=defaults,
            )

            processed.append({"leadgen_id": lead.leadgen_id, "created": created})

        logger.info("Webhook Meta procesado: %s", processed)
        return JsonResponse({"status": "ok", "processed": processed})

    return HttpResponse(status=405)
