# tests/test_app.py

import copy
import pytest
from fastapi.testclient import TestClient

from src import app as app_module

client = TestClient(app_module.app)


@pytest.fixture(autouse=True)
def reset_activities():
    """
    Keep the global `activities` dict pristine between tests by
    snapshotting and restoring a deep copy.
    """
    original = copy.deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(copy.deepcopy(original))


def test_get_activities():
    # Arrange: nothing special to set up for this read-only endpoint

    # Act
    resp = client.get("/activities")

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    # sanity check – some known activity must be present
    assert "Chess Club" in data
    assert isinstance(data["Chess Club"]["participants"], list)


def test_signup_success():
    # Arrange
    email = "new@mergington.edu"
    # ensure student not already in list (implicit by reset fixture)

    # Act
    resp = client.post(
        "/activities/Chess Club/signup", params={"email": email}
    )

    # Assert
    assert resp.status_code == 200
    assert email in app_module.activities["Chess Club"]["participants"]
    assert resp.json()["message"].startswith("Signed up")


def test_signup_duplicate():
    # Arrange
    existing_email = "michael@mergington.edu"  # already in baseline data

    # Act
    resp = client.post(
        "/activities/Chess Club/signup",
        params={"email": existing_email},
    )

    # Assert
    assert resp.status_code == 400
    assert "already signed up" in resp.json()["detail"]


def test_signup_nonexistent_activity():
    # Arrange
    email = "foo@bar.com"

    # Act
    resp = client.post(
        "/activities/NoSuchActivity/signup",
        params={"email": email},
    )

    # Assert
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Activity not found"


def test_unregister_success():
    # Arrange
    email = "temp@mergington.edu"
    client.post(
        "/activities/Chess Club/signup", params={"email": email}
    )

    # Act
    resp = client.delete(
        "/activities/Chess Club/unregister", params={"email": email}
    )

    # Assert
    assert resp.status_code == 200
    assert email not in app_module.activities["Chess Club"]["participants"]
    assert resp.json()["message"].startswith("Removed")


def test_unregister_not_registered():
    # Arrange
    email = "ghost@mergington.edu"  # not in any activity list

    # Act
    resp = client.delete(
        "/activities/Chess Club/unregister",
        params={"email": email},
    )

    # Assert
    assert resp.status_code == 404
    assert "not registered" in resp.json()["detail"]


def test_unregister_nonexistent_activity():
    # Arrange
    email = "foo@bar.com"

    # Act
    resp = client.delete(
        "/activities/NoSuchActivity/unregister",
        params={"email": email},
    )

    # Assert
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Activity not found"
