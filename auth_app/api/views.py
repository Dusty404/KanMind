from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import CustomLoginSerializer, RegistrationSerializer


class RegistrationView(APIView):
    permission_classes = [AllowAny]
    serializer_class = RegistrationSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                self.get_auth_response_data(user),
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"Ungültige Anfragedaten"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def get_auth_response_data(self, user):
        token, created = Token.objects.get_or_create(user=user)
        return {
            "token": token.key,
            "fullname": user.profile.fullname,
            "email": user.email,
            "user_id": user.id,
        }


class CustomLoginView(ObtainAuthToken):
    permission_classes = [AllowAny]
    serializer_class = CustomLoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            return Response(
                self.get_auth_response_data(user),
                status=status.HTTP_200_OK,
            )
        return Response(
            {"Ungültige Anfragedaten"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def get_auth_response_data(self, user):
        token, created = Token.objects.get_or_create(user=user)
        return {
            "token": token.key,
            "fullname": user.profile.fullname,
            "email": user.email,
            "user_id": user.id,
        }


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        return Response(
            {"detail": "Logout erfolgreich."},
            status=status.HTTP_200_OK,
        )
