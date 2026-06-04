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
    """
    Verwaltet Kommentare zu einer bestimmten Task.

    Ermöglicht das Auflisten, Erstellen und Löschen von Kommentaren.
    Der Zugriff wird über die zugehörige Task und die CommentPermission geprüft.
    """
    permission_classes = [IsAuthenticated, CommentPermission]

    def get(self, request, task_id):
        """
        Gibt alle Kommentare einer Task zurück.

        Die Kommentare werden absteigend nach Erstellungsdatum sortiert.
        """
        task = self._get_task_or_error()
        self.check_object_permissions(request, task)
        serializer = CommentsSerializer(task.comments.order_by("-created_at"), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, task_id):
        """
        Erstellt einen neuen Kommentar für die angegebene Task.

        Der angemeldete Benutzer wird automatisch als Eigentümer des Kommentars gespeichert.
        """
        task = self._get_task_or_error()
        self.check_object_permissions(request, task)
        if not request.data.get("content", "").strip():
            return self._empty_content_response()
        serializer = CommentsSerializer(data=request.data)        
        serializer.is_valid(raise_exception=True)
        comment = serializer.save(task=task, owner=request.user)
        return Response(CommentsSerializer(comment).data, status=status.HTTP_201_CREATED)

    def delete(self, request, task_id, comment_id):
        """
        Löscht einen Kommentar einer Task.

        Nur der Ersteller des Kommentars darf diesen löschen.
        """
        task = self._get_task_or_error()
        comment = self._get_comment_or_error(task, comment_id)
        self.check_object_permissions(request, comment)
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _empty_content_response(self):
        """
        Gibt eine 400-Fehlermeldung zurück, wenn der Kommentarinhalt leer ist.
        """
        return Response(
            {"detail": "Ungültige Anfragedaten. Möglicherweise ist der `content`-Wert leer."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    
    def _get_task_or_error(self):
        """
        Liefert die Task aus der URL oder wirft eine projektbezogene 404-Meldung.
        """
        self._validate_task_pk()

        try:
            return Task.objects.get(pk=self.kwargs["task_id"])
        except Task.DoesNotExist:
            raise NotFound({
                "detail": "Task nicht gefunden. Die angegebene Task-ID existiert nicht."
            })

    def _get_comment_or_error(self, task, comment_id):
        """
        Liefert einen Kommentar der angegebenen Task oder wirft eine 404-Meldung.
        """
        try:
            return task.comments.get(pk=comment_id)
        except Comment.DoesNotExist:
            raise NotFound({
            "detail": "Kommentar oder Task nicht gefunden."
        })
                
    def _validate_task_pk(self):
        """
        Prüft, ob die übergebene Task-ID ein gültiges Zahlenformat hat.
        """
        if not str(self.kwargs["task_id"]).isdigit():
            raise ValidationError({
                "detail": "Ungültige Anfragedaten. Die übermittelte Task-ID ist fehlerhaft."
            })