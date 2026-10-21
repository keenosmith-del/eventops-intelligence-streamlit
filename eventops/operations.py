"""Deployment boundaries and operational metadata. Never log payloads or secrets."""

import json
import logging
import threading
import time
from urllib.parse import urlsplit

from sqlalchemy.engine import make_url

from eventops.config import setting

LOGGER = logging.getLogger("eventops.operations")
if not LOGGER.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    LOGGER.addHandler(handler)
LOGGER.setLevel(logging.INFO)
LOGGER.propagate = False


def emit(event, **fields):
    allowed = {
        "request_id",
        "run_id",
        "execution_id",
        "stage",
        "source",
        "status",
        "duration_ms",
        "error_category",
        "http_status",
        "workflow_revision",
    }
    LOGGER.info(
        json.dumps(
            {"event": event, "timestamp": time.time(), **{k: v for k, v in fields.items() if k in allowed}}
        )
    )


def private_origin(url, variable):
    """Exact administrator-configured origin, never supplied by an end user."""
    configured = setting(variable)
    p = urlsplit(configured)
    u = urlsplit(url)
    return bool(
        configured
        and p.scheme == "http"
        and p.hostname
        and p.hostname not in ("localhost", "127.0.0.1", "host.docker.internal")
        and not p.username
        and not p.password
        and not p.query
        and not p.fragment
        and p.path in ("", "/")
        and (u.scheme, u.netloc) == (p.scheme, p.netloc)
    )


def validate_database(url, production=None):
    production = setting("PRODUCTION_MODE") == "true" if production is None else production
    try:
        parsed = make_url(url)
    except Exception:
        raise ValueError("Invalid dedicated database URL") from None
    if production:
        if parsed.drivername != "postgresql+psycopg":
            raise ValueError("Production requires dedicated PostgreSQL")
        if setting("RELEASE_REHEARSAL") != "true":
            mode = parsed.query.get("sslmode")
            if mode != "verify-full":
                raise ValueError("Hosted PostgreSQL requires sslmode=verify-full and a trusted CA")
            if parsed.host in ("localhost", "127.0.0.1", "host.docker.internal", "database"):
                raise ValueError("Production database must be the approved independent hosted database")
    return parsed


def production_errors():
    if setting("PRODUCTION_MODE") != "true":
        return []
    errors = []
    for name in ("APP_PASSWORD", "N8N_WEBHOOK_TOKEN"):
        if len(setting(name)) < 32:
            errors.append(name + " requires at least 32 characters")
    if setting("PUBLIC_DEMO") != "true" or setting("KNOWLEDGE_ADMIN_ENABLED") == "true":
        errors.append("Production requires the access gate and disabled knowledge administration")
    if setting("EVENTOPS_LOCAL_COMPOSE") == "true" or setting("ENABLE_LOCAL_SCENARIO") == "true":
        errors.append("Development trust switches must be disabled in production")
    try:
        validate_database(setting("EVENTOPS_DATABASE_URL"))
    except (ValueError, TypeError):
        errors.append("Production database/TLS configuration is invalid")
    return errors


class WindowLimiter:
    """Small process-local login throttle; no identities or credentials retained."""

    def __init__(self, limit=10, seconds=60):
        self.limit, self.seconds = limit, seconds
        self.window, self.count = None, 0
        self.lock = threading.Lock()

    def allow(self):
        window = int(time.monotonic() // self.seconds)
        with self.lock:
            if window != self.window:
                self.window, self.count = window, 0
            self.count += 1
            return self.count <= self.limit


def reserve_run_capacity(store, owner):
    if setting("PRODUCTION_MODE") != "true":
        return True
    import hashlib

    hour = int(time.time() // 3600)
    owner_hash = hashlib.sha256(owner.encode()).hexdigest()[:20]
    for namespace, limit in (
        (f"runs-owner-{owner_hash}-{hour}", int(setting("RUNS_PER_WORKSPACE_HOUR", "6"))),
        (f"runs-global-{hour}", int(setting("RUNS_PER_HOUR", "30"))),
    ):
        if not any(store.reserve("rate", f"{namespace}:{slot}", {}) for slot in range(limit)):
            return False
    return True
