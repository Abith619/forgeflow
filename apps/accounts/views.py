from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import LogoutSerializer, MeSerializer, RegisterSerializer


class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        return Response(
            {
                "user": MeSerializer(user).data,
                "access": str(access),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )



class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            MeSerializer(request.user).data
        )

class LogoutView(APIView):

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token = serializer.validated_data["refresh"]

        try:
            refresh = RefreshToken(refresh_token)
        except TokenError:
            return Response(
                {"refresh": "Invalid or expired refresh token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token_user_id = refresh.get("user_id")

        if str(token_user_id) != str(request.user.id):
            return Response(
                {"refresh": "Refresh token does not belong to this user."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            refresh.blacklist()
        except AttributeError:
            return Response(
                {"refresh": "Token blacklist is not enabled."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(status=status.HTTP_205_RESET_CONTENT)

