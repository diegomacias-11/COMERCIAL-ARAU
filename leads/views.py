import hashlib
import hmac
import json
import logging
import os
from datetime import datetime

import requests
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt

from .models import LinkedInLead, MetaLead
from comercial.models import Cita
from core.choices import LEAD_ESTATUS_CHOICES, SERVICIO_CHOICES

logger = logging.getLogger(__name__)
META_VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN")
META_PAGE_TOKEN = os.getenv("META_PAGE_TOKEN")


def _normalize_key(name: str) -> str:
    return (name or "").strip().lower().replace(" ", "_")


def _find_first_value(payload, keys):
    if isinstance(payload, dict):
        for key in keys:
            if key in payload and payload[key] not in (None, ""):
                return payload[key]
        for value in payload.values():
            found = _find_first_value(value, keys)
            if found not in (None, ""):
                return found
    elif isinstance(payload, list):
        for item in payload:
            found = _find_first_value(item, keys)
            if found not in (None, ""):
                return found
    return None


def _parse_epoch(value):
    try:
        ts = float(value)
    except (TypeError, ValueError):
        return None
    if ts > 1e12:
        ts = ts / 1000.0
    try:
        return datetime.utcfromtimestamp(ts).replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _linkedin_signature(secret, body_bytes):
    return hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()


def _linkedin_signature_variants(secret, body_bytes):
    digest = _linkedin_signature(secret, body_bytes)
    return {digest, f"hmacsha256={digest}"}


def _linkedin_secret_candidates():
    raw = os.getenv("LINKEDIN_CLIENT_SECRET")
    if not raw:
        return []
    candidates = []
    for value in (
        raw,
        raw.strip(),
        raw.strip().strip('"').strip("'"),
    ):
        if value and value not in candidates:
            candidates.append(value)
    return candidates


def _extract_urn_id(value):
    if value in (None, ""):
        return None
    text = str(value).strip()
    if text.startswith("urn:li:"):
        return text.rsplit(":", 1)[-1].strip(")")
    return text


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


def _normalize_phone(value):
    if not value:
        return None
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    if len(digits) >= 10:
        return digits[-10:]
    return digits or None


def _pick_vendedor(user):
    first_name = (getattr(user, "first_name", "") or "").strip()
    if not first_name:
        return "Giovanni"
    if first_name.lower().startswith("daniel"):
        return "Daniel S."
    return "Giovanni"


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
            "campaign_id,campaign_name,form_id,"
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

    raw_fields, normalized_fields = _split_field_data(data.get("field_data", []) or [])

    created_dt = parse_datetime(data.get("created_time") or "")
    if created_dt and timezone.is_naive(created_dt):
        created_dt = timezone.make_aware(created_dt, timezone.utc)

    form_id = data.get("form_id") or ""

    defaults = {
        "created_time": created_dt or timezone.now(),
        "ad_id": data.get("ad_id") or "",
        "ad_name": data.get("ad_name") or "",
        "adset_id": data.get("adset_id") or "",
        "adset_name": data.get("adset_name") or "",
        "campaign_id": data.get("campaign_id") or "",
        "campaign_name": data.get("campaign_name") or "",
        "form_id": form_id,
        "is_organic": data.get("is_organic") or False,
        "platform": data.get("platform") or "",
        "full_name": raw_fields.get("full_name") or _pick_first(normalized_fields, ["full_name", "nombre_completo", "nombre", "name"]),
        "email": raw_fields.get("email") or _pick_first(normalized_fields, ["email", "correo", "correo_electronico", "email_address"]),
        "phone_number": raw_fields.get("phone_number") or _pick_first(normalized_fields, ["phone_number", "telefono", "tel", "celular", "mobile", "phone"]),
        "job_title": raw_fields.get("job_title") or _pick_first(normalized_fields, ["job_title", "puesto", "cargo", "title"]),
        "company_name": raw_fields.get("company_name") or _pick_first(normalized_fields, ["company_name", "company", "empresa", "nombre_empresa", "nombre_de_empresa", "razon_social", "business_name"]),
        "raw_fields": raw_fields,
        "raw_payload": data,
    }

    lead, _ = MetaLead.objects.update_or_create(
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
            Q(leadgen_id__icontains=q)
            | Q(form_id__icontains=q)
            | Q(campaign_name__icontains=q)
        )

    return render(request, "leads/lista.html", {"leads": leads, "q": q})


@login_required
def lead_delete(request, pk: int):
    if request.method != "POST":
        return HttpResponse(status=405)
    lead = get_object_or_404(MetaLead, pk=pk)
    lead.delete()
    back_url = request.POST.get("next") or "/leads/"
    return redirect(back_url)


@login_required
def lead_detail(request, pk: int):
    lead = get_object_or_404(MetaLead, pk=pk)
    back_url = request.GET.get("next") or "/leads/"
    can_edit = request.user.is_superuser or request.user.groups.filter(
        name__in=["Dirección Comercial", "Apoyo Comercial"]
    ).exists()

    if request.method == "POST":
        if not can_edit:
            return HttpResponse(status=403)

        lead.contactado = request.POST.get("contactado") == "on"
        lead.estatus = request.POST.get("estatus") or None
        lead.servicio = request.POST.get("servicio") or None
        lead.notas = request.POST.get("notas") or None

        cita_value = request.POST.get("cita_agendada") or ""
        cita_dt = parse_datetime(cita_value) if cita_value else None
        if cita_dt and timezone.is_naive(cita_dt):
            cita_dt = timezone.make_aware(cita_dt, timezone.get_current_timezone())

        lead.cita_agendada = cita_dt
        lead.save(update_fields=["contactado", "estatus", "servicio", "notas", "cita_agendada"])

        if cita_dt:
            if lead.cita_id:
                cita = lead.cita
                cita.fecha_cita = cita_dt
            else:
                cita = Cita(fecha_cita=cita_dt)

            raw_fields = lead.raw_fields or {}
            normalized_fields = {_normalize_key(k): v for k, v in raw_fields.items()}
            company_name = lead.company_name or _pick_first(
                normalized_fields,
                [
                    "company_name",
                    "company",
                    "empresa",
                    "nombre_empresa",
                    "nombre_de_empresa",
                    "razon_social",
                    "business_name",
                ],
            )
            cita.prospecto = company_name or ""
            cita.medio = "Lead"
            cita.servicio = lead.servicio or "Pendiente"
            cita.contacto = lead.full_name or ""
            cita.puesto = lead.job_title or ""
            cita.telefono = _normalize_phone(lead.phone_number)
            cita.correo = lead.email or ""
            cita.estatus_cita = "Agendada"
            cita.numero_cita = "Primera"
            cita.vendedor = _pick_vendedor(request.user)

            cita.save()
            if not lead.cita_id:
                lead.cita = cita
                lead.save(update_fields=["cita"])
    field_rows = []
    raw_items = lead.raw_fields or {}

    for name, raw_value in raw_items.items():
        label = " ".join((name or "").replace("_", " ").split())
        value = raw_value or ""
        if isinstance(value, list):
            value = ", ".join(str(v) for v in value if v is not None)
        value_str = str(value)
        if "@" in value_str:
            value = value_str
        else:
            value = " ".join(value_str.replace("_", " ").split())
        field_rows.append({"label": label or "Campo", "value": value})
    return render(
        request,
        "leads/detalle.html",
        {
            "lead": lead,
            "back_url": back_url,
            "field_rows": field_rows,
            "can_edit": can_edit,
            "cita_agendada_value": (
                timezone.localtime(lead.cita_agendada).strftime("%Y-%m-%dT%H:%M")
                if lead.cita_agendada
                else ""
            ),
            "lead_estatus_choices": LEAD_ESTATUS_CHOICES,
            "servicio_choices": SERVICIO_CHOICES,
        },
    )


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


@csrf_exempt
def linkedin_lead_webhook(request):
    logger.warning(
        "LinkedIn webhook hit: method=%s path=%s ua=%s ip=%s",
        request.method,
        request.path,
        request.META.get("HTTP_USER_AGENT", ""),
        request.META.get("REMOTE_ADDR", ""),
    )
    secrets = _linkedin_secret_candidates()
    primary_secret = secrets[0] if secrets else ""

    if request.method == "GET":
        challenge_code = request.GET.get("challengeCode") or request.GET.get("challenge_code")
        logger.warning(
            "LinkedIn webhook GET challengeCode_present=%s len=%s",
            bool(challenge_code),
            len(challenge_code or ""),
        )
        if not challenge_code:
            logger.warning("LinkedIn webhook GET sin challengeCode")
            return HttpResponse("Missing challengeCode", status=400)
        if not primary_secret:
            logger.error("LinkedIn webhook GET sin LINKEDIN_CLIENT_SECRET")
            return HttpResponse("Missing LINKEDIN_CLIENT_SECRET", status=500)
        challenge_response = _linkedin_signature(primary_secret, challenge_code.encode("utf-8"))
        return JsonResponse(
            {
                "challengeCode": challenge_code,
                "challengeResponse": challenge_response,
            }
        )

    if request.method != "POST":
        return HttpResponse(status=405)

    body_bytes = request.body or b""
    signature = request.headers.get("X-LI-Signature") or request.META.get("HTTP_X_LI_SIGNATURE")
    if not secrets:
        logger.error("LinkedIn webhook POST sin LINKEDIN_CLIENT_SECRET")
        return HttpResponse("Missing LINKEDIN_CLIENT_SECRET", status=500)
    if not signature:
        logger.warning("LinkedIn webhook POST sin X-LI-Signature")
        return HttpResponse("Missing X-LI-Signature", status=400)

    provided_signature = signature.strip().strip('"').lower()
    expected_for_log = None
    is_valid_signature = False
    for secret in secrets:
        expected_signatures = _linkedin_signature_variants(secret, body_bytes)
        if expected_for_log is None:
            expected_for_log = _linkedin_signature(secret, body_bytes)
        if any(hmac.compare_digest(provided_signature, expected_sig) for expected_sig in expected_signatures):
            is_valid_signature = True
            break
    if not is_valid_signature:
        logger.warning(
            (
                "LinkedIn webhook POST con firma invalida. "
                "provided=%s expected=%s body_len=%s secret_len=%s"
            ),
            provided_signature[:80],
            (expected_for_log or "")[:80],
            len(body_bytes),
            len(secrets[0]) if secrets else 0,
        )
        return HttpResponse("Invalid signature", status=403)

    try:
        payload = json.loads(body_bytes.decode("utf-8") or "{}")
    except Exception:
        logger.warning("LinkedIn webhook POST JSON invalido")
        return HttpResponse("Invalid JSON", status=400)

    logger.info("LinkedIn webhook POST recibido: %s", body_bytes[:500])

    events = payload.get("events")
    if not isinstance(events, list):
        if isinstance(payload.get("notifications"), list):
            events = payload.get("notifications")
        elif isinstance(payload.get("elements"), list):
            events = payload.get("elements")
        else:
            events = [payload]

    for event in events:
        lead_id = _find_first_value(
            event,
            [
                "leadId",
                "lead_id",
                "leadgen_id",
                "leadgenId",
                "leadGenId",
                "leadGenFormResponse",
                "leadFormResponse",
            ],
        )
        lead_id = _extract_urn_id(lead_id)
        notification_id = _find_first_value(event, ["notificationId", "notification_id"])
        if not lead_id and notification_id not in (None, ""):
            lead_id = f"notification:{notification_id}"

        created_time = _parse_epoch(
            _find_first_value(
                event,
                ["eventTime", "createdTime", "created_time", "timestamp", "occurredAt", "lastModifiedAt"],
            )
        )

        full_name = _find_first_value(event, ["fullName", "full_name", "name"])
        email = _find_first_value(event, ["email", "emailAddress", "work_email"])
        phone = _find_first_value(event, ["phoneNumber", "phone_number", "phone"])
        job_title = _find_first_value(event, ["jobTitle", "job_title", "title"])
        company = _find_first_value(event, ["companyName", "company_name", "company"])

        campaign_id = _find_first_value(event, ["campaignId", "campaign_id"])
        campaign_name = _find_first_value(event, ["campaignName", "campaign_name"])
        form_id = _find_first_value(
            event,
            ["formId", "form_id", "leadGenFormId", "leadGenForm", "versionedForm"],
        )
        ad_id = _find_first_value(event, ["adId", "ad_id"])
        ad_name = _find_first_value(event, ["adName", "ad_name"])
        adset_id = _find_first_value(event, ["adsetId", "adset_id"])
        adset_name = _find_first_value(event, ["adsetName", "adset_name"])

        raw_fields = event.get("raw_fields") if isinstance(event, dict) else None
        if not isinstance(raw_fields, dict):
            raw_fields = {}

        defaults = {
            "created_time": created_time or timezone.now(),
            "campaign_id": campaign_id or "",
            "campaign_name": campaign_name or "",
            "form_id": form_id or "",
            "ad_id": ad_id or "",
            "ad_name": ad_name or "",
            "adset_id": adset_id or "",
            "adset_name": adset_name or "",
            "full_name": full_name,
            "email": email,
            "phone_number": phone,
            "job_title": job_title,
            "company_name": company,
            "raw_fields": raw_fields,
            "raw_payload": event if isinstance(event, dict) else payload,
        }

        if lead_id:
            LinkedInLead.objects.update_or_create(lead_id=str(lead_id), defaults=defaults)
        else:
            LinkedInLead.objects.create(**defaults)

    logger.warning("LinkedIn webhook procesado OK. events=%s", len(events))
    return HttpResponse("OK")
