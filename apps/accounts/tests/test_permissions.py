import pytest
from rest_framework.test import APIRequestFactory

from apps.accounts.models import User
from apps.accounts.permissions import HasRole

pytestmark = pytest.mark.django_db


def test_has_role_denies_when_view_has_no_allowed_roles(user):
    user.role = User.Role.ADMIN

    request = APIRequestFactory().get("/")
    request.user = user

    class View:
        pass

    view = View()

    assert HasRole().has_permission(request, view) is False
