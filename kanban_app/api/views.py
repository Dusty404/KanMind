from django.db.models import Q
from django.http import Http404
from rest_framework import generics, status, viewsets
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from kanban_app.models import Board, Comment, Task, User, UserProfile

from .permission import BoardPermission, CommentPermission, TaskPermission
from .serializers import (
    BoardDetailSerializer,
    BoardPatchSerializer,
    BoardsSerializer,
    BoardUpdateResponseSerializer,
    CommentsSerializer,
    TaskSerializer,
    UserShortProfileSerializer,
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


class TasksViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, TaskPermission]
    serializer_class = TaskSerializer
    queryset = Task.objects.all()

    def get_object(self):
        self._validate_task_pk()
        try:
            return super().get_object()
        except Http404:
            raise NotFound({
                "detail": "Task nicht gefunden. Die angegebene Task-ID existiert nicht."
            })

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return self._invalid_task_response(serializer)

        board = serializer.validated_data["board"]
        if not self._can_create_task(request, board):
            return self._task_create_forbidden_response()

        task = serializer.save(owner=request.user)
        self._add_profiles_to_board(task)
        response_serializer = self.get_serializer(task)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        task = self.get_object()
        serializer = self._get_partial_update_serializer(task, request)

        if not serializer.is_valid():
            return self._invalid_task_data_response()

        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, pk=None):
        task = self.get_object()
        self.check_object_permissions(request, task)
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _validate_task_pk(self):
        pk = self.kwargs.get("pk")
        if not str(pk).isdigit():
            raise ValidationError({
                "detail": "Ungültige Anfragedaten. Die übermittelte Task-ID ist fehlerhaft."
            })

    def _invalid_task_response(self, serializer):
        if "board" in serializer.errors:
            return Response(
                {"detail": "Board nicht gefunden. Die angegebene Board-ID existiert nicht."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return self._invalid_task_data_response()

    def _invalid_task_data_response(self):
        return Response(
            {"detail": "Ungültige Anfragedaten. Möglicherweise fehlen erforderliche Felder oder enthalten ungültige Werte."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def _can_create_task(self, request, board):
        return (
            board.owner_id == request.user.id
            or board.member.filter(user=request.user).exists()
        )

    def _task_create_forbidden_response(self):
        return Response(
            {"detail": "Verboten. Der Benutzer muss Mitglied des Boards sein, um eine Task zu erstellen."},
            status=status.HTTP_403_FORBIDDEN,
        )

    def _add_profiles_to_board(self, task):
        profiles_to_add = self._get_profiles_to_add(task)
        if profiles_to_add:
            task.board.member.add(*profiles_to_add)

    def _get_profiles_to_add(self, task):
        profiles_to_add = []
        if task.assignee:
            profiles_to_add.append(task.assignee.profile)

        if task.reviewer:
            profiles_to_add.append(task.reviewer.profile)

        return profiles_to_add

    def _get_partial_update_serializer(self, task, request):
        return TaskSerializer(
            task,
            data=request.data,
            partial=True,
            exclude_fields=["board", "comments_count", "assignee", "reviewer"],
        )


class TasksAssignedToUserView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TaskSerializer

    def get_queryset(self):
        return Task.objects.filter(assignee=self.request.user)


class ReviewingView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TaskSerializer

    def get_queryset(self):
        return Task.objects.filter(reviewer=self.request.user)


class CommentsView(APIView):
    permission_classes = [IsAuthenticated, CommentPermission]

    def get_task(self, task_id, request):
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return None, self._task_not_found_response()

        if self._can_access_task(request, task):
            return task, None

        return None, self._task_access_forbidden_response()

    def get(self, request, task_id):
        task, error_response = self.get_task(task_id, request)
        if error_response:
            return error_response

        comments = task.comments.all().order_by("-created_at")
        serializer = CommentsSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, task_id):
        task, error_response = self.get_task(task_id, request)
        if error_response:
            return error_response

        if not request.data.get("content", "").strip():
            return self._empty_content_response()

        serializer = CommentsSerializer(data=request.data)
        if serializer.is_valid():
            return self._create_comment_response(serializer, task, request)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, task_id, comment_id):
        task, error_response = self.get_task(task_id, request)
        if error_response:
            return error_response

        comment, error_response = self._get_comment_or_error(task, comment_id)
        if error_response:
            return error_response

        self.check_object_permissions(request, comment)
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _can_access_task(self, request, task):
        return (
            task.owner_id == request.user.id
            or task.board.owner_id == request.user.id
            or task.board.member.filter(user=request.user).exists()
        )

    def _task_not_found_response(self):
        return Response(
            {"detail": "Task nicht gefunden. Die angegebene Task-ID existiert nicht."},
            status=status.HTTP_404_NOT_FOUND,
        )

    def _task_access_forbidden_response(self):
        return Response(
            {"detail": "Verboten. Der Benutzer muss Mitglied des Boards sein, zu dem die Task gehört."},
            status=status.HTTP_403_FORBIDDEN,
        )

    def _empty_content_response(self):
        return Response(
            {"detail": "Ungültige Anfragedaten. Möglicherweise ist der `content`-Wert leer."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def _create_comment_response(self, serializer, task, request):
        comment = serializer.save(task=task, owner=request.user)
        response_serializer = CommentsSerializer(comment)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def _get_comment_or_error(self, task, comment_id):
        try:
            return task.comments.get(pk=comment_id), None
        except Comment.DoesNotExist:
            return None, Response(
                {"detail": "Kommentar oder Task nicht gefunden."},
                status=status.HTTP_404_NOT_FOUND,
            )


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
