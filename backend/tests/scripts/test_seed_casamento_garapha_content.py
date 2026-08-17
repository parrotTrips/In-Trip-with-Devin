import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from scripts import seed_casamento_garapha_content as script


def rows_as_dicts(tab: str, rows: list[list[object]]) -> list[dict[str, object]]:
    header = script.MANAGED_HEADERS[tab]
    return [dict(zip(header, row, strict=True)) for row in rows]


def test_trip_uuid_is_casamento_garapha():
    assert script.TRIP_UUID == "CASAMENTO-GARAPHA-2026"


def test_build_sheet_rows_returns_four_pre_trip_phases():
    rows = script.build_sheet_rows()["content"]["Fases"]
    phases = rows_as_dicts("Fases", rows)

    assert [phase["fase"] for phase in phases] == [
        "logistica_de_viagem",
        "preparando_as_malas",
        "cuidados_e_bem_estar",
        "informacoes_do_casamento",
    ]
    assert {phase["trip_uuid"] for phase in phases} == {script.TRIP_UUID}


def test_checklist_includes_all_pre_trip_content_groups():
    rows = script.build_sheet_rows()["content"]["Checklist"]
    items = rows_as_dicts("Checklist", rows)

    labels_by_phase = {
        phase: {item["label"] for item in items if item["fase"] == phase}
        for phase in {
            "logistica_de_viagem",
            "preparando_as_malas",
            "cuidados_e_bem_estar",
            "informacoes_do_casamento",
        }
    }

    assert "Confirmar voos de chegada e retorno" in labels_by_phase["logistica_de_viagem"]
    assert "Separar roupa para o casamento" in labels_by_phase["preparando_as_malas"]
    assert "Levar protetor solar, repelente e medicacao pessoal" in labels_by_phase["cuidados_e_bem_estar"]
    assert "Revisar site do casamento e lista de presentes" in labels_by_phase["informacoes_do_casamento"]


def test_roteiro_returns_four_activities_across_three_days():
    rows = script.build_sheet_rows()["content"]["Roteiro"]
    activities = rows_as_dicts("Roteiro", rows)

    assert [activity["atividade_nome"] for activity in activities] == [
        "Jantar de Boas Vindas",
        "Passeio de Jangada",
        "Festa Pre Wedding",
        "Casamento",
    ]
    assert {(activity["dia"], activity["data"]) for activity in activities} == {
        (1, "2026-09-04"),
        (2, "2026-09-05"),
        (3, "2026-09-06"),
    }


def test_faq_returns_three_filled_rows():
    rows = script.build_sheet_rows()["content"]["FAQ"]
    faqs = rows_as_dicts("FAQ", rows)

    assert len(faqs) == 3
    assert [faq["sort_order"] for faq in faqs] == [1, 2, 3]
    assert {faq["question"] for faq in faqs} == {
        "Qual e o traje do casamento?",
        "Havera transporte para os eventos?",
        "Que horas devo chegar para a cerimonia?",
    }
    assert all(faq["answer"] for faq in faqs)


def test_recommendations_skip_placeholders_and_include_real_rows():
    rows = script.build_sheet_rows()["content"]["Recomendacoes"]
    recommendations = rows_as_dicts("Recomendacoes", rows)
    names = {recommendation["name"] for recommendation in recommendations}

    assert recommendations
    assert all(recommendation["name"] for recommendation in recommendations)
    assert all("placeholder" not in str(recommendation["name"]).lower() for recommendation in recommendations)
    assert names >= {
        "Aulas de Yoga, Canoa Havaiana e Kayak / Espaco Imparti",
        "Aulas de Kitesurf - Professor Bete",
        "Lucas - Guia e Aluguel Quadri",
        "Ianaele - Cabelo e Maquiagem",
        "Jimmy - Transfer Aeroporto Jeri - Prea e Taxi",
        "Balcon",
        "Rancho do Peixe",
        "Alisios",
        "Restaurante da Lu",
        "Casinha",
        "Restaurante Caboclo",
        "Restaurante Arriegua",
    }
    assert {recommendation["category"] for recommendation in recommendations} >= {
        "Esportes",
        "Turismo",
        "Beleza",
        "Transporte",
        "Restaurantes",
    }


def test_emergency_contacts_contains_marine_carneiro():
    rows = script.build_sheet_rows()["content"]["Emergency Contacts"]
    contacts = rows_as_dicts("Emergency Contacts", rows)

    assert any(contact["name"] == "Marine Carneiro" for contact in contacts)


def test_staff_contacts_contains_marine_carneiro():
    rows = script.build_sheet_rows()["staff"]["Contatos"]
    contacts = rows_as_dicts("Contatos", rows)

    assert any(contact["name"] == "Marine Carneiro" for contact in contacts)
