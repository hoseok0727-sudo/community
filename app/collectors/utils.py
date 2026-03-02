from __future__ import annotations

import re


def safe_int(value: str | int | None) -> int:
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    cleaned = re.sub(r"[^0-9-]", "", value)
    if not cleaned or cleaned == "-":
        return 0
    try:
        return int(cleaned)
    except ValueError:
        return 0

