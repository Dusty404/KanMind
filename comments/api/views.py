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

    def get(self, request, task_id):
        task = self._get_task_or_error()
        self.check_object_permissions(request, task)
        serializer = CommentsSerializer(task.comments.order_by("-created_at"), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, task_id):
        task = self._get_task_or_error()
        self.check_object_permissions(request, task)
        serializer = CommentsSerializer(data=request.data, context={"request": request, "task": task})        
        serializer.is_valid(raise_exception=True)
        comment = serializer.save(task=task, owner=request.user)
        return Response(CommentsSerializer(comment).data, status=status.HTTP_201_CREATED)

    def delete(self, request, task_id, comment_id):
        task = self._get_task_or_error()
        comment = self._get_comment_or_error(task, comment_id)
        self.check_object_permissions(request, comment)
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

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

        try:
            return Task.objects.get(pk=self.kwargs["task_id"])
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
        if not str(self.kwargs["task_id"]).isdigit():
            raise ValidationError({
                "detail": "Ungültige Anfragedaten. Die übermittelte Task-ID ist fehlerhaft."
            })