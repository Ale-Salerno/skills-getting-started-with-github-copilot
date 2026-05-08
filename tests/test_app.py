from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


BASE_ACTIVITIES = deepcopy(app_module.activities)
client = TestClient(app_module.app)


@pytest.fixture(autouse=True)
def reset_activities_state():
    app_module.activities.clear()
    app_module.activities.update(deepcopy(BASE_ACTIVITIES))
    yield
    app_module.activities.clear()
    app_module.activities.update(deepcopy(BASE_ACTIVITIES))


def test_root_redirects_to_static_index():
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_map():
    response = client.get("/activities")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert len(data) == len(BASE_ACTIVITIES)
    assert "Science Club" in data
    assert "participants" in data["Science Club"]


def test_signup_success_for_valid_activity_and_email():
    email = "new.student@mergington.edu"

    response = client.post(
        "/activities/Science Club/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Science Club"}
    assert email in app_module.activities["Science Club"]["participants"]


def test_signup_returns_404_for_unknown_activity():
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_returns_400_when_student_already_signed_up():
    existing_email = app_module.activities["Science Club"]["participants"][0]

    response = client.post(
        "/activities/Science Club/signup",
        params={"email": existing_email},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up"}


def test_unregister_success_for_enrolled_student():
    enrolled_email = app_module.activities["Science Club"]["participants"][0]

    response = client.delete(
        "/activities/Science Club/unregister",
        params={"email": enrolled_email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {enrolled_email} from Science Club"
    }
    assert enrolled_email not in app_module.activities["Science Club"]["participants"]


def test_unregister_returns_404_for_unknown_activity():
    response = client.delete(
        "/activities/Unknown Club/unregister",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_returns_400_for_non_enrolled_student():
    email = "not.enrolled@mergington.edu"

    response = client.delete(
        "/activities/Science Club/unregister",
        params={"email": email},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Student not signed up for this activity"}
