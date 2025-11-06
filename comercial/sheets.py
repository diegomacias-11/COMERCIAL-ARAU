from __future__ import annotations

from typing import List, Optional
from django.conf import settings
import os
import json


def _get_service():
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("Google API client not installed. Install google-api-python-client.") from exc

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]

    # Preferir credenciales desde variable de entorno con contenido JSON completo
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
        # Fallback: archivo en disco (entorno local)
        creds = Credentials.from_service_account_file(
            settings.GOOGLE_SHEETS["CREDENTIALS_FILE"], scopes=scopes
        )
    service = build("sheets", "v4", credentials=creds, cache_discovery=False)
    return service


def _sheet_range_all_columns(sheet_name: str) -> str:
    return f"'{sheet_name}'!A:Z"


def _row_range(sheet_name: str, row: int, last_col: str = "Z") -> str:
    return f"'{sheet_name}'!A{row}:{last_col}{row}"


# Encabezados esperados en la hoja (A..S)
HEADERS = [
    "id",
    "Prospecto",
    "Giro",
    "Tipo",
    "Medio",
    "Servicio",
    "Servicio 2",
    "Servicio 3",
    "Contacto",
    "Teléfono",
    "Conexión",
    "Vendedor",
    "Estatus cita",
    "Fecha cita",
    "Número cita",
    "Estatus seguimiento",
    "Comentarios",
    "Lugar",
    "Fecha registro",
]


def _ensure_headers(service, spreadsheet_id: str, sheet_name: str) -> None:
    # Solo escribe encabezados si la hoja está vacía (sin fila 1)
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
        cita.comentarios or "",
        cita.lugar or "",
        cita.fecha_registro.strftime("%Y-%m-%dT%H:%M") if cita.fecha_registro else "",
    ]


def append_cita_to_sheet(cita) -> Optional[int]:
    cfg = settings.GOOGLE_SHEETS
    service = _get_service()
    _ensure_headers(service, cfg["SPREADSHEET_ID"], cfg["SHEET_NAME"])  # crea encabezados si faltan
    values = [cita_to_row(cita)]
    body = {"values": values}
    result = (
        service.spreadsheets()
        .values()
        .append(
            spreadsheetId=cfg["SPREADSHEET_ID"],
            range=_sheet_range_all_columns(cfg["SHEET_NAME"]),
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body=body,
        )
        .execute()
    )
    # Parse updatedRange like "Historial Comercial!A123:S123"
    updated_range = result.get("updates", {}).get("updatedRange", "")
    try:
        row_part = updated_range.split("!")[-1].split(":")[0]  # A123
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
    # values is a list of rows; each row is a list of cells
    for idx, row in enumerate(values, start=1):
        if not row:
            continue
        if str(row[0]).strip() == str(cita_id):
            return idx
    return None


def update_cita_in_sheet(cita) -> None:
    cfg = settings.GOOGLE_SHEETS
    service = _get_service()
    _ensure_headers(service, cfg["SPREADSHEET_ID"], cfg["SHEET_NAME"])  # por seguridad
    row_index = _find_row_by_id(service, cfg["SPREADSHEET_ID"], cfg["SHEET_NAME"], cita.id)
    if not row_index:
        # If not found, append as new entry
        append_cita_to_sheet(cita)
        return
    row_values = [cita_to_row(cita)]
    service.spreadsheets().values().update(
        spreadsheetId=cfg["SPREADSHEET_ID"],
        range=_row_range(cfg["SHEET_NAME"], row_index, last_col="S"),
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
    cfg = settings.GOOGLE_SHEETS
    service = _get_service()
    # Buscar fila por ID en columna A
    row_index = _find_row_by_id(service, cfg["SPREADSHEET_ID"], cfg["SHEET_NAME"], cita_id)
    if not row_index:
        return  # nada que borrar
    # Necesitamos sheetId (gid) para batchUpdate deleteDimension
    sheet_id = _get_sheet_id_by_title(service, cfg["SPREADSHEET_ID"], cfg["SHEET_NAME"])
    if sheet_id is None:
        return
    # DeleteDimensionRequest usa índices base 0 y endIndex exclusivo
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
    service.spreadsheets().batchUpdate(spreadsheetId=cfg["SPREADSHEET_ID"], body=body).execute()
