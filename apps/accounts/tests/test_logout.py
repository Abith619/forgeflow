import pytest
from django.conf import settings
from rest_framework import status

from apps.accounts.factories import UserFactory

pytestmark = pytest.mark.django_db


def login_for_logout(csrf_client, login_url, csrf_url):
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

    access = login_response.data["access"]

    csrf_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    csrf_client.get(csrf_url)
    csrf_token = csrf_client.cookies["csrftoken"].value

    return user, csrf_token


def test_logout_blacklists_refresh_and_clears_cookie(
    csrf_client,
    login_url,
    csrf_url,
    logout_url,
    refresh_url,
):
    _, csrf_token = login_for_logout(
        csrf_client,
        login_url,
        csrf_url,
    )

    cookie_name = settings.REFRESH_COOKIE_NAME
    old_refresh = csrf_client.cookies[cookie_name].value

    response = csrf_client.post(
        logout_url,
        {},
        format="json",
        headers={"X-CSRFToken": csrf_token},
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert cookie_name in response.cookies
    assert response.cookies[cookie_name]["max-age"] == 0

    # Simulate replay of the old token by a client that retained it.
    csrf_client.cookies[cookie_name] = old_refresh

    refresh_response = csrf_client.post(
        refresh_url,
        {},
        format="json",
        headers={"X-CSRFToken": csrf_token},
    )

    assert refresh_response.status_code == status.HTTP_401_UNAUTHORIZED


def test_logout_without_csrf_returns_403(
    csrf_client,
    login_url,
    csrf_url,
    logout_url,
):
    login_for_logout(
        csrf_client,
        login_url,
        csrf_url,
    )

    response = csrf_client.post(
        logout_url,
        {},
        format="json",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
