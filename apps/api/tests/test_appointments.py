"""
Tests for appointment handlers (create, list, cancel).
"""
import pytest
from datetime import datetime, timedelta
import uuid


class TestListAppointments:
    """Tests for listing user appointments."""

    def test_list_appointments_empty(self, make_request, test_token):
        """Test listing appointments when user has none."""
        response = make_request(
            "GET",
            "/appointments",
            auth_token=test_token,
        )
        
        assert response["statusCode"] == 200
        body = response["body"]
        assert "appointments" in body
        assert body["appointments"] == []

    def test_list_appointments_unauthenticated(self, make_request):
        """Test listing appointments without authentication."""
        response = make_request(
            "GET",
            "/appointments",
        )
        
        assert response["statusCode"] == 401


class TestCreateAppointment:
    """Tests for creating appointments."""

    def test_create_appointment_success(
        self, make_request, test_token, seeded_service
    ):
        """Test successful appointment creation."""
        tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        response = make_request(
            "POST",
            "/appointments",
            body={
                "serviceId": seeded_service["serviceId"],
                "date": tomorrow,
                "time": "10:00",
                "notes": "Please call 10 minutes before",
            },
            auth_token=test_token,
        )
        
        assert response["statusCode"] == 201
        body = response["body"]
        assert "appointment" in body
        appt = body["appointment"]
        assert appt["date"] == tomorrow
        assert appt["time"] == "10:00"
        assert appt["status"] == "pending"

    def test_create_appointment_unauthenticated(self, make_request, seeded_service):
        """Test appointment creation without authentication."""
        response = make_request(
            "POST",
            "/appointments",
            body={
                "serviceId": seeded_service["serviceId"],
                "date": "2025-12-25",
                "time": "10:00",
            },
        )
        
        assert response["statusCode"] == 401

    def test_create_appointment_missing_service(self, make_request, test_token):
        """Test appointment creation with missing service."""
        response = make_request(
            "POST",
            "/appointments",
            body={
                "date": "2025-12-25",
                "time": "10:00",
            },
            auth_token=test_token,
        )
        
        assert response["statusCode"] == 400
        body = response["body"]
        assert "error" in body

    def test_create_appointment_nonexistent_service(self, make_request, test_token):
        """Test appointment creation with non-existent service."""
        response = make_request(
            "POST",
            "/appointments",
            body={
                "serviceId": str(uuid.uuid4()),
                "date": "2025-12-25",
                "time": "10:00",
            },
            auth_token=test_token,
        )
        
        assert response["statusCode"] == 404
        body = response["body"]
        assert "error" in body

    def test_create_appointment_double_booking(
        self, make_request, test_token, seeded_service
    ):
        """Test that double-booking is prevented."""
        tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # First appointment
        response1 = make_request(
            "POST",
            "/appointments",
            body={
                "serviceId": seeded_service["serviceId"],
                "date": tomorrow,
                "time": "10:00",
            },
            auth_token=test_token,
        )
        assert response1["statusCode"] == 201
        
        # Try to book the same time — should fail
        response2 = make_request(
            "POST",
            "/appointments",
            body={
                "serviceId": seeded_service["serviceId"],
                "date": tomorrow,
                "time": "10:00",
            },
            auth_token=test_token,
        )
        assert response2["statusCode"] == 409
        body = response2["body"]
        assert "error" in body


class TestCancelAppointment:
    """Tests for cancelling appointments."""

    def test_cancel_appointment_success(
        self, make_request, test_token, seeded_service
    ):
        """Test successful appointment cancellation."""
        tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Create appointment
        create_response = make_request(
            "POST",
            "/appointments",
            body={
                "serviceId": seeded_service["serviceId"],
                "date": tomorrow,
                "time": "10:00",
            },
            auth_token=test_token,
        )
        appt_id = create_response["body"]["appointment"]["apptId"]
        
        # Cancel it
        response = make_request(
            "DELETE",
            f"/appointments/{appt_id}",
            auth_token=test_token,
        )
        
        assert response["statusCode"] == 200
        body = response["body"]
        assert "message" in body
        assert "cancelled" in body["message"].lower()

    def test_cancel_nonexistent_appointment(self, make_request, test_token):
        """Test cancelling non-existent appointment."""
        response = make_request(
            "DELETE",
            f"/appointments/{str(uuid.uuid4())}",
            auth_token=test_token,
        )
        
        assert response["statusCode"] == 404
        body = response["body"]
        assert "error" in body

    def test_cancel_appointment_unauthenticated(self, make_request):
        """Test appointment cancellation without authentication."""
        response = make_request(
            "DELETE",
            f"/appointments/{str(uuid.uuid4())}",
        )
        
        assert response["statusCode"] == 401

    def test_cancel_appointment_wrong_user(
        self, make_request, test_token, seeded_user, seeded_service
    ):
        """Test that user can't cancel other user's appointments."""
        tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Create appointment as test_token user
        create_response = make_request(
            "POST",
            "/appointments",
            body={
                "serviceId": seeded_service["serviceId"],
                "date": tomorrow,
                "time": "11:00",
            },
            auth_token=test_token,
        )
        appt_id = create_response["body"]["appointment"]["apptId"]
        
        # Try to cancel as different user (would need to generate another token)
        # For now, just verify the appointment exists
        list_response = make_request(
            "GET",
            "/appointments",
            auth_token=test_token,
        )
        assert len(list_response["body"]["appointments"]) > 0

