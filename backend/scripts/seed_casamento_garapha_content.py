"""Build Casamento GaRapha content rows for Google Sheets.

This module is intentionally side-effect free for Tasks 1 and 2. It only
defines constants and returns row data shaped for the existing sheet importers.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


load_dotenv(Path(__file__).parent.parent / ".env")

TRIP_UUID = "CASAMENTO-GARAPHA-2026"
TRIP_TITLE = "Casamento GaRapha"
MARINE_PHONE = "+558899769044"
TRIP_CONTENT_SHEET_ID = os.environ.get(
    "TRIP_CONTENT_SHEET_ID",
    "1N1B66s1-K4DDf2_863frmhnpF6LRZB_ww60uax0gKZM",
)
STAFF_CONTENT_SHEET_ID = os.environ.get(
    "STAFF_CONTENT_SHEET_ID",
    "1iVv9k45F3dacjYEwR4TsIuGuFtFmVgN3y0ueghvNWiI",
)

MANAGED_HEADERS: dict[str, list[str]] = {
    "Viagens": ["trip_uuid", "nome_da_viagem", "data_inicio", "data_fim", "service_agreement_url"],
    "Emergency Contacts": ["trip_uuid", "name", "role", "phone", "sort_order"],
    "Recomendacoes": [
        "trip_uuid",
        "name",
        "description",
        "address",
        "photo_url",
        "sort_order",
        "category",
        "neighborhood",
        "location",
        "highlight",
        "price_range",
        "rating",
        "map_url",
        "emoji",
        "phone",
        "whatsapp_url",
        "contact_label",
    ],
    "Fases": ["trip_uuid", "ordem", "fase", "titulo", "subtitulo", "icone", "descricao_curta", "descricao_completa", "ideal_pace"],
    "Checklist": ["trip_uuid", "fase", "ordem", "label", "obrigatorio"],
    "Links": ["trip_uuid", "fase", "ordem", "label", "url"],
    "Roteiro": [
        "trip_uuid",
        "dia",
        "data",
        "dia_titulo",
        "dia_subtitulo",
        "dia_icon",
        "dia_descricao_curta",
        "dia_descricao_completa",
        "atividade_nome",
        "atividade_tipo",
        "atividade_horario",
        "atividade_duracao_min",
        "atividade_descricao_curta",
        "atividade_info_pratica",
        "atividade_preco_brl",
        "atividade_endereco",
        "atividade_max_scans",
    ],
    "FAQ": ["trip_uuid", "question", "answer", "sort_order"],
    "Contatos": ["trip_uuid", "category", "name", "role", "phone", "sort_order"],
}

CONTENT_ROWS: dict[str, list[list[Any]]] = {
    "Viagens": [[TRIP_UUID, TRIP_TITLE, "2026-09-04", "2026-09-06", ""]],
    "Emergency Contacts": [
        [TRIP_UUID, "Marine Carneiro", "Apoio da cerimonia", MARINE_PHONE, 1],
    ],
    "Recomendacoes": [
        [
            TRIP_UUID,
            "Yoga, Hawaiian Canoe and Kayak Classes / Espaco Imparti",
            "Yoga, Hawaiian canoe, and kayak classes and experiences in Prea.",
            "Prea, Cruz - CE",
            "",
            1,
            "Sports",
            "Prea",
            "Prea, CE",
            "Wellness and ocean activities for free days.",
            "$$",
            "",
            "",
            "yoga",
            "+5588981659580",
            "https://wa.me/5588981659580",
            "Espaco Imparti",
        ],
        [
            TRIP_UUID,
            "Kitesurf Lessons - Professor Bete",
            "Kitesurf lessons with a local instructor to enjoy Prea's winds.",
            "Prea, Cruz - CE",
            "",
            2,
            "Sports",
            "Prea",
            "Prea, CE",
            "A good option for guests who want to practice kitesurfing during the trip.",
            "$$$",
            "",
            "",
            "kite",
            "+5588996439775",
            "https://wa.me/5588996439775",
            "Professor Bete",
        ],
        [
            TRIP_UUID,
            "Lucas - Guide and ATV Rental",
            "Local guide and ATV rental for tours around the region.",
            "Prea, Cruz - CE",
            "",
            3,
            "Sightseeing",
            "Prea",
            "Prea, CE",
            "An option for exploring lagoons, dunes, and nearby areas with local support.",
            "$$$",
            "",
            "",
            "quad",
            "+5588981866421",
            "https://wa.me/5588981866421",
            "Lucas",
        ],
        [
            TRIP_UUID,
            "Ianaele - Hair and Makeup",
            "Local hair and makeup service for the wedding events.",
            "Prea, Cruz - CE",
            "",
            4,
            "Beauty",
            "Prea",
            "Prea, CE",
            "Book in advance for the wedding day.",
            "$$",
            "",
            "",
            "makeup",
            "+5588997177444",
            "https://wa.me/5588997177444",
            "Ianaele",
        ],
        [
            TRIP_UUID,
            "Jimmy - Jeri Airport, Prea Transfer and Taxi",
            "Transfers between Jericoacoara Airport, Prea, and local taxi rides.",
            "Prea, Cruz - CE",
            "",
            5,
            "Transportation",
            "Prea",
            "Prea, CE",
            "Coordinate schedules, flights, and meeting points in advance.",
            "$$",
            "",
            "",
            "transfer",
            "+5588997755605",
            "https://wa.me/5588997755605",
            "Jimmy",
        ],
        [
            TRIP_UUID,
            "Balcon",
            "Recommended restaurant in Prea for meals during free days.",
            "Prea, Cruz - CE",
            "",
            6,
            "Restaurants",
            "Prea",
            "Prea, CE",
            "Local option for lunch or dinner.",
            "$$",
            "",
            "",
            "restaurant",
            "",
            "",
            "",
        ],
        [
            TRIP_UUID,
            "Rancho do Peixe",
            "Restaurant and beach structure at Rancho do Peixe in Prea.",
            "Prea, Cruz - CE",
            "",
            7,
            "Restaurants",
            "Prea",
            "Prea, CE",
            "Well-known option for meals and beach meetups.",
            "$$$",
            "",
            "",
            "restaurant",
            "",
            "",
            "",
        ],
        [
            TRIP_UUID,
            "Alisios",
            "Local restaurant recommended for meals in Prea.",
            "Prea, Cruz - CE",
            "",
            8,
            "Restaurants",
            "Prea",
            "Prea, CE",
            "Good option for dinner on free evenings.",
            "$$",
            "",
            "",
            "restaurant",
            "",
            "",
            "",
        ],
        [
            TRIP_UUID,
            "Restaurante da Lu",
            "Local restaurant recommended for regional food.",
            "Prea, Cruz - CE",
            "",
            9,
            "Restaurants",
            "Prea",
            "Prea, CE",
            "Simple local option for lunch or dinner.",
            "$$",
            "",
            "",
            "restaurant",
            "",
            "",
            "",
        ],
        [
            TRIP_UUID,
            "Casinha",
            "Recommended restaurant in Prea for meals during the stay.",
            "Prea, Cruz - CE",
            "",
            10,
            "Restaurants",
            "Prea",
            "Prea, CE",
            "Convenient option for free time between events.",
            "$$",
            "",
            "",
            "restaurant",
            "",
            "",
            "",
        ],
        [
            TRIP_UUID,
            "Restaurante Caboclo",
            "Local restaurant recommended in the Prea area.",
            "Prea, Cruz - CE",
            "",
            11,
            "Restaurants",
            "Prea",
            "Prea, CE",
            "Local option for meals with guests.",
            "$$",
            "",
            "",
            "restaurant",
            "",
            "",
            "",
        ],
        [
            TRIP_UUID,
            "Restaurante Arriegua",
            "Recommended restaurant for meals during the trip.",
            "Prea, Cruz - CE",
            "",
            12,
            "Restaurants",
            "Prea",
            "Prea, CE",
            "Option for lunch or dinner on free days.",
            "$$",
            "",
            "",
            "restaurant",
            "",
            "",
            "",
        ],
    ],
    "Fases": [
        [
            TRIP_UUID,
            1,
            "logistica_de_viagem",
            "Logistica de Viagem",
            "Chegada, hospedagem e deslocamentos",
            "plane",
            "Organize voos, hospedagem, transfer e documentos antes de embarcar.",
            "Confirme chegada e retorno, dados da hospedagem, deslocamento ate Prea e documentos pessoais necessarios para viajar com tranquilidade.",
            "",
        ],
        [
            TRIP_UUID,
            2,
            "preparando_as_malas",
            "Preparando as Malas",
            "Roupas e itens para os eventos",
            "luggage",
            "Separe roupas para praia, jantar de boas vindas e casamento.",
            "Inclua trajes dos eventos, roupas leves, calcados confortaveis, sandalias, oculos de sol e itens pessoais para praia e celebracao.",
            "",
        ],
        [
            TRIP_UUID,
            3,
            "cuidados_e_bem_estar",
            "Cuidados e Bem-estar",
            "Saude, clima e conforto",
            "heart",
            "Prepare itens de saude, protecao solar e cuidados para clima de praia.",
            "Leve protetor solar, repelente, medicacao pessoal, kit de higiene, garrafa de agua e tudo que ajude a manter bem-estar durante os eventos.",
            "",
        ],
        [
            TRIP_UUID,
            4,
            "informacoes_do_casamento",
            "Informacoes do Casamento",
            "Cerimonia, festa e links uteis",
            "rings",
            "Revise orientacoes do casamento, venue, horarios e presentes.",
            "Consulte o site do casamento, confirme orientacoes de chegada, transporte, venue principal e lista de presentes antes da viagem.",
            "",
        ],
    ],
    "Checklist": [
        [TRIP_UUID, "logistica_de_viagem", 1, "Confirmar voos de chegada e retorno", "true"],
        [TRIP_UUID, "logistica_de_viagem", 2, "Confirmar hospedagem em Prea ou Jericoacoara", "true"],
        [TRIP_UUID, "logistica_de_viagem", 3, "Organizar transfer ate Prea", "true"],
        [TRIP_UUID, "logistica_de_viagem", 4, "Separar documentos pessoais", "true"],
        [TRIP_UUID, "preparando_as_malas", 1, "Separar roupa para o jantar de boas vindas", "true"],
        [TRIP_UUID, "preparando_as_malas", 2, "Separar roupa de praia e sandalias", "true"],
        [TRIP_UUID, "preparando_as_malas", 3, "Separar roupa para o casamento", "true"],
        [TRIP_UUID, "preparando_as_malas", 4, "Levar oculos de sol", "false"],
        [TRIP_UUID, "cuidados_e_bem_estar", 1, "Levar protetor solar, repelente e medicacao pessoal", "true"],
        [TRIP_UUID, "cuidados_e_bem_estar", 2, "Montar kit de higiene pessoal", "true"],
        [TRIP_UUID, "cuidados_e_bem_estar", 3, "Planejar hidratacao para dias de sol e praia", "false"],
        [TRIP_UUID, "informacoes_do_casamento", 1, "Revisar site do casamento e lista de presentes", "true"],
        [TRIP_UUID, "informacoes_do_casamento", 2, "Confirmar horario de chegada para a cerimonia", "true"],
        [TRIP_UUID, "informacoes_do_casamento", 3, "Verificar orientacoes de transporte dos eventos", "true"],
    ],
    "Links": [
        [TRIP_UUID, "informacoes_do_casamento", 1, "Site do casamento", "https://sites.icasei.com.br/gabrielaeraphael/home"],
        [TRIP_UUID, "informacoes_do_casamento", 2, "Local dos eventos", "https://sites.icasei.com.br/gabrielaeraphael/places/18"],
        [TRIP_UUID, "informacoes_do_casamento", 3, "Lista de presentes", "https://sites.icasei.com.br/gabrielaeraphael/pages/37083965"],
        [TRIP_UUID, "logistica_de_viagem", 1, "Mapa de Prea", "https://maps.google.com/?q=Prea,Cruz,CE"],
    ],
    "Roteiro": [
        [
            TRIP_UUID,
            1,
            "2026-09-04",
            "Dia 1 - Boas Vindas",
            "Chegada e encontro inicial",
            "utensils",
            "Jantar de boas vindas para reunir os convidados.",
            "Primeiro encontro oficial do fim de semana do casamento.",
            "Jantar de Boas Vindas",
            "included",
            "19:00",
            240,
            "Encontro de boas vindas para convidados.",
            "Confira o local e o horario final no site do casamento ou com a organizacao.",
            "",
            "Rancho do Kite, Prea - CE",
            "",
        ],
        [
            TRIP_UUID,
            2,
            "2026-09-05",
            "Dia 2 - Pre Wedding",
            "Passeio de jangada e festa",
            "waves",
            "Dia de praia, passeio e celebracao pre wedding.",
            "Programacao de sabado com passeio de jangada e festa pre wedding.",
            "Passeio de Jangada",
            "optional",
            "09:30",
            150,
            "Passeio de jangada para convidados.",
            "Use roupa de praia, protetor solar e confirme condicoes do mar com a organizacao.",
            "",
            "Prea - CE",
            "",
        ],
        [
            TRIP_UUID,
            2,
            "2026-09-05",
            "Dia 2 - Pre Wedding",
            "Passeio de jangada e festa",
            "waves",
            "Dia de praia, passeio e celebracao pre wedding.",
            "Programacao de sabado com passeio de jangada e festa pre wedding.",
            "Festa Pre Wedding",
            "included",
            "13:00",
            360,
            "Festa pre wedding para abrir a celebracao.",
            "Confira traje, local e transporte nas informacoes oficiais do casamento.",
            "",
            "Prea - CE",
            "",
        ],
        [
            TRIP_UUID,
            3,
            "2026-09-06",
            "Dia 3 - Casamento",
            "Cerimonia e festa",
            "heart",
            "Dia da cerimonia e festa do casamento.",
            "Celebracao principal do casamento de Gabriela e Raphael.",
            "Casamento",
            "included",
            "15:00",
            540,
            "Cerimonia e festa do casamento.",
            "Chegue com antecedencia e siga as orientacoes de transporte e traje.",
            "",
            "Prea - CE",
            "",
        ],
    ],
    "FAQ": [
        [
            TRIP_UUID,
            "Qual e o traje do casamento?",
            "Siga o dress code informado no site do casamento e priorize conforto para clima de praia.",
            1,
        ],
        [
            TRIP_UUID,
            "Havera transporte para os eventos?",
            "Consulte as orientacoes oficiais do casamento e combine deslocamentos com antecedencia.",
            2,
        ],
        [
            TRIP_UUID,
            "Que horas devo chegar para a cerimonia?",
            "Planeje chegar com antecedencia ao horario informado para evitar atrasos na celebracao.",
            3,
        ],
    ],
}

STAFF_ROWS: dict[str, list[list[Any]]] = {
    "Contatos": [
        [TRIP_UUID, "Cerimonia", "Marine Carneiro", "Apoio da cerimonia", MARINE_PHONE, 1],
    ],
}

GOOGLE_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
OAUTH_TOKEN_FILE = Path(__file__).parent.parent / "secrets" / "gcp-oauth2-token.json"
OAUTH_CLIENT_FILE = Path(__file__).parent.parent / "secrets" / "gcp-oauth2-credentials.json"


def copy_rows(rows: list[list[Any]]) -> list[list[Any]]:
    return [list(row) for row in rows]


def build_sheet_rows() -> dict[str, dict[str, list[list[Any]]]]:
    return {
        "content": {
            "Viagens": copy_rows(CONTENT_ROWS["Viagens"]),
            "Emergency Contacts": copy_rows(CONTENT_ROWS["Emergency Contacts"]),
            "Recomendacoes": copy_rows(CONTENT_ROWS["Recomendacoes"]),
            "Fases": copy_rows(CONTENT_ROWS["Fases"]),
            "Checklist": copy_rows(CONTENT_ROWS["Checklist"]),
            "Links": copy_rows(CONTENT_ROWS["Links"]),
            "Roteiro": copy_rows(CONTENT_ROWS["Roteiro"]),
            "FAQ": copy_rows(CONTENT_ROWS["FAQ"]),
        },
        "staff": {
            "Contatos": copy_rows(STAFF_ROWS["Contatos"]),
        },
    }


def normalize_sheet_values(rows: list[list[Any]]) -> list[list[Any]]:
    normalized = []
    for row in rows:
        normalized_row = []
        for value in row:
            if value is None:
                normalized_row.append("")
            elif isinstance(value, Decimal):
                normalized_row.append(str(value))
            elif isinstance(value, (datetime, date)):
                normalized_row.append(value.isoformat())
            else:
                normalized_row.append(value)
        normalized.append(normalized_row)
    return normalized


def row_matches_trip_uuid(row: list[Any], header: list[str], trip_uuid: str = TRIP_UUID) -> bool:
    normalized_header = [str(value).strip().lower() for value in header]
    try:
        trip_uuid_index = normalized_header.index("trip_uuid")
    except ValueError:
        return False
    if trip_uuid_index >= len(row):
        return False
    return str(row[trip_uuid_index]).strip() == trip_uuid


def merge_trip_rows(
    existing_rows: list[list[Any]],
    header: list[str],
    new_rows: list[list[Any]],
    trip_uuid: str = TRIP_UUID,
) -> list[list[Any]]:
    body = existing_rows[1:] if existing_rows else []
    kept = [row for row in body if not row_matches_trip_uuid(row, header, trip_uuid)]
    return normalize_sheet_values([header] + kept + new_rows)


def validate_managed_header(tab: str, values: list[list[Any]]) -> list[str]:
    managed_header = MANAGED_HEADERS.get(tab)
    if not managed_header:
        return values[0] if values else []
    if values and values[0] != managed_header:
        raise ValueError(f"Header mismatch for managed tab {tab}: expected {managed_header}, found {values[0]}")
    return managed_header


def pad_rows_for_write(rows: list[list[Any]], row_count: int, column_count: int = 26) -> list[list[Any]]:
    padded_rows = [list(row[:column_count]) + [""] * max(0, column_count - len(row)) for row in rows]
    while len(padded_rows) < row_count:
        padded_rows.append([""] * column_count)
    return padded_rows


def column_letter(column_index: int) -> str:
    letters = ""
    while column_index:
        column_index, remainder = divmod(column_index - 1, 26)
        letters = chr(ord("A") + remainder) + letters
    return letters


def sheet_row_range(tab: str, start_row: int, row_count: int, column_count: int) -> str:
    end_row = start_row + row_count - 1
    return f"'{tab}'!A{start_row}:{column_letter(column_count)}{end_row}"


def get_tab_properties(sheets, spreadsheet_id: str) -> dict[str, dict[str, Any]]:
    meta = (
        sheets.spreadsheets()
        .get(spreadsheetId=spreadsheet_id, fields="sheets.properties(sheetId,title)")
        .execute()
    )
    return {sheet["properties"]["title"]: sheet["properties"] for sheet in meta.get("sheets", [])}


def ensure_tab(sheets, spreadsheet_id: str, tab: str) -> int:
    properties_by_title = get_tab_properties(sheets, spreadsheet_id)
    if tab in properties_by_title:
        return int(properties_by_title[tab]["sheetId"])
    sheets.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": [{"addSheet": {"properties": {"title": tab}}}]},
    ).execute()
    properties_by_title = get_tab_properties(sheets, spreadsheet_id)
    return int(properties_by_title[tab]["sheetId"])


def find_trip_row_block(values: list[list[Any]], header: list[str], trip_uuid: str = TRIP_UUID) -> tuple[int, int]:
    matching_indexes = [
        row_index
        for row_index, row in enumerate(values[1:], start=1)
        if row_matches_trip_uuid(row, header, trip_uuid)
    ]
    if not matching_indexes:
        return len(values), 0

    block_start = matching_indexes[0]
    block_end = matching_indexes[-1]
    expected_indexes = list(range(block_start, block_end + 1))
    if matching_indexes != expected_indexes:
        raise ValueError(f"Found non-contiguous rows for trip {trip_uuid} in managed sheet")
    return block_start, len(matching_indexes)


def insert_sheet_rows(sheets, spreadsheet_id: str, sheet_id: int, start_index: int, row_count: int) -> None:
    if row_count <= 0:
        return
    sheets.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "requests": [
                {
                    "insertDimension": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "ROWS",
                            "startIndex": start_index,
                            "endIndex": start_index + row_count,
                        },
                        "inheritFromBefore": start_index > 0,
                    }
                }
            ]
        },
    ).execute()


def delete_sheet_rows(sheets, spreadsheet_id: str, sheet_id: int, start_index: int, row_count: int) -> None:
    if row_count <= 0:
        return
    sheets.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "requests": [
                {
                    "deleteDimension": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "ROWS",
                            "startIndex": start_index,
                            "endIndex": start_index + row_count,
                        }
                    }
                }
            ]
        },
    ).execute()


def update_sheet_values(
    sheets,
    spreadsheet_id: str,
    tab: str,
    start_row: int,
    rows: list[list[Any]],
    column_count: int,
) -> None:
    if not rows:
        return
    sheets.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=sheet_row_range(tab, start_row, len(rows), column_count),
        valueInputOption="RAW",
        body={"values": normalize_sheet_values(rows)},
    ).execute()


def replace_trip_rows(sheets, spreadsheet_id: str, tab: str, new_rows: list[list[Any]]) -> None:
    sheet_id = ensure_tab(sheets, spreadsheet_id, tab)
    values = (
        sheets.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=f"'{tab}'!A:Z")
        .execute()
        .get("values", [])
    )
    header = validate_managed_header(tab, values)
    column_count = len(header)
    if not values:
        update_sheet_values(sheets, spreadsheet_id, tab, 1, [header] + new_rows, column_count)
        return

    block_start_index, existing_trip_row_count = find_trip_row_block(values, header)
    new_trip_row_count = len(new_rows)
    delta = new_trip_row_count - existing_trip_row_count
    if delta > 0 and existing_trip_row_count > 0:
        insert_sheet_rows(sheets, spreadsheet_id, sheet_id, block_start_index + existing_trip_row_count, delta)

    update_sheet_values(sheets, spreadsheet_id, tab, block_start_index + 1, new_rows, column_count)

    if delta < 0:
        delete_sheet_rows(
            sheets,
            spreadsheet_id,
            sheet_id,
            block_start_index + new_trip_row_count,
            abs(delta),
        )


def update_sheets(sheets, rows: dict[str, dict[str, list[list[Any]]]]) -> dict[str, Any]:
    for tab, tab_rows in rows["content"].items():
        replace_trip_rows(sheets, TRIP_CONTENT_SHEET_ID, tab, tab_rows)
    for tab, tab_rows in rows["staff"].items():
        replace_trip_rows(sheets, STAFF_CONTENT_SHEET_ID, tab, tab_rows)
    return {
        "content_sheet_id": TRIP_CONTENT_SHEET_ID,
        "staff_sheet_id": STAFF_CONTENT_SHEET_ID,
        "updated_tabs": {"content": sorted(rows["content"]), "staff": sorted(rows["staff"])},
    }


def build_sheets_client():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    credentials = None
    if OAUTH_TOKEN_FILE.exists():
        credentials = Credentials.from_authorized_user_file(str(OAUTH_TOKEN_FILE), GOOGLE_SCOPES)
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            if not OAUTH_CLIENT_FILE.exists():
                print(f"ERROR: OAuth2 credentials file not found: {OAUTH_CLIENT_FILE}", file=sys.stderr)
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(str(OAUTH_CLIENT_FILE), GOOGLE_SCOPES)
            credentials = flow.run_local_server(port=0)
        OAUTH_TOKEN_FILE.write_text(credentials.to_json(), encoding="utf-8")
    return build("sheets", "v4", credentials=credentials)


def _col(row: list[str], header: list[str], name: str) -> str:
    try:
        idx = header.index(name)
    except ValueError:
        return ""
    if idx >= len(row):
        return ""
    return str(row[idx]).strip()


def _parse_sort_order(value: str) -> int:
    try:
        return int(value or "0")
    except ValueError:
        return 0


async def import_recommendations(sheets_svc, conn) -> dict[str, Any]:
    from scripts import import_trip_content

    rows = import_trip_content.filter_rows_by_trip(
        import_trip_content.read_tab(sheets_svc, TRIP_CONTENT_SHEET_ID, "Recomendacoes"),
        TRIP_UUID,
    )
    if not rows or len(rows) < 2:
        return {"status": "skipped", "trip_uuid": TRIP_UUID, "message": "No recommendations found"}

    recommendations = import_trip_content.parse_recommendations_tab(rows)
    async with conn.transaction():
        await conn.execute("DELETE FROM trip_recommendations WHERE wetravel_trip_uuid = $1", TRIP_UUID)
        for recommendation in recommendations:
            await conn.execute(
                """
                INSERT INTO trip_recommendations
                    (
                        id, wetravel_trip_uuid, name, description, address, photo_url,
                        sort_order, category, neighborhood, location, highlight,
                        price_range, rating, map_url, emoji,
                        phone, whatsapp_url, contact_label, created_at, updated_at
                    )
                VALUES (
                    gen_random_uuid(), $1, $2, $3, $4, $5,
                    $6, $7, $8, $9, $10,
                    $11, $12, $13, $14,
                    $15, $16, $17, now(), now()
                )
                """,
                TRIP_UUID,
                recommendation.name,
                recommendation.description,
                recommendation.address,
                recommendation.photo_url,
                recommendation.sort_order,
                recommendation.category,
                recommendation.neighborhood,
                recommendation.location,
                recommendation.highlight,
                recommendation.price_range,
                recommendation.rating,
                recommendation.map_url,
                recommendation.emoji,
                recommendation.phone,
                recommendation.whatsapp_url,
                recommendation.contact_label,
            )

    return {"status": "ok", "trip_uuid": TRIP_UUID, "recommendations_imported": len(recommendations)}


async def import_emergency_contacts(sheets_svc, conn) -> dict[str, Any]:
    from scripts import import_trip_content

    rows = import_trip_content.filter_rows_by_trip(
        import_trip_content.read_tab(sheets_svc, TRIP_CONTENT_SHEET_ID, "Emergency Contacts"),
        TRIP_UUID,
    )
    if not rows or len(rows) < 2:
        return {"status": "skipped", "trip_uuid": TRIP_UUID, "message": "No emergency contacts found"}

    header = [str(value).strip().lower() for value in rows[0]]
    contacts = []
    for row in rows[1:]:
        name = _col(row, header, "name")
        if not name:
            continue
        contacts.append(
            {
                "name": name,
                "role": _col(row, header, "role") or None,
                "phone": _col(row, header, "phone") or None,
                "sort_order": _parse_sort_order(_col(row, header, "sort_order")),
            }
        )

    async with conn.transaction():
        await conn.execute("DELETE FROM trip_emergency_contacts WHERE wetravel_trip_uuid = $1", TRIP_UUID)
        for contact in contacts:
            await conn.execute(
                """
                INSERT INTO trip_emergency_contacts
                    (id, wetravel_trip_uuid, name, role, phone, sort_order, created_at, updated_at)
                VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, now(), now())
                """,
                TRIP_UUID,
                contact["name"],
                contact["role"],
                contact["phone"],
                contact["sort_order"],
            )

    return {"status": "ok", "trip_uuid": TRIP_UUID, "emergency_contacts_imported": len(contacts)}


async def import_faq(sheets_svc, conn) -> dict[str, Any]:
    from scripts import import_trip_content

    rows = import_trip_content.filter_rows_by_trip(
        import_trip_content.read_tab(sheets_svc, TRIP_CONTENT_SHEET_ID, "FAQ"),
        TRIP_UUID,
    )
    if not rows or len(rows) < 2:
        return {"status": "skipped", "trip_uuid": TRIP_UUID, "message": "No FAQ rows found"}

    header = [str(value).strip().lower() for value in rows[0]]
    faqs = []
    for row in rows[1:]:
        question = _col(row, header, "question")
        answer = _col(row, header, "answer")
        if not question or not answer:
            continue
        faqs.append(
            {
                "question": question,
                "answer": answer,
                "sort_order": _parse_sort_order(_col(row, header, "sort_order")),
            }
        )

    async with conn.transaction():
        await conn.execute("DELETE FROM trip_faqs WHERE wetravel_trip_uuid = $1", TRIP_UUID)
        for faq in faqs:
            await conn.execute(
                """
                INSERT INTO trip_faqs
                    (id, wetravel_trip_uuid, question, answer, sort_order, created_at, updated_at)
                VALUES (gen_random_uuid(), $1, $2, $3, $4, now(), now())
                """,
                TRIP_UUID,
                faq["question"],
                faq["answer"],
                faq["sort_order"],
            )

    return {"status": "ok", "trip_uuid": TRIP_UUID, "imported": len(faqs)}


async def set_mode(conn, mode: str) -> dict[str, Any]:
    if mode not in ("pre-trip", "in-trip"):
        raise ValueError(f"Invalid mode '{mode}'. Must be 'pre-trip' or 'in-trip'.")
    await conn.execute(
        """
        INSERT INTO trip_settings (trip_uuid, mode)
        VALUES ($1, $2)
        ON CONFLICT (trip_uuid) DO UPDATE SET mode = $2, updated_at = now()
        """,
        TRIP_UUID,
        mode,
    )
    return {"status": "ok", "trip_uuid": TRIP_UUID, "mode": mode}


async def import_db_content(sheets=None) -> dict[str, Any]:
    from scripts import import_staff_content, import_trip_content

    sheets_svc = sheets or import_trip_content.build_sheets_client()
    conn = await import_trip_content.asyncpg.connect(import_trip_content.PG_URL)
    try:
        trip_content_result = await import_trip_content.import_one(
            sheets_svc,
            conn,
            TRIP_UUID,
            TRIP_CONTENT_SHEET_ID,
        )
        recommendations_result = await import_recommendations(sheets_svc, conn)
        emergency_contacts_result = await import_emergency_contacts(sheets_svc, conn)
        faq_result = await import_faq(sheets_svc, conn)
        staff_content_result = await import_staff_content.import_one(
            sheets_svc,
            conn,
            TRIP_UUID,
            STAFF_CONTENT_SHEET_ID,
        )
        mode_result = await set_mode(conn, "pre-trip")
    finally:
        await conn.close()

    return {
        "trip_content": trip_content_result,
        "recommendations": recommendations_result,
        "emergency_contacts": emergency_contacts_result,
        "faq": faq_result,
        "staff_content": staff_content_result,
        "mode": mode_result,
    }


def print_counts(rows: dict[str, dict[str, list[list[Any]]]]) -> None:
    for sheet_name in ("content", "staff"):
        for tab in sorted(rows[sheet_name]):
            print(f"{sheet_name}.{tab}: {len(rows[sheet_name][tab])} rows")


def main(argv: list[str] | None = None) -> dict[str, Any] | None:
    parser = argparse.ArgumentParser(description="Seed Casamento GaRapha content rows to Google Sheets.")
    parser.add_argument("--execute", action="store_true", help="Write rows to Google Sheets. Defaults to dry-run.")
    parser.add_argument(
        "--import-db",
        action="store_true",
        help="After writing sheets, import Casamento GaRapha content into the database.",
    )
    args = parser.parse_args(argv)
    if args.import_db and not args.execute:
        parser.error("--import-db requires --execute")

    rows = build_sheet_rows()
    print_counts(rows)
    if not args.execute:
        print("Dry run: no sheets were written")
        return None

    sheets = build_sheets_client()
    result = update_sheets(sheets, rows)
    print(f"Wrote content tabs: {', '.join(result['updated_tabs']['content'])}")
    print(f"Wrote staff tabs: {', '.join(result['updated_tabs']['staff'])}")
    if args.import_db:
        import_result = asyncio.run(import_db_content(sheets))
        result["db_import"] = import_result
        print("Imported database content and set mode to pre-trip")
    return result


if __name__ == "__main__":
    main()
