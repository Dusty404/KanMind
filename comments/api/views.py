from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Comment
from tasks.models import Task

from .permission import CommentPermission
from .serializers import CommentsSerializer


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