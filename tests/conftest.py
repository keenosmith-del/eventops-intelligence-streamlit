import pytest

from eventops.pipeline import deduplicate, extract, normalize, verify
from eventops.store import Store


@pytest.fixture
def store(tmp_path):
    return Store("sqlite:///" + str(tmp_path / "test.db"))


@pytest.fixture
def message():
    return {
        "source": "email",
        "status": "completed",
        "reference": "https://mailtrap.io/synthetic",
        "messages": [
            {
                "id": "1",
                "subject": "Synthetic registration",
                "body": "Event ID: EVT-101\nName: Ada Mensah\nEmail: ADA.MENSAH@example.com",
                "reference": "https://mailtrap.io/synthetic/1",
            }
        ],
    }


@pytest.fixture
def processed(message):
    return verify(deduplicate(normalize(extract(message))), "EVT-101")
