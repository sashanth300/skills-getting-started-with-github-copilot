"""
Tests for the Mergington High School Activities API

Uses the AAA (Arrange-Act-Assert) pattern:
- Arrange: Set up test data and preconditions
- Act: Execute the code being tested
- Assert: Verify the results
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


class TestActivitiesEndpoint:
    """Test the GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self):
        """Should return a dict of all activities"""
        # Arrange
        expected_activity = "Chess Club"
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        assert expected_activity in data

    def test_get_activities_has_required_fields(self):
        """Each activity should have required fields"""
        # Arrange
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        for activity_name, activity in data.items():
            for field in required_fields:
                assert field in activity, f"Missing field '{field}' in {activity_name}"
            assert isinstance(activity["participants"], list)

    def test_get_activities_participants_are_emails(self):
        """Participants should be email strings"""
        # Arrange
        email_indicator = "@"
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        for activity in data.values():
            for participant in activity["participants"]:
                assert isinstance(participant, str)
                assert email_indicator in participant


class TestSignupEndpoint:
    """Test the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_successful(self):
        """Should successfully sign up a new student"""
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]

    def test_signup_adds_participant_to_activity(self):
        """Signup should add participant to activity's participant list"""
        # Arrange
        activity_name = "Programming Class"
        email = "test.add@mergington.edu"
        
        # Act
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        activities_response = client.get("/activities")
        
        # Assert
        assert signup_response.status_code == 200
        activities = activities_response.json()
        assert email in activities[activity_name]["participants"]

    def test_signup_nonexistent_activity(self):
        """Should return 404 for non-existent activity"""
        # Arrange
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_duplicate_student(self):
        """Should reject signing up the same student twice"""
        # Arrange
        activity_name = "Soccer Team"
        email = "duplicate@mergington.edu"
        
        # Act - First signup
        first_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Act - Second signup (duplicate)
        second_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert first_response.status_code == 200
        assert second_response.status_code == 400
        assert "already signed up" in second_response.json()["detail"]

    def test_signup_returns_correct_message(self):
        """Signup should return a success message with email and activity"""
        # Arrange
        activity_name = "Art Club"
        email = "message.test@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert email in data["message"]
        assert activity_name in data["message"]


class TestRemoveParticipantEndpoint:
    """Test the DELETE /activities/{activity_name}/participants endpoint"""

    def test_remove_participant_successful(self):
        """Should successfully remove a participant"""
        # Arrange
        activity_name = "Debate Team"
        email = "remove.test@mergington.edu"
        # Setup: add participant first
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]

    def test_remove_participant_from_activity(self):
        """Remove should delete participant from activity"""
        # Arrange
        activity_name = "Science Club"
        email = "remove.verify@mergington.edu"
        # Setup: add participant
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Act - Remove participant
        client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )
        
        # Act - Verify removed
        response = client.get("/activities")
        
        # Assert
        activities = response.json()
        assert email not in activities[activity_name]["participants"]

    def test_remove_nonexistent_activity(self):
        """Should return 404 for non-existent activity"""
        # Arrange
        activity_name = "Fake Club"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404

    def test_remove_nonexistent_participant(self):
        """Should return 404 when participant not found"""
        # Arrange
        activity_name = "Drama Society"
        email = "notfound@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Participant not found" in response.json()["detail"]


class TestRootEndpoint:
    """Test the GET / endpoint"""

    def test_root_redirects_to_static_index(self):
        """Root path should redirect to static/index.html"""
        # Arrange
        expected_location = "/static/index.html"
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == expected_location
