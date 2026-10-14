import pytest
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def csrf_client():
    return APIClient(enforce_csrf_checks=True)

@pytest.fixture
def login_url():
    return reverse("login")

@pytest.fixture
def csrf_url():
    return reverse("csrf")

@pytest.fixture
def refresh_url():
    return reverse("refresh")

@pytest.fixture
def logout_url():
    return reverse("logout")
