import json
import os
from datetime import datetime

from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import MetaLead

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


def _parse_created_time(created_str, entry_time):
    if isinstance(created_str, str):
        try:
            return datetime.strptime(created_str, "%Y-%m-%dT%H:%M:%S%z")
        except ValueError:
            pass

    if entry_time:
        try:
            return datetime.fromtimestamp(int(entry_time) / 1000, tz=timezone.utc)
        except Exception:
            pass

    return timezone.now()


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
            return JsonResponse({"error": "invalid_json"}, status=400)

        entries = payload.get("entry", [])
        processed = []

        for entry in entries:
            entry_time = entry.get("time")
            for change in entry.get("changes", []):
                value = change.get("value") or {}
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

        return JsonResponse({"status": "ok", "processed": processed})

    return HttpResponse(status=405)
