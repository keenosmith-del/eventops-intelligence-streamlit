"""Read-only, allowlisted external adapters. No email sending capability."""

import ipaddress
import json
import socket
import time
from urllib.parse import urlsplit

import httpx

from eventops.config import setting

DEFAULT_CALENDAR = "https://www.officeholidays.com/ics/south-africa"
DEFAULT_WEB = "https://date.nager.at/api/v3/PublicHolidays/2026/ZA"
ALLOWED_HOSTS = {"www.officeholidays.com", "date.nager.at", "mailtrap.io"}
MAX_BYTES = 512_000


class SourceError(Exception):
    pass


def validate_url(url, resolve=True):
    p = urlsplit(url)
    if (
        p.scheme != "https"
        or p.hostname not in ALLOWED_HOSTS
        or p.port not in (None, 443)
        or p.username
        or p.password
        or p.query
        or p.fragment
    ):
        raise SourceError("Source URL is outside the read-only allowlist")
    if resolve:
        try:
            addresses = socket.getaddrinfo(p.hostname, 443, type=socket.SOCK_STREAM)
            if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
                raise SourceError("Source resolved to a non-public address")
        except OSError as exc:
            raise SourceError("Source DNS lookup failed") from exc
    return url


def fetch(url, headers=None, transport=None):
    validate_url(url, resolve=transport is None)
    started = time.monotonic()
    try:
        with httpx.Client(
            timeout=httpx.Timeout(12, connect=5), follow_redirects=False, transport=transport
        ) as client:
            with client.stream(
                "GET", url, headers={"User-Agent": "EventOps-Streamlit/1.0", **(headers or {})}
            ) as response:
                if response.status_code != 200:
                    raise SourceError(f"Source returned HTTP {response.status_code}")
                chunks, size = [], 0
                for chunk in response.iter_bytes():
                    size += len(chunk)
                    if size > MAX_BYTES or time.monotonic() - started > 20:
                        raise SourceError("Source exceeded the bounded read limit")
                    chunks.append(chunk)
                return b"".join(chunks).decode("utf-8", errors="replace")
    except httpx.HTTPError as exc:
        raise SourceError("Source request failed or timed out") from exc


def mailtrap(limit=3, transport=None):
    token, account, inbox = [
        setting(k) for k in ("MAILTRAP_API_TOKEN", "MAILTRAP_ACCOUNT_ID", "MAILTRAP_INBOX_ID")
    ]
    if not all((token, account, inbox)):
        return {
            "source": "email",
            "status": "unavailable",
            "error": "Mailtrap sandbox is not configured",
            "records": [],
        }
    if not account.isdigit() or not inbox.isdigit():
        raise SourceError("Invalid Mailtrap identifiers")
    root = f"https://mailtrap.io/api/accounts/{account}/inboxes/{inbox}/messages"
    headers = {"Api-Token": token}
    try:
        messages = json.loads(fetch(root, headers, transport))
        if not isinstance(messages, list):
            raise ValueError("Expected messages array")
        output = []
        for message in messages[: min(limit, 5)]:
            mid = str(message["id"])
            if not mid.isdigit():
                raise ValueError("Invalid message ID")
            url = f"{root}/{mid}/body.txt"
            output.append(
                {
                    "id": mid,
                    "subject": str(message.get("subject", ""))[:500],
                    "body": fetch(url, headers, transport)[:12000],
                    "reference": url,
                }
            )
        return {
            "source": "email",
            "status": "completed",
            "reference": root,
            "messages": output,
            "count": len(output),
        }
    except (ValueError, KeyError, TypeError) as exc:
        raise SourceError("Unexpected Mailtrap response schema") from exc


def read_source(source, limit=3, transport=None):
    if source == "email":
        return mailtrap(limit, transport)
    url = (
        setting("CALENDAR_FEED_URL", DEFAULT_CALENDAR)
        if source == "calendar"
        else setting("WEB_SOURCE_URL", DEFAULT_WEB)
    )
    if source not in ("calendar", "web"):
        raise SourceError("Unknown source")
    return {
        "source": source,
        "status": "completed",
        "reference": url,
        "body": fetch(url, transport=transport),
    }
