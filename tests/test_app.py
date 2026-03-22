"""
Unit tests for the High School Management System API (app.py)

Tests include:
- Root endpoint redirect
- Fetching all activities
- Signing up for activities
- Unregistering from activities
- Error handling for invalid activities and duplicate signups

Structured using AAA (Arrange-Act-Assert) pattern.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirects_to_static(self):
        # Arrange
        expected_location = "/static/index.html"

        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == expected_location


class TestGetActivities:
    """Tests for the GET /activities endpoint"""

    def test_get_all_activities(self):
        # Arrange
        # No special setup needed

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        assert "Chess Club" in data
        assert "Programming Class" in data

    def test_activities_have_required_fields(self):
        # Arrange
        required_fields = ["description", "schedule", "max_participants", "participants"]

        # Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        for activity_name, activity_data in activities.items():
            for field in required_fields:
                assert field in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_successful(self):
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]

    def test_signup_nonexistent_activity(self):
        # Arrange
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_duplicate_registration(self):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already in initial data

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_different_activities(self):
        # Arrange
        email = "multisport@mergington.edu"
        activity1 = "Gym Class"
        activity2 = "Basketball Team"

        # Act
        response1 = client.post(
            f"/activities/{activity1}/signup?email={email}"
        )
        response2 = client.post(
            f"/activities/{activity2}/signup?email={email}"
        )

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200


class TestUnregisterFromActivity:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_successful(self):
        # Arrange
        email = "testunreg@mergington.edu"
        activity_name = "Art Studio"
        # First signup
        client.post(f"/activities/{activity_name}/signup?email={email}")

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]

    def test_unregister_nonexistent_activity(self):
        # Arrange
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )

        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_not_registered(self):
        # Arrange
        activity_name = "Tennis Club"
        email = "notstudent@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )

        # Assert
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]

    def test_unregister_then_signup_again(self):
        # Arrange
        email = "reregister@mergington.edu"
        activity_name = "Music Ensemble"

        # Act: Signup
        response1 = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        # Unregister
        response2 = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        # Signup again
        response3 = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200


class TestActivityParticipants:
    """Tests for verifying participant management"""

    def test_participant_added_to_activity(self):
        # Arrange
        email = "checkparticipant@mergington.edu"
        activity_name = "Debate Team"

        # Get initial participant count
        response_before = client.get("/activities")
        initial_count = len(response_before.json()[activity_name]["participants"])

        # Act: Signup
        client.post(f"/activities/{activity_name}/signup?email={email}")

        # Assert
        response_after = client.get("/activities")
        final_count = len(response_after.json()[activity_name]["participants"])
        assert final_count == initial_count + 1
        assert email in response_after.json()[activity_name]["participants"]

    def test_participant_removed_from_activity(self):
        # Arrange
        email = "removetest@mergington.edu"
        activity_name = "Science Club"

        # Signup
        client.post(f"/activities/{activity_name}/signup?email={email}")

        # Act: Unregister
        client.delete(f"/activities/{activity_name}/unregister?email={email}")

        # Assert
        response = client.get("/activities")
        assert email not in response.json()[activity_name]["participants"]