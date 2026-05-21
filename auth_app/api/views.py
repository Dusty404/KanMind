from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegistrationSerializer, CustomLoginSerializer
from rest_framework import status
from .serializers import RegistrationSerializer, CustomLoginSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token


class RegistrationView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            saved_account = serializer.save()
            token, created = Token.objects.get_or_create(user=saved_account)
            return Response({
                "token": token.key,
                "fullname": saved_account.profile.fullname,
                "email": saved_account.email,
                "user_id": saved_account.id

            }, status=status.HTTP_201_CREATED)        
        return Response({"Ungültige Anfragedaten"}, status=status.HTTP_400_BAD_REQUEST)
    

class CustomLoginView(ObtainAuthToken):
    permission_classes = [AllowAny]
    serializer_class = CustomLoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                "token": token.key,
                "fullname": user.profile.fullname,
                "email": user.email,
                "user_id": user.id
            }, status=status.HTTP_200_OK)
        return Response({"Ungültige Anfragedaten"}, status=status.HTTP_400_BAD_REQUEST)
    
    
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        return Response(
            {"detail": "Logout erfolgreich."},
            status=status.HTTP_200_OK
        )