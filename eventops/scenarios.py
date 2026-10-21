"""Backend-owned source scenarios; no operator-supplied URLs."""

from urllib.parse import urlsplit

from eventops.config import setting

SCENARIOS = {
    "external_reference": "External reference connectivity",
    "assessment_event": "Controlled assessment event",
    "provider_unavailable": "Controlled event with unavailable Web",
}


def configuration(scenario="external_reference"):
    from eventops.providers import DEFAULT_CALENDAR, DEFAULT_WEB, SourceError, validate_url

    if scenario not in SCENARIOS:
        raise ValueError("Unknown source scenario")
    if scenario == "external_reference":
        urls = {
            "calendar": setting("CALENDAR_FEED_URL", DEFAULT_CALENDAR),
            "web": setting("WEB_SOURCE_URL", DEFAULT_WEB),
        }
        classification = "Real external public reference observations; not event registrations"
    else:
        base = setting("ASSESSMENT_SOURCE_BASE_URL", "")
        p = urlsplit(base)
        local = (
            setting("ENABLE_LOCAL_SCENARIO") == "true"
            and p.scheme == "http"
            and p.hostname in ("scenario", "127.0.0.1", "host.docker.internal")
            and p.port == 8090
        )
        external = (
            p.scheme == "https"
            and p.hostname == setting("ASSESSMENT_SOURCE_HOST")
            and bool(setting("ASSESSMENT_SOURCE_HOST"))
        )
        if (
            not (local or external)
            or p.username
            or p.password
            or p.query
            or p.fragment
            or p.path not in ("", "/")
        ):
            urls = {"calendar": "", "web": ""}
        else:
            urls = {
                "calendar": base.rstrip("/") + "/calendar.ics",
                "web": base.rstrip("/")
                + ("/unavailable" if scenario == "provider_unavailable" else "/records.json"),
            }
        classification = (
            "Controlled synthetic event data over actual HTTP; fixture service is not an external provider"
        )
    errors = {}
    for source, url in urls.items():
        try:
            if scenario == "external_reference":
                validate_url(url, resolve=False)
            elif not url:
                raise SourceError("Assessment source service is not configured")
        except SourceError as exc:
            errors[source] = str(exc)
            urls[source] = ""
    return {**urls, "scenario": scenario, "classification": classification, "configuration_errors": errors}
