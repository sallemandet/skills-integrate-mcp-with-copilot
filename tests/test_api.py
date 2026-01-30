import copy
from fastapi.testclient import TestClient
import pytest

from src import app as app_module

client = TestClient(app_module.app)


@pytest.fixture(autouse=True)
def restore_activities():
    """Restore the module-level `activities` dict after each test so tests are isolated."""
    original = copy.deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(original)


def test_get_activities_returns_expected_structure():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    # ensure a few known activities from the seed exist
    assert "Chess Club" in data
    assert "Programming Class" in data


def test_signup_and_unregister_flow():
    activity = "Math Club"
    email = "tester@example.com"

    # ensure email not present
    resp = client.get("/activities")
    assert email not in resp.json()[activity]["participants"]

    # signup
    resp = client.post(f"/activities/{activity}/signup?email={email}")
    assert resp.status_code == 200
    assert f"Signed up {email} for {activity}" in resp.json()["message"]

    # verify present
    resp = client.get("/activities")
    assert email in resp.json()[activity]["participants"]

    # unregister
    resp = client.delete(f"/activities/{activity}/unregister?email={email}")
    assert resp.status_code == 200
    assert f"Unregistered {email} from {activity}" in resp.json()["message"]

    # verify removed
    resp = client.get("/activities")
    assert email not in resp.json()[activity]["participants"]


def test_signup_existing_participant_returns_400():
    activity = "Chess Club"
    # pick an existing participant from the seed
    existing = app_module.activities[activity]["participants"][0]

    resp = client.post(f"/activities/{activity}/signup?email={existing}")
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Student is already signed up"


def test_unknown_activity_returns_404_on_signup_and_unregister():
    resp = client.post("/activities/NoSuchActivity/signup?email=a@b.com")
    assert resp.status_code == 404

    resp = client.delete("/activities/NoSuchActivity/unregister?email=a@b.com")
    assert resp.status_code == 404
