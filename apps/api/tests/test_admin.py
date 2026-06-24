"""
Tests for admin handlers (appointments, users, stats, services, availability, config).
"""
import pytest
from datetime import datetime, timedelta
import uuid


class TestAdminAppointments:
    """Tests for admin appointment operations."""

    def test_admin_list_appointments(self, make_request, admin_token):
        """Test admin listing all appointments."""
        response = make_request(
            "GET",
            "/admin/appointments",
            auth_token=admin_token,
        )
        
        assert response["statusCode"] == 200
        body = response["body"]
        assert "appointments" in body
        assert "count" in body

    def test_admin_list_appointments_by_status(self, make_request, admin_token):
        """Test admin filtering appointments by status."""
        response = make_request(
            "GET",
            "/admin/appointments",
            query={"status": "pending"},
            auth_token=admin_token,
        )
        
        assert response["statusCode"] == 200
        body = response["body"]
        assert "appointments" in body

    def test_admin_list_appointments_unauthenticated(self, make_request):
        """Test admin appointments without authentication."""
        response = make_request(
            "GET",
            "/admin/appointments",
        )
        
        assert response["statusCode"] == 401

    def test_admin_list_appointments_user_forbidden(self, make_request, test_token):
        """Test that non-admin users can't list all appointments."""
        response = make_request(
            "GET",
            "/admin/appointments",
            auth_token=test_token,
        )
        
        assert response["statusCode"] == 403


class TestUpdateAppointment:
    """Tests for updating appointment status."""

    def test_update_appointment_accept(
        self, make_request, admin_token, seeded_user, seeded_service
    ):
        """Test accepting a pending appointment."""
        from lib.db import put_item
        import time
        
        appt_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat() + "Z"
        tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Create a pending appointment
        appointment = {
            "PK": f"APPT#{appt_id}",
            "SK": "DETAIL",
            "apptId": appt_id,
            "userId": seeded_user["userId"],
            "userEmail": seeded_user["email"],
            "userName": f"{seeded_user['firstName']} {seeded_user['lastName']}",
            "serviceId": seeded_service["serviceId"],
            "serviceName": seeded_service["name"],
            "date": tomorrow,
            "time": "10:00",
            "status": "pending",
            "GSI1PK": "STATUS#pending",
            "GSI1SK": f"DATE#{tomorrow}",
            "createdAt": now,
            "updatedAt": now,
        }
        put_item(appointment)
        
        # Accept it
        response = make_request(
            "PATCH",
            f"/admin/appointments/{appt_id}",
            body={"status": "accepted"},
            auth_token=admin_token,
        )
        
        assert response["statusCode"] == 200
        body = response["body"]
        assert "message" in body
        assert "accepted" in body["message"].lower()

    def test_update_appointment_decline(
        self, make_request, admin_token, seeded_user, seeded_service
    ):
        """Test declining a pending appointment."""
        from lib.db import put_item
        
        appt_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat() + "Z"
        tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        appointment = {
            "PK": f"APPT#{appt_id}",
            "SK": "DETAIL",
            "apptId": appt_id,
            "userId": seeded_user["userId"],
            "userEmail": seeded_user["email"],
            "userName": f"{seeded_user['firstName']} {seeded_user['lastName']}",
            "serviceId": seeded_service["serviceId"],
            "serviceName": seeded_service["name"],
            "date": tomorrow,
            "time": "11:00",
            "status": "pending",
            "GSI1PK": "STATUS#pending",
            "GSI1SK": f"DATE#{tomorrow}",
            "createdAt": now,
            "updatedAt": now,
        }
        put_item(appointment)
        
        response = make_request(
            "PATCH",
            f"/admin/appointments/{appt_id}",
            body={"status": "declined"},
            auth_token=admin_token,
        )
        
        assert response["statusCode"] == 200
        body = response["body"]
        assert "declined" in body["message"].lower()

    def test_update_appointment_forbidden_user(
        self, make_request, test_token, seeded_service
    ):
        """Test that non-admin can't update appointments."""
        response = make_request(
            "PATCH",
            f"/admin/appointments/{str(uuid.uuid4())}",
            body={"status": "accepted"},
            auth_token=test_token,
        )
        
        assert response["statusCode"] == 403


class TestAdminUsers:
    """Tests for listing users."""

    def test_admin_list_users(self, make_request, admin_token, seeded_user):
        """Test admin listing all users."""
        response = make_request(
            "GET",
            "/admin/users",
            auth_token=admin_token,
        )
        
        assert response["statusCode"] == 200
        body = response["body"]
        assert "users" in body
        assert "count" in body
        assert body["count"] >= 1


class TestAdminStats:
    """Tests for dashboard statistics."""

    def test_admin_get_stats(self, make_request, admin_token):
        """Test getting dashboard stats."""
        response = make_request(
            "GET",
            "/admin/stats",
            auth_token=admin_token,
        )
        
        assert response["statusCode"] == 200
        body = response["body"]
        assert "stats" in body
        stats = body["stats"]
        assert "pendingAppointments" in stats
        assert "acceptedThisWeek" in stats
        assert "todayAppointments" in stats
        assert "totalUsers" in stats


class TestAdminServices:
    """Tests for admin service management."""

    def test_admin_list_services(self, make_request, admin_token, seeded_service):
        """Test admin listing services."""
        response = make_request(
            "GET",
            "/admin/services",
            auth_token=admin_token,
        )
        
        assert response["statusCode"] == 200
        body = response["body"]
        assert "services" in body

    def test_admin_create_service(self, make_request, admin_token):
        """Test admin creating a service."""
        response = make_request(
            "POST",
            "/admin/services",
            body={
                "name": {
                    "en": "New Service",
                    "es": "Nuevo Servicio",
                },
                "description": {
                    "en": "A new service",
                    "es": "Un nuevo servicio",
                },
                "durationMinutes": 60,
            },
            auth_token=admin_token,
        )
        
        assert response["statusCode"] == 201
        body = response["body"]
        assert "service" in body

    def test_admin_create_service_missing_name(self, make_request, admin_token):
        """Test creating service without English name."""
        response = make_request(
            "POST",
            "/admin/services",
            body={
                "description": {"en": "A service"},
                "durationMinutes": 50,
            },
            auth_token=admin_token,
        )
        
        assert response["statusCode"] == 400

    def test_admin_update_service(self, make_request, admin_token, seeded_service):
        """Test admin updating a service."""
        response = make_request(
            "PATCH",
            f"/admin/services/{seeded_service['serviceId']}",
            body={
                "name": {
                    "en": "Updated Service",
                    "es": "Servicio Actualizado",
                },
            },
            auth_token=admin_token,
        )
        
        assert response["statusCode"] == 200
        body = response["body"]
        assert "service" in body

    def test_admin_delete_service(self, make_request, admin_token, seeded_service):
        """Test admin deleting (soft delete) a service."""
        response = make_request(
            "DELETE",
            f"/admin/services/{seeded_service['serviceId']}",
            auth_token=admin_token,
        )
        
        assert response["statusCode"] == 200
        body = response["body"]
        assert "message" in body


class TestAdminAvailability:
    """Tests for admin availability management."""

    def test_admin_get_availability(self, make_request, admin_token):
        """Test getting availability for a date."""
        tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        response = make_request(
            "GET",
            "/admin/availability",
            query={"date": tomorrow},
            auth_token=admin_token,
        )
        
        assert response["statusCode"] == 200
        body = response["body"]
        assert "date" in body
        assert "slots" in body

    def test_admin_create_availability(self, make_request, admin_token):
        """Test adding time slots."""
        tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        response = make_request(
            "POST",
            "/admin/availability",
            body={
                "date": tomorrow,
                "times": ["09:00", "10:00", "11:00"],
            },
            auth_token=admin_token,
        )
        
        assert response["statusCode"] == 201
        body = response["body"]
        assert "slots" in body
        assert body["count"] == 3

    def test_admin_delete_availability(self, make_request, admin_token):
        """Test removing a time slot."""
        tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # First, create a slot
        make_request(
            "POST",
            "/admin/availability",
            body={
                "date": tomorrow,
                "times": ["09:00"],
            },
            auth_token=admin_token,
        )
        
        # Then delete it
        response = make_request(
            "DELETE",
            f"/admin/availability/{tomorrow}_09:00",
            auth_token=admin_token,
        )
        
        assert response["statusCode"] == 200


class TestAdminConfig:
    """Tests for admin config management."""

    def test_admin_get_config(self, make_request, admin_token):
        """Test getting site config."""
        response = make_request(
            "GET",
            "/admin/config",
            auth_token=admin_token,
        )
        
        assert response["statusCode"] == 200
        body = response["body"]
        assert "config" in body

    def test_admin_update_config(self, make_request, admin_token):
        """Test updating site config."""
        response = make_request(
            "PATCH",
            "/admin/config",
            body={
                "theme": {
                    "primaryColor": "#ff0000",
                },
            },
            auth_token=admin_token,
        )
        
        assert response["statusCode"] == 200
        body = response["body"]
        assert "config" in body

