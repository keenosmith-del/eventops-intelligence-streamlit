import httpx
import pytest

from eventops.providers import SourceError, fetch, mailtrap, read_source, validate_url


@pytest.mark.parametrize(
    "url",
    [
        "http://www.officeholidays.com/ics",
        "https://127.0.0.1",
        "https://example.com",
        "https://mailtrap.io:8443/api",
        "https://user:pass@mailtrap.io/api",
        "https://mailtrap.io/api?token=secret",
    ],
)
def test_url_allowlist(url):
    with pytest.raises(SourceError):
        validate_url(url, resolve=False)


@pytest.mark.parametrize("status", [301, 401, 429, 500])
def test_http_errors(status):
    with pytest.raises(SourceError, match=str(status)):
        fetch(
            "https://date.nager.at/api",
            transport=httpx.MockTransport(lambda request: httpx.Response(status)),
        )


def test_timeout():
    def timeout(request):
        raise httpx.ReadTimeout("test")

    with pytest.raises(SourceError, match="timed out"):
        fetch("https://date.nager.at/api", transport=httpx.MockTransport(timeout))


def test_size_limit():
    with pytest.raises(SourceError, match="bounded"):
        fetch(
            "https://date.nager.at/api",
            transport=httpx.MockTransport(lambda request: httpx.Response(200, text="a" * 512001)),
        )


def test_missing_mailtrap(monkeypatch):
    monkeypatch.delenv("MAILTRAP_API_TOKEN", raising=False)
    assert mailtrap()["status"] == "unavailable"


@pytest.mark.parametrize("bad", ["{}", '[{"id":"../not-valid"}]', '"wrong"'])
def test_mailtrap_schema(monkeypatch, bad):
    for k, v in [
        ("MAILTRAP_API_TOKEN", "test"),
        ("MAILTRAP_ACCOUNT_ID", "1"),
        ("MAILTRAP_INBOX_ID", "2"),
    ]:
        monkeypatch.setenv(k, v)
    with pytest.raises(SourceError):
        mailtrap(transport=httpx.MockTransport(lambda request: httpx.Response(200, text=bad)))


def test_mailtrap_read_only(monkeypatch):
    for k, v in [
        ("MAILTRAP_API_TOKEN", "test"),
        ("MAILTRAP_ACCOUNT_ID", "1"),
        ("MAILTRAP_INBOX_ID", "2"),
    ]:
        monkeypatch.setenv(k, v)
    paths = []

    def handler(request):
        assert request.method == "GET"
        assert request.headers["Api-Token"] == "test"
        paths.append(request.url.path)
        return (
            httpx.Response(200, text="Synthetic body")
            if request.url.path.endswith("body.txt")
            else httpx.Response(200, json=[{"id": 3, "subject": "Synthetic"}])
        )

    result = mailtrap(transport=httpx.MockTransport(handler))
    assert result["count"] == 1
    assert len(paths) == 2


def test_read_adapters():
    transport = httpx.MockTransport(lambda request: httpx.Response(200, text="body"))
    for source in ["calendar", "web"]:
        assert read_source(source, transport=transport)["status"] == "completed"
