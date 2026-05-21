from rest_framework import permissions
from rest_framework.exceptions import NotAuthenticated, PermissionDenied

class IsOwnerOrReadOnly(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):

        if not request.user.is_authenticated:
            raise PermissionDenied({"detail": "Verboten. Der Benutzer muss entweder der Eigentümer oder ein Mitglied des Boards sein."})
        

        if request.method == "PATCH":
            if request.user.is_authenticated:
                return True

            raise PermissionDenied({"detail": "Verboten. Der Benutzer muss entweder der Eigentümer oder ein Mitglied des Boards sein."})
        

        if request.method == "DELETE":
            if obj.owner_id == request.user.id:
                return True

            raise PermissionDenied({"detail": "Verboten. Der Benutzer muss der Eigentümer des Boards sein, um es zu löschen."})
        
    
class IsTaskOwnerOrBoardOwner(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.method == "DELETE":
            if obj.owner_id == request.user.id or obj.board.owner_id == request.user.id:
                return True

            raise PermissionDenied({"detail": "Verboten. Nur der Ersteller der Task oder der Board-Eigentümer kann die Task löschen."})