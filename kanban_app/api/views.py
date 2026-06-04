from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.models import User


from auth_app.api.serializers import UserShortProfileSerializer


class EmailCheckView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        email = request.query_params.get("email")
        if not email:
            return self._missing_email_response()

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return self._email_not_found_response()

        serializer = UserShortProfileSerializer(user.profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def _missing_email_response(self):
        return Response(
            {"detail": "Ungültige Anfrage. Die E-Mail-Adresse fehlt oder hat ein falsches Format."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def _email_not_found_response(self):
        return Response(
            {"detail": "Email nicht gefunden. Die Email existiert nicht."},
            status=status.HTTP_404_NOT_FOUND,
        )
