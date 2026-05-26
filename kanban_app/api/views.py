from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, mixins, viewsets
from kanban_app.models import Board, UserProfile, User, Task, Comment
from .serializers import BoardsSerializer, BoardDetailSerializer, BoardUpdateResponseSerializer, UserShortProfileSerializer, TaskSerializer, CommentsSerializer, BoardPatchSerializer
from .permission import IsOwnerOrReadOnly, IsTaskOwnerOrBoardOwner
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.http import Http404
from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError


class BoardViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    serializer_class = BoardsSerializer

    def get_queryset(self):
        try:
            return Board.objects.filter(
            Q(owner_id=self.request.user.id) |
            Q(member__user=self.request.user)
            ).distinct()
        except Board.DoesNotExist:
            return None, Response({"detail": "Board nicht gefunden. Die angegebene Task-ID existiert nicht."}, status=status.HTTP_404_NOT_FOUND) 

    def list(self, request):
        boards = self.get_queryset()
        serializer = BoardsSerializer(boards, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        try:
            board = Board.objects.get(pk=pk)
        except Board.DoesNotExist:
            return Response(
                {"detail": "Board nicht gefunden. Die angegebene Board-ID existiert nicht."}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, board)
        serializer = BoardDetailSerializer(board)
        return Response(serializer.data)
    
    def create(self, request):
        serializer = BoardsSerializer(data=request.data)
        
        if serializer.is_valid():
            member_ids = request.data.get("members", [])
            profiles = UserProfile.objects.filter(user_id__in=member_ids)
            if profiles.count() != len(member_ids):
                return Response({"detail": "Ungültige Anfragedaten. Möglicherweise sind einige Benutzer-Email-Adressen ungültig."}, status=status.HTTP_400_BAD_REQUEST)
            board = serializer.save(owner=request.user)
            board.member.set(profiles)
            response_serializer = BoardsSerializer(board)
            data = response_serializer.data
            data["detail"] = "Das Board wurde erfolgreich erstellt"
            return Response(data, status=status.HTTP_201_CREATED)
        return Response({"detail": "Ungültige Anfragedaten. Möglicherweise sind einige Benutzer-Email-Adressen ungültig."}, status=status.HTTP_400_BAD_REQUEST)
    
    def partial_update(self, request, pk=None):
        try:
            board = Board.objects.get(pk=pk)
        except Board.DoesNotExist:
            return Response(
                {"detail": "Board nicht gefunden. Die angegebene Board-ID existiert nicht."}, status=status.HTTP_404_NOT_FOUND)
        serializer = BoardPatchSerializer(board, data=request.data, partial=True)

        if serializer.is_valid():
            self.check_object_permissions(request, board)
            member_ids = request.data.get("members", None)
            if member_ids is not None:
                profiles = UserProfile.objects.filter(user_id__in=member_ids)
                if profiles.count() != len(member_ids):
                    return Response({"detail": "Ungültige Anfragedaten. Möglicherweise sind einige Benutzer-Email-Adressen ungültig."}, status=status.HTTP_400_BAD_REQUEST)
            board = serializer.save()
            if member_ids is not None:
                board.member.set(profiles)
            response_serializer = BoardUpdateResponseSerializer(board)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        return Response({"detail": "Ungültige Anfragedaten. Möglicherweise sind einige Benutzer-Email-Adressen ungültig."}, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, pk=None):
        try:
            board = Board.objects.get(pk=pk)
        except Board.DoesNotExist:
            return Response(
                {"detail": "Board nicht gefunden. Die angegebene Board-ID existiert nicht."}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, board)
        board.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

class TasksViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsTaskOwnerOrBoardOwner]
    serializer_class = TaskSerializer

    def get_queryset(self):
        return Task.objects.all()
    
    def get_object(self):
        pk = self.kwargs.get("pk")

        if not str(pk).isdigit():
            raise ValidationError({"detail": "Ungültige Anfragedaten. Die übermittelte Task-ID ist fehlerhaft."})
        try:
            return super().get_object()
        except Http404:
            raise NotFound({"detail": "Task nicht gefunden. Die angegebene Task-ID existiert nicht."})

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            if "board" in serializer.errors:
                return Response({"detail": "Board nicht gefunden. Die angegebene Board-ID existiert nicht."}, status=status.HTTP_404_NOT_FOUND)
            return Response({"detail": "Ungültige Anfragedaten. Möglicherweise fehlen erforderliche Felder oder enthalten ungültige Werte."}, status=status.HTTP_400_BAD_REQUEST)

        board = serializer.validated_data.get("board")

        if not (board.owner_id == request.user.id or board.member.filter(user=request.user).exists()):
            raise PermissionDenied({"detail": "Verboten. Der Benutzer muss Mitglied des Boards sein, um eine Task zu erstellen."})

        task = serializer.save(owner=self.request.user)
        profiles_to_add = []

        if task.assignee:
            profiles_to_add.append(task.assignee.profile)
        if task.reviewer:
            profiles_to_add.append(task.reviewer.profile)
        if profiles_to_add:
            task.board.member.add(*profiles_to_add)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def partial_update(self, request, *args, **kwargs):
    
        task = self.get_object()
        serializer = TaskSerializer(task, data=request.data, partial=True, exclude_fields=['board', 'comments_count', 'assignee', 'reviewer'])

        if not serializer.is_valid():
            return Response({"detail": "Ungültige Anfragedaten. Möglicherweise fehlen erforderliche Felder oder enthalten ungültige Werte."}, status=status.HTTP_400_BAD_REQUEST)
        elif serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        try:
            task = self.get_object()
        except Task.DoesNotExist:
            return Response({"detail": "Task nicht gefunden. Die angegebene Task-ID existiert nicht."}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, task)
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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
    permission_classes = [IsAuthenticated]

    def get_task(self, task_id, request):

        try:
            task = Task.objects.get(pk=task_id)
        except Task.DoesNotExist:
            return None, Response({"detail": "Task nicht gefunden. Die angegebene Task-ID existiert nicht."}, status=status.HTTP_404_NOT_FOUND) 
        
        is_member = task.board.member.filter(user=request.user).exists()
        is_owner = task.board.owner_id == request.user.id

        try:
            task = Task.objects.get(pk=task_id)
        except Task.DoesNotExist:
            return None, Response({"detail": "Task nicht gefunden. Die angegebene Task-ID existiert nicht."}, status=status.HTTP_404_NOT_FOUND)        

        if not is_member and not is_owner:
            return None, Response({"detail": "Verboten. Der Benutzer muss Mitglied des Boards sein, zu dem die Task gehört."}, status=status.HTTP_403_FORBIDDEN)
        return task, None

    def get(self, request, task_id):

        task, error_response = self.get_task(task_id, request)
        if error_response:
            return error_response

        comments = task.comments.all().order_by("created_at")
        serializer = CommentsSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, task_id):

        task, error_response = self.get_task(task_id, request)
        if error_response:
            return error_response

        serializer = CommentsSerializer(data=request.data)
        if not request.data.get("content", "").strip():
            return Response({"detail": "Ungültige Anfragedaten. Möglicherweise ist der `content`-Wert leer."}, status=status.HTTP_400_BAD_REQUEST)
        if serializer.is_valid():
            comment = serializer.save(task=task, author=request.user.profile)
            response_serializer = CommentsSerializer(comment)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, task_id, comment_id):

        task, error_response = self.get_task(task_id, request)
        if error_response:
            return error_response

        try:
            comment = task.comments.get(pk=comment_id)
        except Comment.DoesNotExist:
            return Response({"detail": "Kommentar oder Task nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)

        if comment.author.user_id != request.user.id:
            return Response({"detail": "Verboten. Nur der Ersteller des Kommentars darf ihn löschen."}, status=status.HTTP_403_FORBIDDEN)
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

class EmailCheckView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        email = request.query_params.get("email")

        if not email:
            return Response({"detail": "Ungültige Anfrage. Die E-Mail-Adresse fehlt oder hat ein falsches Format."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "Email nicht gefunden. Die Email existiert nicht."}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserShortProfileSerializer(user.profile)
        return Response(serializer.data, status=status.HTTP_200_OK)