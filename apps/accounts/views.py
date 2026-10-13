from django.conf import settings
from django.contrib.auth import authenticate
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .cookies import (
    clear_refresh_cookie,
    enforce_csrf,
    set_refresh_cookie,
)
from .serializers import (
    LoginSerializer,
    MeSerializer,
    RegisterSerializer,
)


class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        response = Response(
            {
                "access": str(access),
                "user": MeSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )

        set_refresh_cookie(response, refresh)

        return response


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(MeSerializer(request.user).data)


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        user = authenticate(
            request,
            email=email,
            password=password,
        )

        # Keep failures generic to prevent user enumeration.
        if user is None or not user.is_active:
            return Response(
                {"detail": "Invalid email or password"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        response = Response(
            {
                "access": str(access),
                "user": MeSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )

        set_refresh_cookie(response, refresh)

        return response


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # 1. Explicit CSRF validation first.
        enforce_csrf(request._request)

        # 2. Read refresh token from the cookie.
        refresh_token = request.COOKIES.get(settings.REFRESH_COOKIE_NAME)

        # 3. Logout is idempotent if the cookie is missing.
        if not refresh_token:
            response = Response(status=status.HTTP_204_NO_CONTENT)
            clear_refresh_cookie(response)
            return response

        # 4. Validate token and verify ownership.
        try:
            token = RefreshToken(refresh_token)
        except TokenError:
            response = Response(
                {"detail": "Invalid refresh token"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
            clear_refresh_cookie(response)
            return response

        token_user_id = token.get("user_id")

        if str(token_user_id) != str(request.user.pk):
            raise PermissionDenied(
                "Refresh token does not belong to the authenticated user."
            )

        # 5. Blacklist the refresh token.
        token.blacklist()

        # 6. Clear cookie and return 204.
        response = Response(status=status.HTTP_204_NO_CONTENT)
        clear_refresh_cookie(response)
        return response


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response(
            {"detail": "CSRF cookie set"},
            status=status.HTTP_200_OK,
        )


class RefreshView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        # 1. CSRF must be checked before reading the refresh token.
        enforce_csrf(request._request)

        # 2. Read the refresh token from the HttpOnly cookie.
        refresh_token = request.COOKIES.get(settings.REFRESH_COOKIE_NAME)

        if not refresh_token:
            return Response(
                {"detail": "Refresh token missing"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # 3. Validate and rotate using SimpleJWT.
        serializer = TokenRefreshSerializer(data={"refresh": refresh_token})

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError:
            response = Response(
                {"detail": "Invalid or expired refresh token"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
            clear_refresh_cookie(response)
            return response

        # 4. Return only the access token in the response body.
        data = serializer.validated_data
        response = Response(
            {"access": data["access"]},
            status=status.HTTP_200_OK,
        )

        # 5. Store the rotated refresh token in the cookie.
        set_refresh_cookie(response, data["refresh"])

        return response
