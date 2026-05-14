from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, mixins, viewsets
from kanban_app.models import Board, UserProfile, User
from .serializers import BoardsSerializer, BoardDetailSerializer, BoardUpdateResponseSerializer, UserShortProfileSerializer
from .permission import IsOwnerOrReadOnly
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q


class BoardViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    serializer_class = BoardsSerializer

    def get_queryset(self):
        return Board.objects.filter(
        Q(owner_id=self.request.user.id) |
        Q(member__user=self.request.user)
    ).distinct()

    def list(self, request):
        boards = self.get_queryset()
        serializer = BoardsSerializer(boards, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        board = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = BoardDetailSerializer(board)
        return Response(serializer.data)
    
    def create(self, request):
        serializer = BoardsSerializer(data=request.data)
        if serializer.is_valid():
            member_ids = request.data.get("members", [])
            profiles = UserProfile.objects.filter(user_id__in=member_ids)
            if profiles.count() != len(member_ids):
                return Response({
                    "detail": "Ungültige Anfragedaten. Möglicherweise sind einige Benutzer-IDs ungültig."
                }, status=status.HTTP_400_BAD_REQUEST)
            board = serializer.save(owner=request.user)
            board.member.set(profiles)
            response_serializer = BoardsSerializer(board)
            data = response_serializer.data
            data["detail"] = "Das Board wurde erfolgreich erstellt"
            return Response(data, status=status.HTTP_201_CREATED)
        return Response({
            "detail": "Ungültige Anfragedaten."
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def partial_update(self, request, pk=None):
        board = get_object_or_404(Board, pk=pk)
        self.check_object_permissions(request, board)
        serializer = BoardDetailSerializer(board, data=request.data, partial=True)

        if serializer.is_valid():
            member_ids = request.data.get("members", None)
            if member_ids is not None:
                profiles = UserProfile.objects.filter(user_id__in=member_ids)
            if profiles.count() != len(member_ids):
                return Response({
                    "detail": "Ungültige Anfragedaten. Möglicherweise sind einige Benutzer-IDs ungültig."
                }, status=status.HTTP_400_BAD_REQUEST)
            board = serializer.save()
            if member_ids is not None:
                board.member.set(profiles)
            response_serializer = BoardUpdateResponseSerializer(board)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        return Response({"detail": "Ungültige Anfragedaten."}, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, pk=None):
        try:
            board = Board.objects.get(pk=pk)
        except Board.DoesNotExist:
            return Response(
                {"detail": "Board nicht gefunden. Die angegebene Board-ID existiert nicht."}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, board)
        board.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

class TasksViewSet(viewsets.ViewSet):
    pass
    

class EmailCheckView(APIView):
    def get(self, request, email):
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "Email nicht gefunden. Die Email exestiert nicht."}, status=status.HTTP_404_NOT_FOUND)
        response_serializer = UserShortProfileSerializer(user.profile)
        return Response(response_serializer.data, status=status.HTTP_200_OK)