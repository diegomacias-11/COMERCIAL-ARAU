from django.db import migrations, models


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


def _parse_is_organic(raw_payload):
    explicit = _find_first_value(raw_payload, ["is_organic", "isOrganic", "organic"])
    if isinstance(explicit, bool):
        return explicit
    if isinstance(explicit, (int, float)):
        return bool(explicit)
    if isinstance(explicit, str):
        normalized = explicit.strip().lower()
        if normalized in {"1", "true", "yes", "si", "organic", "organico"}:
            return True
        if normalized in {"0", "false", "no", "sponsored", "patrocinado"}:
            return False

    lead_type = _find_first_value(raw_payload, ["lead_type", "leadType", "type"])
    if isinstance(lead_type, dict):
        lead_type = _find_first_value(lead_type, ["value", "type", "name", "code"])
    text = str(lead_type or "").strip().upper()
    if "ORGANIC" in text:
        return True
    if "SPONSORED" in text:
        return False
    return None


def _backfill_is_organic(apps, schema_editor):
    LinkedInLead = apps.get_model("leads", "LinkedInLead")
    for lead in LinkedInLead.objects.all().only("id", "raw_payload", "is_organic"):
        raw_payload = lead.raw_payload if isinstance(lead.raw_payload, dict) else {}
        parsed = _parse_is_organic(raw_payload)
        if parsed is None:
            continue
        if bool(lead.is_organic) != bool(parsed):
            lead.is_organic = bool(parsed)
            lead.save(update_fields=["is_organic"])


class Migration(migrations.Migration):

    dependencies = [
        ("leads", "0006_linkedinlead"),
    ]

    operations = [
        migrations.AddField(
            model_name="linkedinlead",
            name="is_organic",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(_backfill_is_organic, migrations.RunPython.noop),
    ]
