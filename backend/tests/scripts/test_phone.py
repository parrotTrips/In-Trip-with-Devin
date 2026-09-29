import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts._phone import normalize_phone


def test_normalize_phone_adds_missing_leading_plus():
    assert normalize_phone("5511990001234") == "+5511990001234"


def test_normalize_phone_keeps_existing_leading_plus():
    assert normalize_phone("+5511990001234") == "+5511990001234"


def test_normalize_phone_strips_spaces_dashes_and_parentheses():
    assert normalize_phone("+55 (11) 99999-0001") == "+5511999990001"
    assert normalize_phone("55 11 99999-0001") == "+5511999990001"
    assert normalize_phone("(11) 99999-0001") == "+11999990001"


def test_normalize_phone_handles_empty_and_none():
    assert normalize_phone("") == ""
    assert normalize_phone(None) == ""
    assert normalize_phone("   ") == ""


def test_normalize_phone_is_idempotent():
    once = normalize_phone("+55 (11) 99999-0001")
    twice = normalize_phone(once)
    assert once == twice == "+5511999990001"
