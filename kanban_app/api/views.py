from django.db.models import Q
from django.http import Http404
from rest_framework import generics, status, viewsets
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from kanban_app.models import Comment, Task, User

from .permission import CommentPermission, TaskPermission
from .serializers import (
    CommentsSerializer,
    TaskSerializer,
)

from auth_app.api.serializers import UserShortProfileSerializer


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
            exclude_fields=["board", "comments_count"],
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

    def check_task_permission(self, task, request):        
        if self._can_access_task(request, task):
                return task, None

        return None, self._task_access_forbidden_response()

    def get(self, request, task_id):
        task = self._get_task_or_error()
        self.check_object_permissions(request, task)

        comments = task.comments.all().order_by("-created_at")
        serializer = CommentsSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, task_id):
        task = self._get_task_or_error()

        if not request.data.get("content", "").strip():
            return self._empty_content_response()

        self.check_object_permissions(request, task)

        serializer = CommentsSerializer(data=request.data)
        if serializer.is_valid():
            return self._create_comment_response(serializer, task, request)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, task_id, comment_id):
        task = self._get_task_or_error()
        comment = self._get_comment_or_error(task, comment_id)

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
    
    def _get_task_or_error(self):
        self._validate_task_pk()
        task_id = self.kwargs.get("task_id")

        try:
            return Task.objects.get(pk=task_id)
        except Task.DoesNotExist:
            raise NotFound({
                "detail": "Task nicht gefunden. Die angegebene Task-ID existiert nicht."
            })

    def _get_comment_or_error(self, task, comment_id):
        try:
            return task.comments.get(pk=comment_id)
        except Comment.DoesNotExist:
            raise NotFound({
            "detail": "Kommentar oder Task nicht gefunden."
        })
                
        
    def _validate_task_pk(self):
        task_id = self.kwargs.get("task_id")

        if not str(task_id).isdigit():
            raise ValidationError({
                "detail": "Ungültige Anfragedaten. Die übermittelte Task-ID ist fehlerhaft."
            })


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
