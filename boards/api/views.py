from django.db.models import Q
from django.http import Http404
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.models import UserProfile, User
from auth_app.api.serializers import UserShortProfileSerializer
from .permission import BoardPermission
from ..models import Board
from .serializers import (
    BoardDetailSerializer,
    BoardCreateSerializer,
    BoardPatchSerializer,
    BoardsSerializer,
    BoardUpdateResponseSerializer
)


class BoardViewSet(viewsets.ModelViewSet):
    """
    Verwaltet CRUD-Operationen für Boards.

    - Listet alle Boards auf, bei denen der Benutzer Eigentümer oder Mitglied ist.
    - Erstellt neue Boards.
    - Zeigt Board-Details an.
    - Aktualisiert bestehende Boards.
    - Löscht Boards.
    """
    permission_classes = [IsAuthenticated, BoardPermission]
    serializer_class = BoardsSerializer

    def get_queryset(self):
        """
        Liefert die für den Benutzer sichtbaren Boards.

        Bei der Listenansicht werden nur Boards zurückgegeben, bei denen der Benutzer Eigentümer oder Mitglied ist.

        Für Detailansichten wird das vollständige QuerySet verwendet, damit zwischen 403 und 404 unterschieden werden kann.
        """
        if self.action == "list":
            return Board.objects.filter(
                Q(owner_id=self.request.user.id)
                | Q(member__user=self.request.user)
            ).distinct()
        
        return Board.objects.all()
    
    def get_object(self):
        """
        Liefert ein einzelnes Board anhand der URL-ID.

        Wandelt das Standard-404 von Django in eine spezifische Fehlermeldung um.
        """
        try:
            return super().get_object()
        except Http404:
            raise NotFound({
                "detail": "Board nicht gefunden. Die angegebene Board-ID existiert nicht."
            })

    def get_serializer_class(self):
        """
        Wählt abhängig von der Aktion den passenden Serializer aus.
        """
        if self.action == "create":
            return BoardCreateSerializer

        if self.action == "retrieve":
            return BoardDetailSerializer

        if self.action == "partial_update":
            return BoardPatchSerializer

        return BoardsSerializer

    def create(self, request):
        """
        Erstellt ein neues Board und gibt die Board-Daten inklusive Erfolgsmeldung zurück.
        """
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return self._invalid_board_data_response()

        board = serializer.save()
        return self._board_created_response(board)

    def partial_update(self, request, *args, **kwargs):
        """
        Aktualisiert einzelne Felder eines bestehenden Boards.
        """
        board = self.get_object()
        serializer = self.get_serializer(board, data=request.data, partial=True)
        if not serializer.is_valid():
            return self._invalid_board_data_response()

        board = serializer.save()
        response_serializer = BoardUpdateResponseSerializer(board)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def _get_board_or_error(self, pk):
        try:
            return Board.objects.get(pk=pk), None
        except Board.DoesNotExist:
            return None, Response(
                {"detail": "Board nicht gefunden. Die angegebene Board-ID existiert nicht."},
                status=status.HTTP_404_NOT_FOUND,
            )

    def _get_profiles(self, member_ids):
        profiles = UserProfile.objects.filter(user_id__in=member_ids)
        if profiles.count() != len(member_ids):
            raise ValueError

        return profiles
    
    def _update_members(self, board, member_ids):
        if member_ids is None:
            return

        profiles = self._get_profiles(member_ids)
        board.member.set(profiles)

    def _invalid_board_data_response(self):
        """
        Gibt eine standardisierte 400-Fehlermeldung für ungültige Board-Daten zurück.
        """
        return Response(
            {"detail": "Ungültige Anfragedaten. Möglicherweise sind einige Benutzer-Email-Adressen ungültig."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def _board_created_response(self, board):
        """
        Erstellt den Response für erfolgreich angelegte Boards.
        """
        serializer = BoardsSerializer(board)
        data = serializer.data
        data["detail"] = "Das Board wurde erfolgreich erstellt"
        return Response(data, status=status.HTTP_201_CREATED)
    
class EmailCheckView(APIView):
    """
    Prüft, ob ein Benutzer mit der angegebenen E-Mail-Adresse existiert und liefert dessen Profildaten zurück.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Sucht einen Benutzer anhand der übergebenen E-Mail-Adresse.
        """
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
        """
        Gibt eine 400-Fehlermeldung zurück, wenn keine E-Mail-Adresse übergeben wurde.
        """
        return Response(
            {"detail": "Ungültige Anfrage. Die E-Mail-Adresse fehlt oder hat ein falsches Format."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def _email_not_found_response(self):
        """
        Gibt eine 404-Fehlermeldung zurück, wenn kein Benutzer mit der angegebenen E-Mail-Adresse existiert.
        """
        return Response(
            {"detail": "Email nicht gefunden. Die Email existiert nicht."},
            status=status.HTTP_404_NOT_FOUND,
        )