"""Read-only public smoke checks; never triggers a workflow or sends model data."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import httpx


def check_public(url, rehearsal=False):
    p = urlsplit(url)
    if p.username or p.password or p.query or p.fragment or p.path not in ("", "/"):
        raise ValueError("Use a public application origin")
    if not rehearsal and p.scheme != "https":
        raise ValueError("Public checks require HTTPS")
    if rehearsal and (p.scheme != "http" or p.hostname not in ("localhost", "127.0.0.1") or p.port != 8503):
        raise ValueError("Rehearsal smoke checks are limited to the fixed loopback proxy")
    results = []
    with httpx.Client(timeout=15, follow_redirects=False) as client:
        headers = {"Host": "localhost:8080"} if rehearsal else {}
        response = client.get(url.rstrip("/") + "/", headers=headers)
        assert response.status_code == 200 and "streamlit" in response.text.lower()
        results.append({"route": "/", "status": 200})
        for route in (
            "/webhook/eventops-verify",
            "/webhook/eventops-agent",
            "/rest/settings",
            "/api/v1/workflows",
            "/healthz",
            "/readyz",
            "/metrics",
            "/docs",
            "/openapi.json",
            "/_stcore/health",
        ):
            response = client.get(url.rstrip("/") + route, headers=headers)
            assert response.status_code == 404, route
            results.append({"route": route, "status": 404})
        for name in ("x-content-type-options", "x-frame-options", "referrer-policy", "permissions-policy"):
            assert name in response.headers
    return {
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "environment": "loopback HTTP" if rehearsal else "public HTTPS",
        "routes": results,
        "tls": "not_tested" if rehearsal else "certificate_validated_by_httpx",
        "provider_availability": "not_checked",
        "authentication_ui": "requires_browser_check",
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", required=True)
    p.add_argument("--rehearsal", action="store_true")
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    try:
        result = check_public(args.url, args.rehearsal)
    except Exception as exc:
        print(json.dumps({"status": "failed", "category": type(exc).__name__}))
        raise SystemExit(1) from None
    if args.output:
        args.output.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
