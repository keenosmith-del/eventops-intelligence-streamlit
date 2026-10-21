"""Sanitize exported evidence only; private persisted provenance remains intact."""

import json
import re


def sanitize(value):
    text = json.dumps(value, ensure_ascii=False)
    text = re.sub(
        r"mailtrap\.io/api/accounts/\d+/inboxes/\d+",
        "mailtrap.io/api/accounts/REDACTED/inboxes/REDACTED",
        text,
    )
    value = json.loads(text)

    def walk(v):
        if isinstance(v, dict):
            return {
                k: walk(x)
                for k, x in v.items()
                if k not in {"owner", "headers", "apiKey", "api_key", "token", "password"}
            }
        if isinstance(v, list):
            return [walk(x) for x in v]
        return v

    return walk(value)
