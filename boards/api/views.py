from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.models import UserProfile, User
from auth_app.api.serializers import UserShortProfileSerializer
from .permission import BoardPermission
from ..models import Board
from .serializers import (
    BoardDetailSerializer,
    BoardPatchSerializer,
    BoardsSerializer,
    BoardUpdateResponseSerializer,
)


class BoardViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, BoardPermission]
    serializer_class = BoardsSerializer

    def get_queryset(self):
        return Board.objects.filter(
            Q(owner_id=self.request.user.id)
            | Q(member__user=self.request.user)
        ).distinct()

    def list(self, request):
        boards = self.get_queryset()
        serializer = BoardsSerializer(boards, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        board, error_response = self._get_board_or_error(pk)
        if error_response:
            return error_response

        self.check_object_permissions(request, board)
        serializer = BoardDetailSerializer(board)
        return Response(serializer.data)

    def create(self, request):
        serializer = BoardsSerializer(data=request.data)
        if not serializer.is_valid():
            return self._invalid_board_data_response()

        member_ids = request.data.get("members", [])
        profiles, error_response = self._get_profiles_or_error(member_ids)
        if error_response:
            return error_response

        board = serializer.save(owner=request.user)
        board.member.set(profiles)
        return self._board_created_response(board)

    def partial_update(self, request, pk=None):
        board, error_response = self._get_board_or_error(pk)
        if error_response:
            return error_response

        serializer = BoardPatchSerializer(board, data=request.data, partial=True)
        if not serializer.is_valid():
            return self._invalid_board_data_response()

        return self._update_board(request, board, serializer)

    def destroy(self, request, pk=None):
        board, error_response = self._get_board_or_error(pk)
        if error_response:
            return error_response

        self.check_object_permissions(request, board)
        board.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _get_board_or_error(self, pk):
        try:
            return Board.objects.get(pk=pk), None
        except Board.DoesNotExist:
            return None, Response(
                {"detail": "Board nicht gefunden. Die angegebene Board-ID existiert nicht."},
                status=status.HTTP_404_NOT_FOUND,
            )

    def _get_profiles_or_error(self, member_ids):
        profiles = UserProfile.objects.filter(user_id__in=member_ids)
        if profiles.count() == len(member_ids):
            return profiles, None

        return None, self._invalid_board_data_response()

    def _invalid_board_data_response(self):
        return Response(
            {"detail": "Ungültige Anfragedaten. Möglicherweise sind einige Benutzer-Email-Adressen ungültig."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def _board_created_response(self, board):
        response_serializer = BoardsSerializer(board)
        data = response_serializer.data
        data["detail"] = "Das Board wurde erfolgreich erstellt"
        return Response(data, status=status.HTTP_201_CREATED)

    def _update_board(self, request, board, serializer):
        self.check_object_permissions(request, board)
        member_ids = request.data.get("members", None)
        profiles, error_response = self._get_update_profiles(member_ids)
        if error_response:
            return error_response

        board = serializer.save()
        if member_ids is not None:
            board.member.set(profiles)

        response_serializer = BoardUpdateResponseSerializer(board)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def _get_update_profiles(self, member_ids):
        if member_ids is None:
            return None, None

        return self._get_profiles_or_error(member_ids)
    
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