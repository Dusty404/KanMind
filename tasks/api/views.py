from django.http import Http404
from rest_framework import generics, status, viewsets
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from kanban_app.models import Task

from .permission import TaskPermission
from .serializers import TaskSerializer


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