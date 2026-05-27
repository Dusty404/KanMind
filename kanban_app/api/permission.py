from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in ["GET", "PATCH", "PUT"]:
            return self._has_read_or_write_permission(request, obj)

        if request.method == "DELETE":
            return self._has_delete_permission(request, obj)

        return False

    def _has_read_or_write_permission(self, request, obj):
        if obj.owner_id == request.user.id:
            return True

        if obj.member.filter(user=request.user).exists():
            return True

        raise PermissionDenied({
            "detail": "Verboten. Der Benutzer muss entweder Mitglied des Boards oder der Eigentümer des Boards sein."
        })

    def _has_delete_permission(self, request, obj):
        if obj.owner_id == request.user.id:
            return True

        raise PermissionDenied({
            "detail": "Verboten. Der Benutzer muss der Eigentümer des Boards sein, um es zu löschen."
        })


class BoardPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, board):
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


class TaskPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, task):
        if request.method == "DELETE":
            return self._has_delete_permission(request, task)

        if request.method in ["GET", "PATCH", "PUT"]:
            return self._has_read_or_write_permission(request, task)

        return False

    def _has_delete_permission(self, request, task):
        if self._is_owner_or_board_owner(request, task):
            return True

        raise PermissionDenied({
            "detail": "Verboten. Nur der Ersteller der Task oder der Board-Eigentümer kann die Task löschen."
        })

    def _has_read_or_write_permission(self, request, task):
        if self._is_owner_board_owner_or_member(request, task):
            return True

        raise PermissionDenied({
            "detail": "Verboten. Der Benutzer muss Mitglied des Boards sein, zu dem die Task gehört."
        })

    def _is_owner_or_board_owner(self, request, task):
        return task.owner_id == request.user.id or task.board.owner_id == request.user.id

    def _is_owner_board_owner_or_member(self, request, task):
        return (
            self._is_owner_or_board_owner(request, task)
            or task.board.member.filter(user=request.user).exists()
        )


class CommentPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, comment):
        if request.method == "DELETE":
            return self._has_delete_permission(request, comment)

        return True

    def _has_delete_permission(self, request, comment):
        if comment.owner_id == request.user.id:
            return True

        raise PermissionDenied({
            "detail": "Verboten. Nur der Ersteller des Kommentars darf ihn löschen."
        })
