import pytest
from django.conf import settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

pytestmark = pytest.mark.django_db

User = get_user_model()


def test_register_sets_httponly_refresh_cookie():
    client = APIClient()

    response = client.post(
        reverse("register"),
        {
            "email": "register@example.com",
            "password": "A-Strong-Passphrase-927!",
            "full_name": "Test User",
            "company_name": "Test Company",
            "company_code": "TEST-COMPANY-001",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED

    # Access token is in the response body; refresh token is not.
    assert "access" in response.data
    assert "refresh" not in response.data

    # Refresh token is set in an HttpOnly cookie.
    cookie_name = settings.REFRESH_COOKIE_NAME
    assert cookie_name in response.cookies
    assert response.cookies[cookie_name]["httponly"]


def test_register_rejects_weak_password():
    client = APIClient()

    response = client.post(
        reverse("register"),
        {
            "email": "weak-password@example.com",
            "password": "123",
            "full_name": "Test User",
            "company_name": "Weak Password Company",
            "company_code": "WEAK-PASSWORD-001",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "password" in response.data


def test_register_assigns_admin_role(api_client):
    payload = {
        "email": "new-owner@example.com",
        "password": "A-Strong-Passphrase-927!",
        "full_name": "Company Owner",
        "company_name": "New Company",
        "company_code": "NEW-COMPANY-001",
    }

    response = api_client.post(
        reverse("register"),
        payload,
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED

    user = User.objects.get(email=payload["email"])

    assert user.role == User.Role.ADMIN
    assert response.data["user"]["role"] == User.Role.ADMIN
