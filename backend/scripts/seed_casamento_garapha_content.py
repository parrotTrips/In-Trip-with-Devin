"""Build Casamento GaRapha content rows for Google Sheets.

This module is intentionally side-effect free for Tasks 1 and 2. It only
defines constants and returns row data shaped for the existing sheet importers.
"""

from __future__ import annotations

import argparse
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
        [TRIP_UUID, "Marine Carneiro", "Apoio da cerimonia", "", 1],
    ],
    "Recomendacoes": [
        [
            TRIP_UUID,
            "Aulas de Yoga, Canoa Havaiana e Kayak / Espaco Imparti",
            "Aulas e experiencias de yoga, canoa havaiana e kayak em Prea.",
            "Prea, Cruz - CE",
            "",
            1,
            "Esportes",
            "Prea",
            "Prea, CE",
            "Atividades de bem-estar e mar para dias livres.",
            "$$",
            "",
            "",
            "yoga",
        ],
        [
            TRIP_UUID,
            "Aulas de Kitesurf - Professor Bete",
            "Aulas de kitesurf com professor local para aproveitar os ventos de Prea.",
            "Prea, Cruz - CE",
            "",
            2,
            "Esportes",
            "Prea",
            "Prea, CE",
            "Opcao para quem quer praticar kitesurf durante a viagem.",
            "$$$",
            "",
            "",
            "kite",
        ],
        [
            TRIP_UUID,
            "Lucas - Guia e Aluguel Quadri",
            "Guia local e aluguel de quadriciclo para passeios na regiao.",
            "Prea, Cruz - CE",
            "",
            3,
            "Turismo",
            "Prea",
            "Prea, CE",
            "Alternativa para conhecer lagoas, dunas e arredores com apoio local.",
            "$$$",
            "",
            "",
            "quad",
        ],
        [
            TRIP_UUID,
            "Ianaele - Cabelo e Maquiagem",
            "Servico local de cabelo e maquiagem para os eventos do casamento.",
            "Prea, Cruz - CE",
            "",
            4,
            "Beleza",
            "Prea",
            "Prea, CE",
            "Reserve com antecedencia para o dia do casamento.",
            "$$",
            "",
            "",
            "makeup",
        ],
        [
            TRIP_UUID,
            "Jimmy - Transfer Aeroporto Jeri - Prea e Taxi",
            "Transfer entre Aeroporto de Jericoacoara, Prea e deslocamentos de taxi.",
            "Prea, Cruz - CE",
            "",
            5,
            "Transporte",
            "Prea",
            "Prea, CE",
            "Combine horarios, voos e pontos de encontro com antecedencia.",
            "$$",
            "",
            "",
            "transfer",
        ],
        [
            TRIP_UUID,
            "Balcon",
            "Restaurante indicado em Prea para refeicoes durante dias livres.",
            "Prea, Cruz - CE",
            "",
            6,
            "Restaurantes",
            "Prea",
            "Prea, CE",
            "Opcao local para almoco ou jantar.",
            "$$",
            "",
            "",
            "restaurant",
        ],
        [
            TRIP_UUID,
            "Rancho do Peixe",
            "Restaurante e estrutura do Rancho do Peixe em Prea.",
            "Prea, Cruz - CE",
            "",
            7,
            "Restaurantes",
            "Prea",
            "Prea, CE",
            "Opcao conhecida para refeicoes e encontros na praia.",
            "$$$",
            "",
            "",
            "restaurant",
        ],
        [
            TRIP_UUID,
            "Alisios",
            "Restaurante local indicado para refeicoes em Prea.",
            "Prea, Cruz - CE",
            "",
            8,
            "Restaurantes",
            "Prea",
            "Prea, CE",
            "Boa opcao para jantar em dias livres.",
            "$$",
            "",
            "",
            "restaurant",
        ],
        [
            TRIP_UUID,
            "Restaurante da Lu",
            "Restaurante local indicado para comida regional.",
            "Prea, Cruz - CE",
            "",
            9,
            "Restaurantes",
            "Prea",
            "Prea, CE",
            "Opcao simples e local para almoco ou jantar.",
            "$$",
            "",
            "",
            "restaurant",
        ],
        [
            TRIP_UUID,
            "Casinha",
            "Restaurante indicado em Prea para refeicoes durante a estadia.",
            "Prea, Cruz - CE",
            "",
            10,
            "Restaurantes",
            "Prea",
            "Prea, CE",
            "Opcao pratica para dias livres entre os eventos.",
            "$$",
            "",
            "",
            "restaurant",
        ],
        [
            TRIP_UUID,
            "Restaurante Caboclo",
            "Restaurante local recomendado na regiao de Prea.",
            "Prea, Cruz - CE",
            "",
            11,
            "Restaurantes",
            "Prea",
            "Prea, CE",
            "Opcao local para refeicoes com convidados.",
            "$$",
            "",
            "",
            "restaurant",
        ],
        [
            TRIP_UUID,
            "Restaurante Arriegua",
            "Restaurante recomendado para refeicoes durante a viagem.",
            "Prea, Cruz - CE",
            "",
            12,
            "Restaurantes",
            "Prea",
            "Prea, CE",
            "Opcao para almoco ou jantar em dias livres.",
            "$$",
            "",
            "",
            "restaurant",
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
        [TRIP_UUID, "informacoes_do_casamento", 1, "Site do casamento", ""],
        [TRIP_UUID, "informacoes_do_casamento", 2, "Lista de presentes", ""],
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
            "informativo",
            "",
            "",
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
            "informativo",
            "",
            "",
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
            "informativo",
            "",
            "",
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
            "informativo",
            "",
            "",
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
        [TRIP_UUID, "Cerimonia", "Marine Carneiro", "Apoio da cerimonia", "", 1],
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


def ensure_tab(sheets, spreadsheet_id: str, tab: str) -> None:
    meta = sheets.spreadsheets().get(spreadsheetId=spreadsheet_id, fields="sheets.properties.title").execute()
    titles = {sheet["properties"]["title"] for sheet in meta.get("sheets", [])}
    if tab in titles:
        return
    sheets.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": [{"addSheet": {"properties": {"title": tab}}}]},
    ).execute()


def replace_trip_rows(sheets, spreadsheet_id: str, tab: str, new_rows: list[list[Any]]) -> None:
    ensure_tab(sheets, spreadsheet_id, tab)
    values = (
        sheets.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=f"'{tab}'!A:Z")
        .execute()
        .get("values", [])
    )
    header = MANAGED_HEADERS.get(tab) or (values[0] if values else [])
    merged = merge_trip_rows(values, header, new_rows)
    sheets.spreadsheets().values().clear(spreadsheetId=spreadsheet_id, range=f"'{tab}'!A:Z").execute()
    sheets.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f"'{tab}'!A:Z",
        valueInputOption="RAW",
        body={"values": merged},
    ).execute()


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


def print_counts(rows: dict[str, dict[str, list[list[Any]]]]) -> None:
    for sheet_name in ("content", "staff"):
        for tab in sorted(rows[sheet_name]):
            print(f"{sheet_name}.{tab}: {len(rows[sheet_name][tab])} rows")


def main(argv: list[str] | None = None) -> dict[str, Any] | None:
    parser = argparse.ArgumentParser(description="Seed Casamento GaRapha content rows to Google Sheets.")
    parser.add_argument("--execute", action="store_true", help="Write rows to Google Sheets. Defaults to dry-run.")
    args = parser.parse_args(argv)

    rows = build_sheet_rows()
    print_counts(rows)
    if not args.execute:
        print("Dry run: no sheets were written")
        return None

    result = update_sheets(build_sheets_client(), rows)
    print(f"Wrote content tabs: {', '.join(result['updated_tabs']['content'])}")
    print(f"Wrote staff tabs: {', '.join(result['updated_tabs']['staff'])}")
    return result


if __name__ == "__main__":
    main()
