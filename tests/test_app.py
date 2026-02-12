"""
Tests for the Mergington High School API
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from fastapi.testclient import TestClient
from app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def fresh_app():
    """Reset the app to a fresh state before each test"""
    # Reimport to get fresh activity data
    import importlib
    import app as app_module
    importlib.reload(app_module)
    return app_module


class TestGetActivities:
    """Tests for the GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) == 9
        assert "Basketball" in activities
        assert "Tennis Club" in activities
        assert "Drama Club" in activities

    def test_activity_structure(self, client):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        activities = response.json()
        basketball = activities["Basketball"]
        
        assert "description" in basketball
        assert "schedule" in basketball
        assert "max_participants" in basketball
        assert "participants" in basketball
        assert isinstance(basketball["participants"], list)


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_for_activity_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Basketball/signup?email=student@mergington.edu"
        )
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]

    def test_signup_for_nonexistent_activity(self, client):
        """Test signup for an activity that doesn't exist"""
        response = client.post(
            "/activities/NonexistentActivity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_already_registered(self, client):
        """Test that a student can't sign up twice for the same activity"""
        email = "duplicate@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(f"/activities/Basketball/signup?email={email}")
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(f"/activities/Basketball/signup?email={email}")
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]

    def test_participants_list_updated_after_signup(self, client):
        """Test that participants list is updated after signup"""
        email = "newstudent@mergington.edu"
        
        # Get initial participants count
        response1 = client.get("/activities")
        initial_count = len(response1.json()["Basketball"]["participants"])
        
        # Sign up
        client.post(f"/activities/Basketball/signup?email={email}")
        
        # Check updated count
        response2 = client.get("/activities")
        new_count = len(response2.json()["Basketball"]["participants"])
        
        assert new_count == initial_count + 1
        assert email in response2.json()["Basketball"]["participants"]


class TestUnregisterFromActivity:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_from_activity_success(self, client):
        """Test successful unregister from an activity"""
        email = "temp@mergington.edu"
        
        # First, sign up
        client.post(f"/activities/Basketball/signup?email={email}")
        
        # Then unregister
        response = client.delete(
            f"/activities/Basketball/unregister?email={email}"
        )
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]

    def test_unregister_from_nonexistent_activity(self, client):
        """Test unregister from an activity that doesn't exist"""
        response = client.delete(
            "/activities/NonexistentActivity/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_not_signed_up(self, client):
        """Test unregister for a student not signed up"""
        response = client.delete(
            "/activities/Basketball/unregister?email=notstudent@mergington.edu"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]

    def test_participants_list_updated_after_unregister(self, client):
        """Test that participants list is updated after unregister"""
        email = "temporary@mergington.edu"
        
        # Sign up
        client.post(f"/activities/Basketball/signup?email={email}")
        
        # Get count after signup
        response1 = client.get("/activities")
        count_after_signup = len(response1.json()["Basketball"]["participants"])
        
        # Unregister
        client.delete(f"/activities/Basketball/unregister?email={email}")
        
        # Check count after unregister
        response2 = client.get("/activities")
        count_after_unregister = len(response2.json()["Basketball"]["participants"])
        
        assert count_after_unregister == count_after_signup - 1
        assert email not in response2.json()["Basketball"]["participants"]


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirects_to_static(self, client):
        """Test that root redirects to static files"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
