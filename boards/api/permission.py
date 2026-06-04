from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied

class BoardPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, board):
        if request.method in ["GET", "PATCH", "PUT"]:
            return self._has_read_or_write_permission(request, board)

        if request.method == "DELETE":
            return self._has_delete_permission(request, board)

        if self._is_owner_or_member(request, board):
            return True

        raise PermissionDenied({
            "detail": "Verboten. Der Benutzer muss entweder Mitglied des Boards oder der Eigentümer des Boards sein."
        })

    def _has_delete_permission(self, request, board):
        if board.owner_id == request.user.id:
            return True

        raise PermissionDenied({
            "detail": "Verboten. Der Benutzer muss der Eigentümer des Boards sein, um es zu löschen."
        })

    def _is_owner_or_member(self, request, board):
        return (
            board.owner_id == request.user.id
            or board.member.filter(user=request.user).exists()
        )
    
    def _has_read_or_write_permission(self, request, board):
        if board.owner_id == request.user.id:
            return True

        if board.member.filter(user=request.user).exists():
            return True

        raise PermissionDenied({
            "detail": "Verboten. Der Benutzer muss entweder Mitglied des Boards oder der Eigentümer des Boards sein."
        })