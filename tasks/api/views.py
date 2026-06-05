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
    Manages CRUD operations for tasks.

    Allows users to create, retrieve, update, and delete tasks
    while enforcing the defined permissions.
    """
    permission_classes = [IsAuthenticated, TaskPermission]
    serializer_class = TaskSerializer
    queryset = Task.objects.all()

    def get_serializer_class(self):
        if self.action == "partial_update":
            return TaskPatchSerializer

        return TaskSerializer

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

        task = serializer.save()
        response_serializer = TaskSerializer(task)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        task = self.get_object()
        serializer = self.get_serializer(task, data=request.data, partial=True)

        if not serializer.is_valid():
            return self._invalid_task_data_response()

        task = serializer.save()
        response_serializer = TaskSerializer(task)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def _validate_task_pk(self):
        pk = self.kwargs.get("pk")
        if not str(pk).isdigit():
            raise ValidationError({
                "detail": "Ungültige Anfragedaten. Die übermittelte Task-ID ist fehlerhaft."
            })

    def _invalid_task_response(self, serializer):
        """
        Checks whether the validation errors contain a board or permission error 
        and returns a 404 response if the specified board does not exist and a 403 response if the user does not have permission to create a task.
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
        return Response(
            {"detail": "Ungültige Anfragedaten. Möglicherweise fehlen erforderliche Felder oder enthalten ungültige Werte."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class TasksAssignedToUserView(generics.ListAPIView):
    """
    Returns all tasks assigned to the currently authenticated user.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TaskSerializer

    def get_queryset(self):
        return Task.objects.filter(assignee=self.request.user)


class ReviewingView(generics.ListAPIView):
    """
    Returns all tasks where the currently authenticated user is assigned
    as the reviewer.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TaskSerializer

    def get_queryset(self):
        return Task.objects.filter(reviewer=self.request.user)