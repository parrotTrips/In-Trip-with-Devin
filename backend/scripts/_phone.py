"""Phone-number normalization shared by the traveler and staff import scripts.

Not a validator: just enough normalization so the same real phone number
resolves to the same `users.phone` value across every importer, regardless of
how it was typed into a spreadsheet or CSV cell — a missing leading "+", or
spaces/dashes/parentheses around the digits.
"""

from __future__ import annotations

import re


def normalize_phone(value: str | None) -> str:
    """Strip everything but digits, then restore a single leading "+".

    Examples:
      "+55 (11) 99999-0001" -> "+5511999990001"
      "55 11 99999-0001"    -> "+5511999990001"
      "5511999990001"       -> "+5511999990001"
      ""                    -> ""
      None                  -> ""
    """
    digits = re.sub(r"\D", "", value or "")
    return f"+{digits}" if digits else ""
