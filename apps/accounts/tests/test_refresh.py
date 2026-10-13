import pytest
from django.conf import settings
from rest_framework import status

from apps.accounts.factories import UserFactory

pytestmark = pytest.mark.django_db


def login_and_get_csrf(csrf_client, login_url, csrf_url):
    user = UserFactory(password="TestPassword123!")

    login_response = csrf_client.post(
        login_url,
        {
            "email": user.email,
            "password": "TestPassword123!",
        },
        format="json",
    )

    assert login_response.status_code == status.HTTP_200_OK

    csrf_response = csrf_client.get(csrf_url)
    assert csrf_response.status_code == status.HTTP_200_OK
    assert "csrftoken" in csrf_client.cookies

    csrf_token = csrf_client.cookies["csrftoken"].value

    return user, csrf_token


def post_refresh(csrf_client, refresh_url, csrf_token):
    return csrf_client.post(
        refresh_url,
        {},
        format="json",
        headers={"X-CSRFToken": csrf_token},
    )


def test_refresh_rotates_cookie_and_returns_access_only(
    csrf_client,
    login_url,
    csrf_url,
    refresh_url,
):
    login_and_get_csrf(csrf_client, login_url, csrf_url)

    cookie_name = settings.REFRESH_COOKIE_NAME
    old_refresh = csrf_client.cookies[cookie_name].value
    csrf_token = csrf_client.cookies["csrftoken"].value

    response = post_refresh(
        csrf_client,
        refresh_url,
        csrf_token,
    )

    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data
    assert "refresh" not in response.data

    new_refresh = response.cookies[cookie_name].value

    assert new_refresh != old_refresh
    assert response.cookies[cookie_name]["httponly"]
    assert response.cookies[cookie_name]["path"] == (settings.REFRESH_COOKIE_PATH)


def test_refresh_without_csrf_header_returns_403(
    csrf_client,
    login_url,
    csrf_url,
    refresh_url,
):
    login_and_get_csrf(csrf_client, login_url, csrf_url)

    response = csrf_client.post(
        refresh_url,
        {},
        format="json",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "CSRF token missing" in response.data["detail"]


def test_refresh_without_cookie_returns_401(
    csrf_client,
    login_url,
    csrf_url,
    refresh_url,
):
    login_and_get_csrf(csrf_client, login_url, csrf_url)

    csrf_token = csrf_client.cookies["csrftoken"].value

    # Remove the refresh cookie while retaining the CSRF cookie.
    csrf_client.cookies.pop(settings.REFRESH_COOKIE_NAME, None)

    response = post_refresh(
        csrf_client,
        refresh_url,
        csrf_token,
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data["detail"] == "Refresh token missing"


def test_refresh_rejects_reused_old_token(
    csrf_client,
    login_url,
    csrf_url,
    refresh_url,
):
    login_and_get_csrf(csrf_client, login_url, csrf_url)

    cookie_name = settings.REFRESH_COOKIE_NAME
    old_refresh = csrf_client.cookies[cookie_name].value
    csrf_token = csrf_client.cookies["csrftoken"].value

    # First use: rotate the token and blacklist the old one.
    first_response = post_refresh(
        csrf_client,
        refresh_url,
        csrf_token,
    )

    assert first_response.status_code == status.HTTP_200_OK

    # Simulate a client replaying the stolen, old token.
    csrf_client.cookies[cookie_name] = old_refresh

    second_response = post_refresh(
        csrf_client,
        refresh_url,
        csrf_token,
    )

    assert second_response.status_code == status.HTTP_401_UNAUTHORIZED
    assert cookie_name in second_response.cookies
    assert second_response.cookies[cookie_name]["max-age"] == 0


def test_refresh_with_garbage_cookie_returns_401_and_clears_cookie(
    csrf_client,
    login_url,
    csrf_url,
    refresh_url,
):
    login_and_get_csrf(csrf_client, login_url, csrf_url)

    cookie_name = settings.REFRESH_COOKIE_NAME
    csrf_token = csrf_client.cookies["csrftoken"].value

    csrf_client.cookies[cookie_name] = "not-a-valid-jwt"

    response = post_refresh(
        csrf_client,
        refresh_url,
        csrf_token,
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert cookie_name in response.cookies
    assert response.cookies[cookie_name]["max-age"] == 0
