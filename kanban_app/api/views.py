from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, mixins
from kanban_app.models import Board
from .serializers import BoardsSerializer, BoardsCreateSerializer
from auth_app.api.permission import IsOwnerOrReadOnly
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotAuthenticated


class BoardListAndCreateView(mixins.ListModelMixin, mixins.CreateModelMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def permission_denied(self, request, message=None, code=None):
        if not request.user or not request.user.is_authenticated:
            raise NotAuthenticated("Nicht autorisiert. Der Benutzer muss eingeloggt sein.")
        super().permission_denied(request, message, code)
    
    def get_queryset(self):
        return Board.objects.filter(owner_id=self.request.user.id)
    
    def get_serializer_class(self):
        if self.request.method == "POST":
            return BoardsCreateSerializer
        return BoardsSerializer
    
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
    
    def post(self, request):
        serializer = self.get_serializer(
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():
            board = serializer.save(owner=request.user)

            return Response({
            "id": board.id,
            "title": board.title,
            "member_count": board.member.count(),
            "ticket_count": board.tasks.count(),
            "tasks_to_do_count": board.tasks.filter(status="to_do").count(),
            "tasks_high_prio_count": board.tasks.filter(priority="high").count(),
            "owner_id": board.owner_id,
        }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    
class BoardDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    queryset = Board.objects.all()
    serializer_class = BoardsSerializer


class BoardCreateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BoardsCreateSerializer

    def permission_denied(self, request, message=None, code=None):
        if not request.user or not request.user.is_authenticated:
            raise NotAuthenticated("Nicht autorisiert. Der Benutzer muss eingeloggt sein.")
        super().permission_denied(request, message, code)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            board = serializer.save(owner=request.user)

            return Response({
                "id": board.id,
                "title": board.title,
                "member_count": board.member.count(),
                "ticket_count": board.tasks.count(),
                "tasks_to_do_count": board.tasks.filter(status="to_do").count(),
                "tasks_high_prio_count": board.tasks.filter(priority="high").count(),
                "owner_id": board.owner_id,
            }, status=status.HTTP_201_CREATED)

        return Response({"Ungültige Anfragedaten. Möglicherweise sind einige Benutzer-Email-Adressen ungültig."}, status=status.HTTP_400_BAD_REQUEST)