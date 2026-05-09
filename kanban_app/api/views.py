from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, mixins, viewsets
from kanban_app.models import Board, UserProfile
from .serializers import BoardsSerializer, BoardDetailSerializer
from auth_app.api.permission import IsOwnerOrReadOnly
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotAuthenticated
from django.shortcuts import get_object_or_404


class BoardViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def permission_denied(self, request, message=None, code=None):
        if not request.user.is_authenticated:
            raise NotAuthenticated("Verboten. Der Benutzer muss entweder Mitglied des Boards oder der Eigentümer des Boards sein.")
        elif not request.user:
            raise NotAuthenticated("Nicht autorisiert. Der Benutzer muss eingeloggt sein, um auf die Ressource zuzugreifen.")
        super().permission_denied(request, message, code)

    def get_queryset(self):
        return Board.objects.filter(owner_id=self.request.user.id)

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
    
    def destroy(self, request, pk=None):
        board = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = BoardsSerializer(board)
        board.delete()
        return Response({"detail": "Das Board wurde erfolgreich gelöscht"}, status=status.HTTP_204_NO_CONTENT
)


# class BoardListAndCreateView(mixins.ListModelMixin, mixins.CreateModelMixin, generics.GenericAPIView):
#     permission_classes = [IsAuthenticated]

    # def permission_denied(self, request, message=None, code=None):
    #     if not request.user or not request.user.is_authenticated:
    #         raise NotAuthenticated("Nicht autorisiert. Der Benutzer muss eingeloggt sein.")
    #     super().permission_denied(request, message, code)
    
#     def get_queryset(self):
#         return Board.objects.filter(owner_id=self.request.user.id)
    
#     def get_serializer_class(self):
#         if self.request.method == "POST":
#             return BoardsCreateSerializer
#         return BoardsSerializer
    
#     def get(self, request, *args, **kwargs):
#         return self.list(request, *args, **kwargs)
    
#     def post(self, request):
#         serializer = self.get_serializer(
#             data=request.data,
#             context={"request": request}
#         )

#         if serializer.is_valid():
#             board = serializer.save(owner=request.user)

#             return Response({
#             "id": board.id,
#             "title": board.title,
#             "member_count": board.member.count(),
#             "ticket_count": board.tasks.count(),
#             "tasks_to_do_count": board.tasks.filter(status="to_do").count(),
#             "tasks_high_prio_count": board.tasks.filter(priority="high").count(),
#             "owner_id": board.owner_id,
#         }, status=status.HTTP_201_CREATED)

#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    
# class BoardDetailView(generics.RetrieveAPIView):
#     permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
#     queryset = Board.objects.all()
#     serializer_class = BoardsSerializer


# class BoardCreateView(APIView):
#     permission_classes = [IsAuthenticated]
#     serializer_class = BoardsCreateSerializer

#     def permission_denied(self, request, message=None, code=None):
#         if not request.user or not request.user.is_authenticated:
#             raise NotAuthenticated("Nicht autorisiert. Der Benutzer muss eingeloggt sein.")
#         super().permission_denied(request, message, code)

#     def post(self, request):
#         serializer = self.get_serializer(data=request.data)

#         if serializer.is_valid():
#             board = serializer.save(owner=request.user)

#             return Response({
#                 "id": board.id,
#                 "title": board.title,
#                 "member_count": board.member.count(),
#                 "ticket_count": board.tasks.count(),
#                 "tasks_to_do_count": board.tasks.filter(status="to_do").count(),
#                 "tasks_high_prio_count": board.tasks.filter(priority="high").count(),
#                 "owner_id": board.owner_id,
#             }, status=status.HTTP_201_CREATED)

#         return Response({"Ungültige Anfragedaten. Möglicherweise sind einige Benutzer-Email-Adressen ungültig."}, status=status.HTTP_400_BAD_REQUEST)