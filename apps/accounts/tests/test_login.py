import pytest
from django.conf import settings
from django.urls import reverse
from rest_framework import status

from apps.accounts.factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def login_url():
    return reverse("login")


def test_login_successful(api_client, login_url):
    user = UserFactory(password="TestPassword123!")

    response = api_client.post(
        login_url,
        {
            "email": user.email,
            "password": "TestPassword123!",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK

    # Access token is in the body; refresh token is not.
    assert "access" in response.data
    assert "refresh" not in response.data
    assert "user" in response.data

    # Refresh token is stored in the cookie.
    cookie_name = settings.REFRESH_COOKIE_NAME
    assert cookie_name in response.cookies

    cookie = response.cookies[cookie_name]
    assert cookie["httponly"]
    assert cookie["path"] == settings.REFRESH_COOKIE_PATH


def test_login_wrong_password_returns_401_without_cookie(
    api_client,
    login_url,
):
    user = UserFactory(password="TestPassword123!")

    response = api_client.post(
        login_url,
        {
            "email": user.email,
            "password": "WrongPassword123!",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data["detail"] == "Invalid email or password"
    assert settings.REFRESH_COOKIE_NAME not in response.cookies


def test_login_unknown_email_returns_same_error(
    api_client,
    login_url,
):
    response = api_client.post(
        login_url,
        {
            "email": "unknown@example.com",
            "password": "TestPassword123!",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data["detail"] == "Invalid email or password"
    assert settings.REFRESH_COOKIE_NAME not in response.cookies


def test_login_inactive_user_returns_401(
    api_client,
    login_url,
):
    user = UserFactory(
        password="TestPassword123!",
        is_active=False,
    )

    response = api_client.post(
        login_url,
        {
            "email": user.email,
            "password": "TestPassword123!",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data["detail"] == "Invalid email or password"
    assert settings.REFRESH_COOKIE_NAME not in response.cookies
