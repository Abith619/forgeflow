from django.conf import settings
from rest_framework.authentication import CSRFCheck
from rest_framework.exceptions import PermissionDenied


def set_refresh_cookie(response, refresh_token):
    max_age = int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds())

    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=str(refresh_token),
        max_age=max_age,
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite="Lax",
        path=settings.REFRESH_COOKIE_PATH,
    )


def clear_refresh_cookie(response):
    response.delete_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        path=settings.REFRESH_COOKIE_PATH,
        samesite="Lax",
    )


def enforce_csrf(request):
    """
    Explicitly enforce Django CSRF validation for a DRF request.
    """

    def dummy_get_response(request):
        return None

    check = CSRFCheck(dummy_get_response)
    check.process_request(request)
    reason = check.process_view(request, lambda request: None, (), {})

    if reason:
        raise PermissionDenied(f"CSRF Failed: {reason}")
