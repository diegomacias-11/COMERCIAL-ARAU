from __future__ import annotations
from typing import List, Optional
import os
import json
from django.conf import settings


# ============================================================
# CONFIGURACIÓN FLEXIBLE: PRODUCCIÓN (Render) o LOCAL
# ============================================================

# Variables de entorno (Render u otro servidor)
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SHEET_NAME = os.getenv("SHEET_NAME")

# Si no existen, usar valores locales de prueba
if not SPREADSHEET_ID or not SHEET_NAME:
    SPREADSHEET_ID = getattr(settings, "LOCAL_SPREADSHEET_ID", None) or "TU_ID_DE_HOJA_LOCAL"
    SHEET_NAME = getattr(settings, "LOCAL_SHEET_NAME", None) or "Historial Comercial (TEST)"

print(f"📄 Conectando con hoja '{SHEET_NAME}' (ID: {SPREADSHEET_ID})")


# ============================================================
# FUNCIÓN BASE DE CONEXIÓN
# ============================================================

def _get_service():
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
    except Exception as exc:
        raise RuntimeError("Google API client not installed. Install google-api-python-client.") from exc

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]

    # Credenciales desde variable de entorno o archivo local
    raw = (
        os.getenv("GOOGLE_CREDENTIALS")
        or os.getenv("GOOGLE_CREDENTIALS_JSON")
        or os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        or ""
    ).strip()

    if raw:
        creds_info = json.loads(raw)
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    else:
        creds = Credentials.from_service_account_file(
            settings.GOOGLE_SHEETS.get("CREDENTIALS_FILE"), scopes=scopes
        )

    service = build("sheets", "v4", credentials=creds, cache_discovery=False)
    return service


# ============================================================
# UTILIDADES
# ============================================================

def _sheet_range_all_columns(sheet_name: str) -> str:
    return f"'{sheet_name}'!A:Z"


def _row_range(sheet_name: str, row: int, last_col: str = "Z") -> str:
    return f"'{sheet_name}'!A{row}:{last_col}{row}"


HEADERS = [
    "id", "Prospecto", "Giro", "Tipo", "Medio",
    "Servicio", "Servicio 2", "Servicio 3", "Contacto",
    "Teléfono", "Conexión", "Vendedor", "Estatus cita",
    "Fecha cita", "Número cita", "Estatus seguimiento",
    "Monto factura", "Comentarios", "Lugar", "Fecha registro",
]


# ============================================================
# FUNCIONES DE ESCRITURA / ACTUALIZACIÓN / BORRADO
# ============================================================

def _ensure_headers(service, spreadsheet_id: str, sheet_name: str) -> None:
    resp = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=f"'{sheet_name}'!A1:S1")
        .execute()
    )
    values = resp.get("values", [])
    if not values:
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"'{sheet_name}'!A1:S1",
            valueInputOption="RAW",
            body={"values": [HEADERS]},
        ).execute()


def cita_to_row(cita) -> List:
    return [
        str(cita.id or ""),
        cita.prospecto or "",
        cita.giro or "",
        cita.tipo or "",
        cita.medio or "",
        cita.servicio or "",
        getattr(cita, "servicio2", "") or "",
        getattr(cita, "servicio3", "") or "",
        cita.contacto or "",
        cita.telefono or "",
        cita.conexion or "",
        cita.vendedor or "",
        cita.estatus_cita or "",
        cita.fecha_cita.strftime("%Y-%m-%dT%H:%M") if cita.fecha_cita else "",
        cita.numero_cita or "",
        cita.estatus_seguimiento or "",
        getattr(cita, "monto_factura", "") or "",
        cita.comentarios or "",
        cita.lugar or "",
        cita.fecha_registro.strftime("%Y-%m-%dT%H:%M") if cita.fecha_registro else "",
    ]


def append_cita_to_sheet(cita) -> Optional[int]:
    service = _get_service()
    _ensure_headers(service, SPREADSHEET_ID, SHEET_NAME)
    values = [cita_to_row(cita)]
    body = {"values": values}
    result = (
        service.spreadsheets()
        .values()
        .append(
            spreadsheetId=SPREADSHEET_ID,
            range=_sheet_range_all_columns(SHEET_NAME),
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body=body,
        )
        .execute()
    )
    updated_range = result.get("updates", {}).get("updatedRange", "")
    try:
        row_part = updated_range.split("!")[-1].split(":")[0]
        row_num = int("".join(ch for ch in row_part if ch.isdigit()))
        return row_num
    except Exception:
        return None


def _find_row_by_id(service, spreadsheet_id: str, sheet_name: str, cita_id: int) -> Optional[int]:
    resp = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=f"'{sheet_name}'!A:A")
        .execute()
    )
    values = resp.get("values", [])
    for idx, row in enumerate(values, start=1):
        if not row:
            continue
        if str(row[0]).strip() == str(cita_id):
            return idx
    return None


def update_cita_in_sheet(cita) -> None:
    service = _get_service()
    _ensure_headers(service, SPREADSHEET_ID, SHEET_NAME)
    row_index = _find_row_by_id(service, SPREADSHEET_ID, SHEET_NAME, cita.id)
    if not row_index:
        append_cita_to_sheet(cita)
        return
    row_values = [cita_to_row(cita)]
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=_row_range(SHEET_NAME, row_index, last_col="S"),
        valueInputOption="RAW",
        body={"values": row_values},
    ).execute()


def _get_sheet_id_by_title(service, spreadsheet_id: str, sheet_title: str) -> Optional[int]:
    meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    for sh in meta.get("sheets", []):
        props = sh.get("properties", {})
        if props.get("title") == sheet_title:
            return props.get("sheetId")
    return None


def delete_cita_from_sheet(cita_id: int) -> None:
    service = _get_service()
    row_index = _find_row_by_id(service, SPREADSHEET_ID, SHEET_NAME, cita_id)
    if not row_index:
        return
    sheet_id = _get_sheet_id_by_title(service, SPREADSHEET_ID, SHEET_NAME)
    if sheet_id is None:
        return
    body = {
        "requests": [
            {
                "deleteDimension": {
                    "range": {
                        "sheetId": sheet_id,
                        "dimension": "ROWS",
                        "startIndex": row_index - 1,
                        "endIndex": row_index,
                    }
                }
            }
        ]
    }
    service.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()
