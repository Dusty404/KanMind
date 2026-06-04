from django.http import Http404
from rest_framework import generics, status, viewsets
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Task

from .permission import TaskPermission
from .serializers import TaskSerializer, TaskPatchSerializer


class TasksViewSet(viewsets.ModelViewSet):
    """
    Verwaltet CRUD-Operationen für Tasks.

    Ermöglicht das Erstellen, Anzeigen, Aktualisieren und Löschen von Tasks unter Berücksichtigung der definierten Berechtigungen.
    """
    permission_classes = [IsAuthenticated, TaskPermission]
    serializer_class = TaskSerializer
    queryset = Task.objects.all()

    def get_serializer_class(self):
        """
        Wählt abhängig von der aktuellen Aktion den passenden Serializer aus.
        """
        if self.action == "partial_update":
            return TaskPatchSerializer

        return TaskSerializer

    def get_object(self):
        """
        Liefert die angeforderte Task anhand der URL-ID.

        Wandelt das Standard-404 von Django in die projektspezifische Fehlermeldung um.
        """
        self._validate_task_pk()
        try:
            return super().get_object()
        except Http404:
            raise NotFound({
                "detail": "Task nicht gefunden. Die angegebene Task-ID existiert nicht."
            })

    def create(self, request, *args, **kwargs):
        """
        Erstellt eine neue Task und gibt die erzeugte Task als API-Antwort zurück.
        """
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return self._invalid_task_response(serializer)

        task = serializer.save()
        response_serializer = TaskSerializer(task)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        """
        Aktualisiert einzelne Felder einer bestehenden Task.
        """
        task = self.get_object()
        serializer = self.get_serializer(task, data=request.data, partial=True)

        if not serializer.is_valid():
            return self._invalid_task_data_response()

        task = serializer.save()
        response_serializer = TaskSerializer(task)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def _validate_task_pk(self):
        """
        Prüft, ob die übergebene Task-ID ein gültiges Zahlenformat besitzt.
        """
        pk = self.kwargs.get("pk")
        if not str(pk).isdigit():
            raise ValidationError({
                "detail": "Ungültige Anfragedaten. Die übermittelte Task-ID ist fehlerhaft."
            })

    def _invalid_task_response(self, serializer):
        """
        Erstellt die passende Fehlerantwort für Validierungsfehler beim Erstellen einer Task.
        """
        if "board" in serializer.errors:
            return Response(
                {"detail": "Board nicht gefunden. Die angegebene Board-ID existiert nicht."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        if "permission" in serializer.errors:
            return Response(
                {"detail": "Verboten. Der Benutzer muss Mitglied des Boards sein, um eine Task zu erstellen."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return self._invalid_task_data_response()

    def _invalid_task_data_response(self):
        """
        Gibt eine standardisierte 400-Fehlermeldung für ungültige Task-Daten zurück.
        """
        return Response(
            {"detail": "Ungültige Anfragedaten. Möglicherweise fehlen erforderliche Felder oder enthalten ungültige Werte."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class TasksAssignedToUserView(generics.ListAPIView):
    """
    Gibt alle Tasks zurück, die dem aktuell angemeldeten Benutzer zugewiesen sind.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TaskSerializer

    def get_queryset(self):
        """
        Liefert alle Tasks, bei denen der aktuelle Benutzer als Bearbeiter eingetragen ist.
        """
        return Task.objects.filter(assignee=self.request.user)


class ReviewingView(generics.ListAPIView):
    """
    Gibt alle Tasks zurück, bei denen der aktuell angemeldete Benutzer als Reviewer eingetragen ist.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TaskSerializer

    def get_queryset(self):
        """
        Liefert alle Tasks, bei denen der aktuelle Benutzer als Reviewer eingetragen ist.
        """
        return Task.objects.filter(reviewer=self.request.user)