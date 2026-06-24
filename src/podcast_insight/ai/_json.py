"""Helper to pull a JSON object out of a model response.

Models usually return clean JSON when asked, but sometimes wrap it in ```json
fences or add a stray sentence. This extracts the first balanced {...} block.
"""

from __future__ import annotations

import json
import re
from typing import Any


def parse_json(text: str) -> Any:
    text = text.strip()
    # Strip code fences if present.
    fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Fall back to the first balanced brace block.
    start = text.find("{")
    if start == -1:
        raise ValueError(f"No JSON object found in model output:\n{text[:500]}")
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start : i + 1])
    raise ValueError(f"Unbalanced JSON in model output:\n{text[:500]}")
