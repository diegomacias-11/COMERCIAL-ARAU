import hashlib
import hmac
import json
import logging
import os
import uuid
from datetime import datetime
from urllib.parse import quote

import requests
from django import forms
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


class WhatsAppLeadCaptureForm(forms.Form):
    full_name = forms.CharField(label="Nombre completo", max_length=200)
    email = forms.EmailField(label="Email", required=False)
    phone_number = forms.CharField(label="Telefono", required=False, max_length=50)
    job_title = forms.CharField(label="Cargo", required=False, max_length=150)
    company_name = forms.CharField(label="Nombre de la empresa", required=False, max_length=200)
    is_organic = forms.BooleanField(label="Organico", required=False)


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


def _find_all_values(payload, keys):
    found = []
    keyset = set(keys or [])
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in keyset and value not in (None, ""):
                found.append(value)
            found.extend(_find_all_values(value, keyset))
    elif isinstance(payload, list):
        for item in payload:
            found.extend(_find_all_values(item, keyset))
    return found


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
    secret_bytes = secret.encode("utf-8")
    hmac_digest = _linkedin_signature(secret, body_bytes)
    return {
        "hmac_sha256": hmac_digest,
        "hmac_sha256_prefixed": f"hmacsha256={hmac_digest}",
        "sha256_secret_plus_body": hashlib.sha256(secret_bytes + body_bytes).hexdigest(),
        "sha256_body_plus_secret": hashlib.sha256(body_bytes + secret_bytes).hexdigest(),
    }


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


def _linkedin_access_token():
    return (
        os.getenv("LINKEDIN_ACCESS_TOKEN")
        or os.getenv("LINKEDIN_TOKEN")
        or os.getenv("LINKEDIN_OAUTH_TOKEN")
        or ""
    ).strip()


def _linkedin_api_version():
    return (os.getenv("LINKEDIN_API_VERSION") or os.getenv("LINKEDIN_VERSION") or "202601").strip()


def _linkedin_is_fetchable_lead_id(lead_id: str) -> bool:
    if not lead_id:
        return False
    return not (lead_id.startswith("notification:") or lead_id.startswith("event:"))


def _linkedin_lead_ref_candidates(lead_ref):
    candidates = []

    def _add(value):
        if value in (None, ""):
            return
        text = str(value).strip()
        if text and text not in candidates:
            candidates.append(text)

    _add(lead_ref)
    extracted = _extract_urn_id(lead_ref)
    _add(extracted)

    if extracted and not str(extracted).startswith("urn:li:"):
        _add(f"urn:li:leadFormResponse:{extracted}")
        _add(f"urn:li:leadGenFormResponse:{extracted}")

    return [c for c in candidates if _linkedin_is_fetchable_lead_id(c)]


def _linkedin_extract_form_id(form_ref):
    if form_ref in (None, ""):
        return None
    text = str(form_ref).strip()
    if not text:
        return None
    if text.isdigit():
        return text

    marker = "urn:li:leadGenForm:"
    if marker in text:
        tail = text.split(marker, 1)[1]
        digits = []
        for ch in tail:
            if ch.isdigit():
                digits.append(ch)
            else:
                break
        if digits:
            return "".join(digits)
    return None


def _linkedin_extract_answer_value(answer):
    def _coerce_scalar(value):
        if value in (None, ""):
            return None
        if isinstance(value, str):
            value = value.strip()
            return value or None
        if isinstance(value, (int, float, bool)):
            return str(value)
        if isinstance(value, list):
            cleaned = []
            for item in value:
                scalar = _coerce_scalar(item)
                if scalar not in (None, ""):
                    cleaned.append(str(scalar))
            return ", ".join(cleaned) if cleaned else None
        if isinstance(value, dict):
            for key in (
                "answer",
                "value",
                "text",
                "label",
                "name",
                "email",
                "phoneNumber",
                "phone",
                "companyName",
                "title",
                "id",
                "urn",
            ):
                scalar = _coerce_scalar(value.get(key))
                if scalar not in (None, ""):
                    return scalar
        return None

    if not isinstance(answer, dict):
        return _coerce_scalar(answer)

    candidates = []
    for key in ("accepted", "rejected", "answer", "response", "value"):
        candidate = answer.get(key)
        if isinstance(candidate, dict):
            candidates.append(candidate)
    candidates.append(answer)

    for candidate in candidates:
        simple = _find_first_value(
            candidate,
            [
                "answer",
                "value",
                "text",
                "email",
                "phoneNumber",
                "phone",
                "companyName",
                "title",
                "stringValue",
                "freeTextAnswer",
                "singleLineAnswer",
                "multiLineAnswer",
                "inputValue",
            ],
        )
        scalar = _coerce_scalar(simple)
        if scalar not in (None, ""):
            return scalar

        options = _find_first_value(
            candidate,
            [
                "selectedOptions",
                "options",
                "optionIds",
                "optionUrns",
                "selectedValues",
                "choices",
            ],
        )
        scalar = _coerce_scalar(options)
        if scalar not in (None, ""):
            return scalar
    return None


def _linkedin_extract_question_name(answer, idx):
    if not isinstance(answer, dict):
        return f"question_{idx + 1}"

    for key in ("name", "question", "questionText", "questionLabel", "label", "fieldName", "field"):
        value = answer.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, dict):
            nested = _find_first_value(value, ["name", "question", "text", "label", "title"])
            if isinstance(nested, str) and nested.strip():
                return nested.strip()

    question_id = answer.get("questionId") or answer.get("id")
    if question_id not in (None, ""):
        return f"question_{question_id}"
    return f"question_{idx + 1}"


def _linkedin_raw_fields_from_response(payload):
    raw_fields = {}

    answers = _find_first_value(payload, ["answers", "responses", "questionsAndAnswers"])
    if isinstance(answers, list):
        for idx, answer in enumerate(answers):
            question_name = _linkedin_extract_question_name(answer, idx)
            value = _linkedin_extract_answer_value(answer)
            if value not in (None, ""):
                raw_fields[str(question_name)] = value

    generic_fields = _find_first_value(payload, ["field_data", "fieldData", "fields", "formFields"])
    if isinstance(generic_fields, list):
        for idx, field in enumerate(generic_fields):
            if not isinstance(field, dict):
                continue
            question_name = (
                field.get("name")
                or field.get("label")
                or field.get("question")
                or field.get("field")
                or field.get("key")
                or f"field_{idx + 1}"
            )
            value = (
                field.get("value")
                if field.get("value") not in (None, "")
                else field.get("values")
                if field.get("values") not in (None, "")
                else field.get("answer")
                if field.get("answer") not in (None, "")
                else field.get("response")
                if field.get("response") not in (None, "")
                else field.get("text")
            )
            parsed_value = _linkedin_extract_answer_value({"value": value})
            if parsed_value not in (None, ""):
                raw_fields[str(question_name)] = parsed_value

    return raw_fields


def _extract_question_id_from_key(raw_key):
    text = str(raw_key or "").strip().lower()
    if not text:
        return None
    if text.startswith("urn:li:"):
        return _extract_urn_id(text)
    if text.startswith("question_"):
        candidate = text[len("question_"):].strip()
        return candidate or None
    if text.startswith("question "):
        candidate = text[len("question "):].strip()
        return candidate or None
    return None


def _stringify_label_candidate(value):
    if isinstance(value, str):
        value = value.strip()
        return value or None
    if isinstance(value, list):
        for item in value:
            label = _stringify_label_candidate(item)
            if label:
                return label
        return None
    if isinstance(value, dict):
        for key in (
            "questionText",
            "questionLabel",
            "question",
            "label",
            "name",
            "text",
            "title",
            "displayName",
            "localizedName",
            "localizedText",
            "value",
        ):
            label = _stringify_label_candidate(value.get(key))
            if label:
                return label
        for localized_key in ("localized", "localizedValue", "localizedText"):
            localized = value.get(localized_key)
            label = _stringify_label_candidate(localized)
            if label:
                return label
        # Fallback para objetos localized como {"en_US": "..."} o estructuras similares.
        for nested in value.values():
            label = _stringify_label_candidate(nested)
            if label:
                return label
    return None


def _linkedin_question_labels_from_payload(payload):
    label_map = {}
    if not isinstance(payload, dict):
        return label_map

    def _store_label(qid, label):
        if qid in (None, "") or label in (None, ""):
            return
        qid_str = str(qid).strip()
        label_str = str(label).strip()
        if not qid_str or not label_str:
            return
        lower = label_str.lower()
        if lower.startswith("urn:li:"):
            return
        if lower in {f"question_{qid_str.lower()}", f"question {qid_str.lower()}"}:
            return
        label_map.setdefault(f"question_{qid_str}", label_str)
        label_map.setdefault(f"question {qid_str}", label_str)
        label_map.setdefault(qid_str, label_str)

    answer_lists = _find_all_values(payload, ["answers", "responses", "questionsAndAnswers"])
    for answers in answer_lists:
        if not isinstance(answers, list):
            continue
        for idx, answer in enumerate(answers):
            if not isinstance(answer, dict):
                continue

            question_id = (
                answer.get("questionId")
                or _extract_urn_id(
                    _find_first_value(
                        answer,
                        [
                            "questionUrn",
                            "question_urn",
                            "question",
                            "questionRef",
                            "questionReference",
                            "id",
                        ],
                    )
                )
            )
            question_id = str(question_id).strip() if question_id not in (None, "") else None

            question_label = _stringify_label_candidate(
                _find_first_value(
                    answer,
                    [
                        "questionText",
                        "questionLabel",
                        "question",
                        "questionInfo",
                        "questionDetails",
                        "questionMetadata",
                        "prompt",
                        "label",
                        "name",
                        "title",
                    ],
                )
            ) or _linkedin_extract_question_name(answer, idx)
            _store_label(question_id, question_label)

    question_lists = _find_all_values(payload, ["questions", "formQuestions", "leadFormQuestions"])
    for form_questions in question_lists:
        if not isinstance(form_questions, list):
            continue
        for question in form_questions:
            if not isinstance(question, dict):
                continue
            question_id = (
                question.get("questionId")
                or question.get("id")
                or _extract_urn_id(
                    _find_first_value(
                        question,
                        ["question", "questionUrn", "question_urn", "urn", "entityUrn", "questionRef"],
                    )
                )
            )
            question_label = _stringify_label_candidate(
                _find_first_value(
                    question,
                    [
                        "questionText",
                        "questionLabel",
                        "label",
                        "name",
                        "text",
                        "title",
                        "localizedName",
                        "localizedText",
                        "prompt",
                    ],
                )
            )
            _store_label(question_id, question_label)

    return label_map


def _linkedin_fetch_form_schema(form_ref):
    form_id = _linkedin_extract_form_id(form_ref)
    if not form_id:
        return {}, {}

    token = _linkedin_access_token()
    if not token:
        return {}, {}

    version = _linkedin_api_version()
    form_id_url = quote(str(form_id), safe="")
    url = f"https://api.linkedin.com/rest/leadForms/{form_id_url}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Linkedin-Version": version,
        "X-Restli-Protocol-Version": "2.0.0",
    }
    payload = None
    for variant in (
        {"params": {"fields": "content,creationLocale,name,id"}, "label": "with_fields"},
        {"params": None, "label": "without_fields"},
    ):
        try:
            response = requests.get(url, headers=headers, params=variant["params"], timeout=15)
            response.raise_for_status()
            payload = response.json()
            break
        except Exception as exc:
            logger.warning(
                "LinkedIn leadForms fallo form_id=%s mode=%s error=%s",
                form_id,
                variant["label"],
                exc,
            )
    if not isinstance(payload, dict):
        return {}, {}

    question_labels = {}
    option_labels_by_question = {}

    question_lists = _find_all_values(payload, ["questions"])
    for question_list in question_lists:
        if not isinstance(question_list, list):
            continue

        for question in question_list:
            if not isinstance(question, dict):
                continue

            qid = question.get("questionId") or question.get("id")
            if qid in (None, ""):
                qid = _extract_urn_id(_find_first_value(question, ["question", "questionUrn", "urn", "entityUrn"]))
            if qid in (None, ""):
                continue
            qid_str = str(qid).strip()
            if not qid_str:
                continue

            qlabel = (
                _stringify_label_candidate(question.get("question"))
                or _stringify_label_candidate(question.get("label"))
                or _stringify_label_candidate(question.get("name"))
            )
            if qlabel:
                question_labels.setdefault(f"question_{qid_str}", qlabel)
                question_labels.setdefault(f"question {qid_str}", qlabel)
                question_labels.setdefault(qid_str, qlabel)

            option_labels = {}
            option_lists = _find_all_values(question, ["options"])
            for opt_list in option_lists:
                if not isinstance(opt_list, list):
                    continue
                for opt in opt_list:
                    if not isinstance(opt, dict):
                        continue
                    opt_id = opt.get("id")
                    if opt_id in (None, ""):
                        continue
                    opt_label = (
                        _stringify_label_candidate(opt.get("text"))
                        or _stringify_label_candidate(opt.get("label"))
                        or _stringify_label_candidate(opt.get("name"))
                    )
                    if opt_label:
                        option_labels[str(opt_id).strip()] = opt_label
            if option_labels:
                option_labels_by_question[qid_str] = option_labels

    return question_labels, option_labels_by_question


def _linkedin_fetch_full_response(lead_ref):
    ref_candidates = _linkedin_lead_ref_candidates(lead_ref)
    if not ref_candidates:
        return None

    token = _linkedin_access_token()
    if not token:
        logger.warning(
            "LinkedIn: sin token de acceso; se omite fetch de leadFormResponses para lead_ref=%s",
            lead_ref,
        )
        return None

    version = _linkedin_api_version()
    fields_projection = (
        "ownerInfo,associatedEntityInfo,leadMetadataInfo,leadType,versionedLeadGenFormUrn,"
        "id,submittedAt,testLead,formResponse,form:(hiddenFields,creationLocale,name,id,content)"
    )
    headers = {
        "Authorization": f"Bearer {token}",
        "Linkedin-Version": version,
        "X-Restli-Protocol-Version": "2.0.0",
    }
    request_variants = [
        {"params": {"fields": fields_projection}, "label": "with_fields"},
        {"params": None, "label": "without_fields"},
    ]

    last_error = None
    for candidate in ref_candidates:
        lead_id_url = quote(str(candidate), safe="")
        url = f"https://api.linkedin.com/rest/leadFormResponses/{lead_id_url}"

        for variant in request_variants:
            try:
                response = requests.get(
                    url,
                    headers=headers,
                    params=variant["params"],
                    timeout=15,
                )
                response.raise_for_status()
                payload = response.json()
                answers = _find_first_value(payload, ["answers", "responses"])
                logger.info(
                    "LinkedIn leadFormResponses OK candidate=%s mode=%s answers=%s",
                    candidate,
                    variant["label"],
                    len(answers) if isinstance(answers, list) else 0,
                )
                return payload
            except requests.HTTPError as exc:
                status = getattr(exc.response, "status_code", None)
                body = getattr(exc.response, "text", "")
                last_error = f"http_{status}"
                if status in (400, 404) and variant["label"] == "with_fields":
                    continue
                logger.warning(
                    "LinkedIn leadFormResponses HTTP %s candidate=%s mode=%s body=%s",
                    status or "unknown",
                    candidate,
                    variant["label"],
                    (body or "")[:400],
                )
            except Exception as exc:
                last_error = str(exc)
                logger.warning(
                    "LinkedIn leadFormResponses fallo candidate=%s mode=%s error=%s",
                    candidate,
                    variant["label"],
                    exc,
                )
    logger.warning(
        "LinkedIn leadFormResponses sin exito para lead_ref=%s candidates=%s last_error=%s",
        lead_ref,
        ref_candidates[:4],
        last_error,
    )
    return None


def _extract_urn_id(value):
    if value in (None, ""):
        return None

    if isinstance(value, dict):
        nested = _find_first_value(
            value,
            [
                "id",
                "$id",
                "urn",
                "entityUrn",
                "resource",
                "leadId",
                "lead_id",
                "leadgen_id",
                "leadGenId",
                "leadGenFormResponse",
                "leadFormResponse",
            ],
        )
        if nested is value:
            return None
        return _extract_urn_id(nested)

    if isinstance(value, list):
        for item in value:
            extracted = _extract_urn_id(item)
            if extracted:
                return extracted
        return None

    text = str(value).strip()
    if not text:
        return None
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


def _lead_sort_datetime(value):
    if not value:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)
    if timezone.is_naive(value):
        return timezone.make_aware(value, timezone.utc)
    return value


def _coerce_lead_text(value):
    if value in (None, ""):
        return ""
    if isinstance(value, list):
        for item in value:
            text = _coerce_lead_text(item)
            if text:
                return text
        return ""
    if isinstance(value, dict):
        for key in ("value", "text", "label", "name", "answer"):
            text = _coerce_lead_text(value.get(key))
            if text:
                return text
        return ""
    return str(value).strip()


def _lead_display_name(lead):
    full_name = _coerce_lead_text(getattr(lead, "full_name", ""))
    if full_name:
        return full_name

    raw_fields = getattr(lead, "raw_fields", None) or {}
    if isinstance(raw_fields, dict):
        normalized = {_normalize_key(k): v for k, v in raw_fields.items()}
        direct_name = _pick_first(normalized, ["full_name", "nombre_completo", "name", "nombre"])
        if _coerce_lead_text(direct_name):
            return _coerce_lead_text(direct_name)

        first_name = _pick_first(normalized, ["first_name", "nombre"])
        last_name = _pick_first(normalized, ["last_name", "apellido", "apellidos"])
        composed = " ".join(part for part in [_coerce_lead_text(first_name), _coerce_lead_text(last_name)] if part).strip()
        if composed:
            return composed

        # LinkedIn: algunos formularios guardan question_<id>; intentamos detectar el campo de nombre por etiqueta.
        payload_labels = _linkedin_question_labels_from_payload(getattr(lead, "raw_payload", {}) or {})
        if payload_labels:
            name_value = ""
            for key, value in raw_fields.items():
                question_id = _extract_question_id_from_key(key)
                label = (
                    payload_labels.get(str(key))
                    or payload_labels.get((str(key) or "").replace(" ", "_"))
                    or payload_labels.get((str(key) or "").replace("_", " "))
                    or (payload_labels.get(question_id) if question_id else None)
                    or ""
                )
                normalized_label = _normalize_key(label)
                if any(token in normalized_label for token in ("full_name", "nombre_completo", "first_name", "last_name", "nombre", "apellido", "name")):
                    candidate = _coerce_lead_text(value)
                    if candidate:
                        name_value = candidate
                        break
            if name_value:
                return name_value

    email = _coerce_lead_text(getattr(lead, "email", ""))
    if email:
        return email

    company_name = _coerce_lead_text(getattr(lead, "company_name", ""))
    if company_name:
        return company_name

    phone = _coerce_lead_text(getattr(lead, "phone_number", ""))
    if phone:
        return phone

    lead_identifier = _coerce_lead_text(getattr(lead, "leadgen_id", "") or getattr(lead, "lead_id", ""))
    return lead_identifier or "Sin nombre"


def _prepare_lead_for_list(lead, *, detail_url_name, source_label, identifier_value):
    lead.detail_url_name = detail_url_name
    lead.source_label = source_label
    lead.identifier_value = identifier_value or ""
    lead.display_name = _lead_display_name(lead)
    return lead


def _generate_manual_leadgen_id():
    for _ in range(5):
        candidate = f"manual-whatsapp-{uuid.uuid4().hex[:20]}"
        if not MetaLead.objects.filter(leadgen_id=candidate).exists():
            return candidate
    return f"manual-whatsapp-{uuid.uuid4().hex}"


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


def _linkedin_defaults_from_full_response(full_payload, fallback_defaults):
    defaults = dict(fallback_defaults or {})
    lead_metadata = full_payload.get("leadMetadata") if isinstance(full_payload, dict) else {}
    if not isinstance(lead_metadata, dict):
        lead_metadata = {}
    lead_metadata_info = full_payload.get("leadMetadataInfo") if isinstance(full_payload, dict) else {}
    if not isinstance(lead_metadata_info, dict):
        lead_metadata_info = {}
    sponsored_metadata = lead_metadata.get("sponsoredLeadMetadata") if isinstance(lead_metadata, dict) else {}
    if not isinstance(sponsored_metadata, dict):
        sponsored_metadata = {}
    sponsored_metadata_info = (
        lead_metadata_info.get("sponsoredLeadMetadataInfo") if isinstance(lead_metadata_info, dict) else {}
    )
    if not isinstance(sponsored_metadata_info, dict):
        sponsored_metadata_info = {}
    associated_entity = full_payload.get("associatedEntity") if isinstance(full_payload, dict) else {}
    if not isinstance(associated_entity, dict):
        associated_entity = {}
    associated_entity_info = full_payload.get("associatedEntityInfo") if isinstance(full_payload, dict) else {}
    if not isinstance(associated_entity_info, dict):
        associated_entity_info = {}
    associated_creative_info = (
        associated_entity_info.get("associatedCreativeInfo") if isinstance(associated_entity_info, dict) else {}
    )
    if not isinstance(associated_creative_info, dict):
        associated_creative_info = {}

    submitted_at = _find_first_value(full_payload, ["submittedAt", "createdTime", "eventTime", "timestamp"])
    created_time = _parse_epoch(submitted_at)
    if created_time:
        defaults["created_time"] = created_time

    campaign_urn = sponsored_metadata.get("campaign")
    campaign_name = _find_first_value(sponsored_metadata_info.get("campaign"), ["name"])
    if campaign_urn:
        defaults["campaign_id"] = _extract_urn_id(campaign_urn) or defaults.get("campaign_id", "")
    if campaign_name:
        defaults["campaign_name"] = campaign_name

    form_urn = _find_first_value(full_payload, ["versionedLeadGenFormUrn", "leadGenFormUrn", "formUrn"])
    if form_urn:
        defaults["form_id"] = str(form_urn)

    creative_urn = (
        associated_entity.get("associatedCreative")
        or associated_entity.get("sponsoredCreative")
        or associated_entity.get("creative")
    )
    creative_name = associated_creative_info.get("name")
    if creative_urn:
        defaults["ad_id"] = _extract_urn_id(creative_urn) or defaults.get("ad_id", "")
    if creative_name:
        defaults["ad_name"] = creative_name

    raw_fields = _linkedin_raw_fields_from_response(full_payload)
    normalized = {_normalize_key(k): v for k, v in raw_fields.items()}

    first_name = _pick_first(normalized, ["first_name", "nombre"])
    last_name = _pick_first(normalized, ["last_name", "apellido", "apellidos"])
    full_name = (
        _pick_first(normalized, ["full_name", "nombre_completo", "name"])
        or " ".join(part for part in [first_name, last_name] if part).strip()
        or defaults.get("full_name")
    )
    email = _pick_first(normalized, ["email", "correo", "correo_electronico", "work_email"]) or defaults.get("email")
    phone = _pick_first(normalized, ["phone_number", "telefono", "tel", "celular", "mobile", "phone"]) or defaults.get("phone_number")
    job_title = _pick_first(normalized, ["job_title", "puesto", "cargo", "title"]) or defaults.get("job_title")
    company = _pick_first(normalized, ["company_name", "company", "empresa", "nombre_empresa", "nombre_de_empresa"]) or defaults.get("company_name")

    defaults.update(
        {
            "full_name": full_name,
            "email": email,
            "phone_number": phone,
            "job_title": job_title,
            "company_name": company,
            "raw_fields": raw_fields or defaults.get("raw_fields") or {},
            "raw_payload": full_payload or defaults.get("raw_payload") or {},
        }
    )
    return defaults


@login_required
def leads_lista(request):
    q = request.GET.get("q", "").strip()
    meta_leads = MetaLead.objects.all()
    linkedin_leads = LinkedInLead.objects.all()

    if q:
        meta_leads = meta_leads.filter(
            Q(leadgen_id__icontains=q)
            | Q(form_id__icontains=q)
            | Q(campaign_name__icontains=q)
            | Q(full_name__icontains=q)
            | Q(raw_fields__icontains=q)
            | Q(email__icontains=q)
            | Q(phone_number__icontains=q)
            | Q(company_name__icontains=q)
        )
        linkedin_leads = linkedin_leads.filter(
            Q(lead_id__icontains=q)
            | Q(form_id__icontains=q)
            | Q(campaign_name__icontains=q)
            | Q(full_name__icontains=q)
            | Q(raw_fields__icontains=q)
            | Q(email__icontains=q)
            | Q(phone_number__icontains=q)
            | Q(company_name__icontains=q)
        )

    leads = []
    for lead in meta_leads:
        leads.append(
            _prepare_lead_for_list(
                lead,
                detail_url_name="leads_metalead_detail",
                source_label="Meta",
                identifier_value=lead.leadgen_id,
            )
        )
    for lead in linkedin_leads:
        leads.append(
            _prepare_lead_for_list(
                lead,
                detail_url_name="leads_metalead_detail_linkedin",
                source_label="LinkedIn",
                identifier_value=lead.lead_id,
            )
        )

    leads.sort(
        key=lambda item: _lead_sort_datetime(getattr(item, "created_time", None)),
        reverse=True,
    )

    return render(request, "leads/lista.html", {"leads": leads, "q": q})


@login_required
def leads_whatsapp_form(request):
    back_url = request.GET.get("next") or request.POST.get("next") or "/leads/"

    if request.method == "POST":
        form = WhatsAppLeadCaptureForm(request.POST)
        if form.is_valid():
            full_name = (form.cleaned_data.get("full_name") or "").strip()
            email = (form.cleaned_data.get("email") or "").strip()
            phone_number = (form.cleaned_data.get("phone_number") or "").strip()
            job_title = (form.cleaned_data.get("job_title") or "").strip()
            company_name = (form.cleaned_data.get("company_name") or "").strip()
            is_organic = bool(form.cleaned_data.get("is_organic"))

            raw_fields = {
                "full_name": full_name,
                "email": email,
                "phone_number": phone_number,
                "job_title": job_title,
                "company_name": company_name,
                "is_organic": is_organic,
            }

            lead = MetaLead.objects.create(
                leadgen_id=_generate_manual_leadgen_id(),
                created_time=timezone.now(),
                ad_id="",
                ad_name="",
                adset_id="",
                adset_name="",
                campaign_id="",
                campaign_name="",
                form_id="manual_whatsapp",
                is_organic=is_organic,
                platform="WhatsApp",
                full_name=full_name or None,
                email=email or None,
                phone_number=phone_number or None,
                job_title=job_title or None,
                company_name=company_name or None,
                raw_fields={k: v for k, v in raw_fields.items() if v not in (None, "")},
                raw_payload={
                    "source": "manual_whatsapp",
                    "captured_from": "leads_ui",
                    "fields": {k: v for k, v in raw_fields.items() if v not in (None, "")},
                },
            )
            return redirect(f"/leads/{lead.id}/?next={back_url}")
    else:
        form = WhatsAppLeadCaptureForm()

    return render(
        request,
        "leads/whatsapp_form.html",
        {
            "form": form,
            "back_url": back_url,
        },
    )


def _lead_delete(request, pk: int, lead_model):
    if request.method != "POST":
        return HttpResponse(status=405)
    lead = get_object_or_404(lead_model, pk=pk)
    lead.delete()
    back_url = request.POST.get("next") or "/leads/"
    return redirect(back_url)


@login_required
def lead_delete(request, pk: int):
    return _lead_delete(request, pk, MetaLead)


@login_required
def linkedin_lead_delete(request, pk: int):
    return _lead_delete(request, pk, LinkedInLead)


def _build_field_rows(lead):
    field_rows = []
    raw_items = lead.raw_fields or {}
    payload_question_labels = {}
    form_question_labels = {}
    form_option_labels = {}
    is_linkedin = (lead.platform or "").strip().lower() == "linkedin"

    if is_linkedin and isinstance(raw_items, dict):
        payload_question_labels = _linkedin_question_labels_from_payload(lead.raw_payload or {})
        # Si el lead no tiene respuestas o no tenemos etiquetas, intenta rehidratar desde API.
        should_refresh = (not raw_items) or (not payload_question_labels)
        if should_refresh:
            payload_lead_ref = _find_first_value(
                lead.raw_payload or {},
                [
                    "leadId",
                    "lead_id",
                    "leadgen_id",
                    "leadgenId",
                    "leadGenId",
                    "leadGenFormResponse",
                    "leadFormResponse",
                    "id",
                ],
            )
            refreshed_payload = _linkedin_fetch_full_response(payload_lead_ref or getattr(lead, "lead_id", "") or "")
            if isinstance(refreshed_payload, dict):
                refreshed_raw_fields = _linkedin_raw_fields_from_response(refreshed_payload)
                refreshed_question_labels = _linkedin_question_labels_from_payload(refreshed_payload)

                update_fields = []
                if refreshed_raw_fields:
                    raw_items = refreshed_raw_fields
                    lead.raw_fields = refreshed_raw_fields
                    update_fields.append("raw_fields")
                if refreshed_payload:
                    lead.raw_payload = refreshed_payload
                    update_fields.append("raw_payload")
                if refreshed_question_labels:
                    payload_question_labels = refreshed_question_labels

                if update_fields:
                    try:
                        lead.save(update_fields=update_fields)
                    except Exception:
                        logger.warning(
                            "No se pudo actualizar datos LinkedIn para lead_id=%s",
                            getattr(lead, "lead_id", ""),
                        )
        form_question_labels, form_option_labels = _linkedin_fetch_form_schema(lead.form_id)

    resolved_question_labels = {}
    if payload_question_labels:
        resolved_question_labels.update(payload_question_labels)
    if form_question_labels:
        # El schema del form tiene prioridad porque es el texto exacto configurado.
        resolved_question_labels.update(form_question_labels)

    def _translate_choice_value(question_id, raw_value):
        if not question_id:
            return raw_value
        choices = form_option_labels.get(str(question_id))
        if not isinstance(choices, dict) or not choices:
            return raw_value

        values = []
        if isinstance(raw_value, list):
            values = [str(v).strip() for v in raw_value if v not in (None, "")]
        elif raw_value not in (None, ""):
            text = str(raw_value).strip()
            if "," in text:
                values = [part.strip() for part in text.split(",") if part.strip()]
            else:
                values = [text]
        if not values:
            return raw_value

        translated = [choices.get(v, v) for v in values]
        return ", ".join(translated)

    for name, raw_value in raw_items.items():
        label = " ".join((name or "").replace("_", " ").split())
        question_id = _extract_question_id_from_key(name)
        if resolved_question_labels:
            label = (
                resolved_question_labels.get(str(name))
                or resolved_question_labels.get((str(name) or "").replace(" ", "_"))
                or resolved_question_labels.get((str(name) or "").replace("_", " "))
                or (resolved_question_labels.get(question_id) if question_id else None)
                or label
            )
        if question_id and label.lower().strip() in {f"question_{question_id}", f"question {question_id}"}:
            label = f"Pregunta {question_id}"
        value = _translate_choice_value(question_id, raw_value)
        value = value or ""
        if isinstance(value, list):
            value = ", ".join(str(v) for v in value if v is not None)
        value_str = str(value)
        if "@" in value_str:
            value = value_str
        else:
            value = " ".join(value_str.replace("_", " ").split())
        field_rows.append({"label": label or "Campo", "value": value})

    if field_rows:
        return field_rows

    if is_linkedin:
        payload_fields = _linkedin_raw_fields_from_response(lead.raw_payload or {})
        if payload_fields:
            lead.raw_fields = payload_fields
            try:
                lead.save(update_fields=["raw_fields"])
            except Exception:
                logger.warning(
                    "No se pudo reconstruir raw_fields desde raw_payload para lead_id=%s",
                    getattr(lead, "lead_id", ""),
                )
            for name, raw_value in payload_fields.items():
                label = " ".join((name or "").replace("_", " ").split())
                question_id = _extract_question_id_from_key(name)
                if resolved_question_labels:
                    label = (
                        resolved_question_labels.get(str(name))
                        or resolved_question_labels.get((str(name) or "").replace(" ", "_"))
                        or resolved_question_labels.get((str(name) or "").replace("_", " "))
                        or (resolved_question_labels.get(question_id) if question_id else None)
                        or label
                    )
                if question_id and label.lower().strip() in {f"question_{question_id}", f"question {question_id}"}:
                    label = f"Pregunta {question_id}"
                value = _translate_choice_value(question_id, raw_value)
                value = value or ""
                if isinstance(value, list):
                    value = ", ".join(str(v) for v in value if v is not None)
                value_str = str(value)
                value = value_str if "@" in value_str else " ".join(value_str.replace("_", " ").split())
                field_rows.append({"label": label or "Campo", "value": value})
            if field_rows:
                return field_rows

    fallback_fields = [
        ("Nombre", lead.full_name),
        ("Email", lead.email),
        ("Telefono", lead.phone_number),
        ("Cargo", lead.job_title),
        ("Empresa", lead.company_name),
    ]
    for label, value in fallback_fields:
        if value not in (None, ""):
            field_rows.append({"label": label, "value": str(value)})
    return field_rows


def _lead_detail(request, pk: int, *, lead_model, delete_url_name, lead_identifier_attr, source_label):
    lead = get_object_or_404(lead_model, pk=pk)
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
    field_rows = _build_field_rows(lead)
    platform_value = (lead.platform or source_label).strip()
    lead_identifier = getattr(lead, lead_identifier_attr, "") or ""
    return render(
        request,
        "leads/detalle.html",
        {
            "lead": lead,
            "back_url": back_url,
            "field_rows": field_rows,
            "can_edit": can_edit,
            "delete_url_name": delete_url_name,
            "show_is_organic": lead_model is MetaLead,
            "lead_identifier": lead_identifier,
            "platform_label": platform_value,
            "cita_agendada_value": (
                timezone.localtime(lead.cita_agendada).strftime("%Y-%m-%dT%H:%M")
                if lead.cita_agendada
                else ""
            ),
            "lead_estatus_choices": LEAD_ESTATUS_CHOICES,
            "servicio_choices": SERVICIO_CHOICES,
        },
    )


@login_required
def lead_detail(request, pk: int):
    return _lead_detail(
        request,
        pk,
        lead_model=MetaLead,
        delete_url_name="leads_metalead_delete",
        lead_identifier_attr="leadgen_id",
        source_label="Meta",
    )


@login_required
def linkedin_lead_detail(request, pk: int):
    return _lead_detail(
        request,
        pk,
        lead_model=LinkedInLead,
        delete_url_name="leads_metalead_delete_linkedin",
        lead_identifier_attr="lead_id",
        source_label="LinkedIn",
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
    skip_signature_check = (
        (os.getenv("LINKEDIN_SKIP_SIGNATURE_CHECK") or "").strip().lower()
        in {"1", "true", "yes", "on"}
    )
    expected_for_log = {}
    matched_strategy = None
    is_valid_signature = False
    for secret in secrets:
        expected_signatures = _linkedin_signature_variants(secret, body_bytes)
        if not expected_for_log:
            expected_for_log = expected_signatures
        for strategy, expected_sig in expected_signatures.items():
            if hmac.compare_digest(provided_signature, expected_sig):
                is_valid_signature = True
                matched_strategy = strategy
                break
        if is_valid_signature:
            break
    if not is_valid_signature:
        logger.warning(
            (
                "LinkedIn webhook POST con firma invalida. "
                "provided=%s hmac=%s s+b=%s b+s=%s body_len=%s secret_len=%s"
            ),
            provided_signature[:80],
            (expected_for_log.get("hmac_sha256", ""))[:80],
            (expected_for_log.get("sha256_secret_plus_body", ""))[:80],
            (expected_for_log.get("sha256_body_plus_secret", ""))[:80],
            len(body_bytes),
            len(secrets[0]) if secrets else 0,
        )
        if not skip_signature_check:
            return HttpResponse("Invalid signature", status=403)
        logger.warning("LinkedIn webhook: firma invalida pero omitida por LINKEDIN_SKIP_SIGNATURE_CHECK=true")
    elif matched_strategy:
        logger.warning("LinkedIn webhook firma valida con estrategia=%s", matched_strategy)

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
        lead_ref = _find_first_value(
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
        lead_id = _extract_urn_id(lead_ref)
        notification_id = _find_first_value(event, ["notificationId", "notification_id"])
        if not lead_id and notification_id not in (None, ""):
            lead_id = f"notification:{notification_id}"
        if not lead_id:
            canonical_event = event if isinstance(event, dict) else {"event": event}
            event_json = json.dumps(canonical_event, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            lead_id = f"event:{hashlib.sha256(event_json.encode('utf-8')).hexdigest()[:40]}"
        existing_lead = LinkedInLead.objects.filter(lead_id=str(lead_id)).first()

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
        if not raw_fields and isinstance(event, dict):
            raw_fields = _linkedin_raw_fields_from_response(event)

        if not raw_fields and existing_lead and isinstance(existing_lead.raw_fields, dict):
            raw_fields = existing_lead.raw_fields

        defaults = {
            "created_time": created_time or (existing_lead.created_time if existing_lead else None) or timezone.now(),
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
            "raw_payload": (
                (event if isinstance(event, dict) else payload)
                if raw_fields
                else (existing_lead.raw_payload if existing_lead and isinstance(existing_lead.raw_payload, dict) else (event if isinstance(event, dict) else payload))
            ),
        }
        if existing_lead:
            defaults["campaign_id"] = defaults["campaign_id"] or (existing_lead.campaign_id or "")
            defaults["campaign_name"] = defaults["campaign_name"] or (existing_lead.campaign_name or "")
            defaults["form_id"] = defaults["form_id"] or (existing_lead.form_id or "")
            defaults["ad_id"] = defaults["ad_id"] or (existing_lead.ad_id or "")
            defaults["ad_name"] = defaults["ad_name"] or (existing_lead.ad_name or "")
            defaults["adset_id"] = defaults["adset_id"] or (existing_lead.adset_id or "")
            defaults["adset_name"] = defaults["adset_name"] or (existing_lead.adset_name or "")
            defaults["full_name"] = defaults["full_name"] or existing_lead.full_name
            defaults["email"] = defaults["email"] or existing_lead.email
            defaults["phone_number"] = defaults["phone_number"] or existing_lead.phone_number
            defaults["job_title"] = defaults["job_title"] or existing_lead.job_title
            defaults["company_name"] = defaults["company_name"] or existing_lead.company_name

        if raw_fields:
            normalized_event = {_normalize_key(k): v for k, v in raw_fields.items()}
            first_name = _pick_first(normalized_event, ["first_name", "nombre"])
            last_name = _pick_first(normalized_event, ["last_name", "apellido", "apellidos"])
            defaults["full_name"] = (
                defaults.get("full_name")
                or _pick_first(normalized_event, ["full_name", "nombre_completo", "name"])
                or " ".join(part for part in [first_name, last_name] if part).strip()
            )
            defaults["email"] = defaults.get("email") or _pick_first(
                normalized_event, ["email", "correo", "correo_electronico", "work_email"]
            )
            defaults["phone_number"] = defaults.get("phone_number") or _pick_first(
                normalized_event, ["phone_number", "telefono", "tel", "celular", "mobile", "phone"]
            )
            defaults["job_title"] = defaults.get("job_title") or _pick_first(
                normalized_event, ["job_title", "puesto", "cargo", "title"]
            )
            defaults["company_name"] = defaults.get("company_name") or _pick_first(
                normalized_event,
                ["company_name", "company", "empresa", "nombre_empresa", "nombre_de_empresa", "razon_social"],
            )

        full_payload = _linkedin_fetch_full_response(lead_ref or lead_id)
        if full_payload:
            defaults = _linkedin_defaults_from_full_response(full_payload, defaults)

        LinkedInLead.objects.update_or_create(lead_id=str(lead_id), defaults=defaults)

    logger.warning("LinkedIn webhook procesado OK. events=%s", len(events))
    return HttpResponse("OK")
