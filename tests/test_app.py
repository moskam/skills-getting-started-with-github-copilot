"""
Tests for the Mergington High School API.

All tests follow the Arrange-Act-Assert (AAA) pattern.
"""

import copy
import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

# ---------------------------------------------------------------------------
# Snapshot of the initial activities state, taken once at module import time.
# The autouse fixture below restores activities to this state before each test
# so that tests cannot bleed state into one another.
# ---------------------------------------------------------------------------
_INITIAL_ACTIVITIES = copy.deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the in-memory activities dict to its original state before every test."""
    # Arrange (shared): reset to known-good state
    activities.clear()
    activities.update(copy.deepcopy(_INITIAL_ACTIVITIES))
    yield


@pytest.fixture()
def client():
    """Return a FastAPI TestClient bound to the app."""
    return TestClient(app)


# ===========================================================================
# GET /activities
# ===========================================================================

class TestGetActivities:
    def test_returns_200(self, client):
        # Arrange: client is ready, no extra setup needed

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200

    def test_returns_all_activities(self, client):
        # Arrange
        expected_names = {
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Soccer Team",
            "Swimming Team",
            "Drama Club",
            "School Band",
            "Math Olympiad",
            "Debate Society",
        }

        # Act
        response = client.get("/activities")

        # Assert
        assert set(response.json().keys()) == expected_names

    def test_activity_structure(self, client):
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}

        # Act
        response = client.get("/activities")

        # Assert
        for name, data in response.json().items():
            assert required_fields.issubset(data.keys()), (
                f"Activity '{name}' is missing required fields"
            )


# ===========================================================================
# POST /activities/{activity_name}/signup
# ===========================================================================

class TestSignup:
    def test_signup_success(self, client):
        # Arrange
        activity_name = "Chess Club"
        new_email = "newstudent@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email},
        )

        # Assert
        assert response.status_code == 200
        assert response.json() == {"message": f"Signed up {new_email} for {activity_name}"}
        assert new_email in activities[activity_name]["participants"]

    def test_signup_normalizes_email(self, client):
        # Arrange: email with leading/trailing spaces and uppercase letters
        activity_name = "Chess Club"
        raw_email = "  NewStudent@Mergington.EDU  "
        expected_email = "newstudent@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": raw_email},
        )

        # Assert
        assert response.status_code == 200
        assert expected_email in activities[activity_name]["participants"]

    def test_signup_activity_not_found(self, client):
        # Arrange
        unknown_activity = "Underwater Basket Weaving"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{unknown_activity}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_already_registered(self, client):
        # Arrange: michael is already in Chess Club (seed data)
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": existing_email},
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up for this activity"


# ===========================================================================
# DELETE /activities/{activity_name}/signup
# ===========================================================================

class TestUnregister:
    def test_unregister_success(self, client):
        # Arrange: michael is already in Chess Club (seed data)
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 200
        assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
        assert email not in activities[activity_name]["participants"]

    def test_unregister_activity_not_found(self, client):
        # Arrange
        unknown_activity = "Underwater Basket Weaving"
        email = "student@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{unknown_activity}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_not_signed_up(self, client):
        # Arrange: this student is not in Chess Club
        activity_name = "Chess Club"
        email = "nothere@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Student is not signed up for this activity"
