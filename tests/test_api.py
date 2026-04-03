"""
FastAPI Backend Tests using AAA (Arrange-Act-Assert) Pattern

This test suite covers all API endpoints with comprehensive test cases:
- GET / (redirect to static files)
- GET /activities (retrieve all activities)
- POST /activities/{activity_name}/signup (register student)
- DELETE /activities/{activity_name}/signup (unregister student)
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Fixture to provide TestClient for FastAPI app"""
    return TestClient(app)


class TestRoot:
    """Tests for GET / endpoint"""

    def test_root_redirect_to_static_html(self, client):
        # Arrange: Root endpoint should redirect to static/index.html
        
        # Act: Make GET request to root
        response = client.get("/", follow_redirects=False)
        
        # Assert: Should return 307 redirect status
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        # Arrange: Expecting all activities to be returned with correct structure
        
        # Act: Request all activities
        response = client.get("/activities")
        
        # Assert: Response should be successful and return JSON
        assert response.status_code == 200
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) > 0

    def test_get_activities_contains_required_fields(self, client):
        # Arrange: Each activity should have specific fields
        required_fields = {"description", "schedule", "max_participants", "participants"}
        
        # Act: Request activities
        response = client.get("/activities")
        activities = response.json()
        
        # Assert: Each activity has all required fields
        for activity_name, activity_data in activities.items():
            assert all(field in activity_data for field in required_fields)
            assert isinstance(activity_data["max_participants"], int)
            assert isinstance(activity_data["participants"], list)

    def test_get_activities_participants_are_strings(self, client):
        # Arrange: Participant list should contain email strings
        
        # Act: Request activities
        response = client.get("/activities")
        activities = response.json()
        
        # Assert: All participants are strings (emails)
        for activity_name, activity_data in activities.items():
            for participant in activity_data["participants"]:
                assert isinstance(participant, str)

    def test_get_activities_contains_expected_activities(self, client):
        # Arrange: Should have specific activities in the database
        expected_activities = {"Chess Club", "Programming Class", "Gym Class"}
        
        # Act: Request activities
        response = client.get("/activities")
        activities = response.json()
        
        # Assert: Expected activities are present
        assert expected_activities.issubset(activities.keys())


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client):
        # Arrange: New student email and available activity
        email = "newstudent@mergington.edu"
        activity = "Basketball Team"
        
        # Act: Sign up for activity
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        
        # Assert: Should return success message
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity in data["message"]

    def test_signup_adds_participant_to_activity(self, client):
        # Arrange: New student and activity
        email = "student@mergington.edu"
        activity = "Art Club"
        
        # Act: Sign up for activity
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert: Participant list should contain the new email
        response = client.get("/activities")
        activities = response.json()
        assert email in activities[activity]["participants"]

    def test_signup_duplicate_email_rejected(self, client):
        # Arrange: Student already signed up for an activity
        email = "michael@mergington.edu"  # Already in Chess Club
        activity = "Chess Club"
        
        # Act: Try to sign up again with same email
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        
        # Assert: Should return 400 error
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()

    def test_signup_invalid_activity_returns_404(self, client):
        # Arrange: Non-existent activity
        email = "student@mergington.edu"
        activity = "NonExistentActivity"
        
        # Act: Try to sign up for non-existent activity
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        
        # Assert: Should return 404 error
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_signup_with_url_encoded_activity_name(self, client):
        # Arrange: Activity name with spaces needs URL encoding
        email = "newstudent@mergington.edu"
        activity = "Programming Class"
        encoded_activity = "Programming%20Class"
        
        # Act: Sign up with URL-encoded activity name
        response = client.post(
            f"/activities/{encoded_activity}/signup?email={email}"
        )
        
        # Assert: Should work with URL encoding
        assert response.status_code == 200

    def test_multiple_students_can_signup_for_same_activity(self, client):
        # Arrange: Multiple different emails for same activity
        emails = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        activity = "Drama Club"
        
        # Act: Sign up all students
        for email in emails:
            response = client.post(
                f"/activities/{activity}/signup?email={email}"
            )
            assert response.status_code == 200
        
        # Assert: All students should be in participant list
        response = client.get("/activities")
        activities = response.json()
        for email in emails:
            assert email in activities[activity]["participants"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/signup endpoint"""

    def test_unregister_success(self, client):
        # Arrange: Student already in participant list
        email = "michael@mergington.edu"  # Already in Chess Club
        activity = "Chess Club"
        
        # Act: Unregister from activity
        response = client.delete(
            f"/activities/{activity}/signup?email={email}"
        )
        
        # Assert: Should return success message
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert "unregistered" in data["message"].lower() or "Unregistered" in data["message"]

    def test_unregister_removes_participant_from_activity(self, client):
        # Arrange: Sign up a student first
        email = "tempstudent@mergington.edu"
        activity = "Soccer Club"
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Act: Unregister the student
        client.delete(f"/activities/{activity}/signup?email={email}")
        
        # Assert: Participant list should not contain the email
        response = client.get("/activities")
        activities = response.json()
        assert email not in activities[activity]["participants"]

    def test_unregister_non_registered_student_returns_400(self, client):
        # Arrange: Student not in participant list
        email = "notregistered@mergington.edu"
        activity = "Chess Club"
        
        # Act: Try to unregister student not in the activity
        response = client.delete(
            f"/activities/{activity}/signup?email={email}"
        )
        
        # Assert: Should return 400 error
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"].lower()

    def test_unregister_invalid_activity_returns_404(self, client):
        # Arrange: Non-existent activity
        email = "student@mergington.edu"
        activity = "FakeActivity"
        
        # Act: Try to unregister from non-existent activity
        response = client.delete(
            f"/activities/{activity}/signup?email={email}"
        )
        
        # Assert: Should return 404 error
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_unregister_with_special_characters_in_email(self, client):
        # Arrange: Sign up student with special characters
        email = "student+test@mergington.edu"
        activity = "Science Club"
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Act: Unregister with special characters
        response = client.delete(
            f"/activities/{activity}/signup?email={email}"
        )
        
        # Assert: Should successfully unregister
        assert response.status_code == 200
        
        # Assert: Participant should be removed
        response = client.get("/activities")
        activities = response.json()
        assert email not in activities[activity]["participants"]


class TestDataIntegrity:
    """Tests for data consistency and integrity"""

    def test_participant_count_matches_list_length(self, client):
        # Arrange: Access activities data
        
        # Act: Request activities
        response = client.get("/activities")
        activities = response.json()
        
        # Assert: Participant count should match list length
        for activity_name, activity_data in activities.items():
            participant_count = len(activity_data["participants"])
            assert participant_count <= activity_data["max_participants"]

    def test_signup_and_unregister_leaves_data_consistent(self, client):
        # Arrange: Get initial participant count
        response = client.get("/activities")
        initial_participants = response.json()["Debate Club"]["participants"].copy()
        initial_count = len(initial_participants)
        
        # Act: Sign up and then unregister
        email = "testuser@mergington.edu"
        client.post(f"/activities/Debate%20Club/signup?email={email}")
        client.delete(f"/activities/Debate%20Club/signup?email={email}")
        
        # Assert: Data should return to initial state
        response = client.get("/activities")
        final_participants = response.json()["Debate Club"]["participants"]
        final_count = len(final_participants)
        assert final_count == initial_count
        assert final_participants == initial_participants
