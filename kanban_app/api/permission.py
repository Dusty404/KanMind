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


class CommentPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, "task"):
            task = obj.task
        else:
            task = obj

        if request.method in ["GET", "POST", "PATCH", "PUT"]:
            return self._has_read_or_write_permission(request, task)

        if request.method == "DELETE":
            return self._has_delete_permission(request, obj)

        return False

    def _has_delete_permission(self, request, comment):
        if comment.owner_id == request.user.id:
            return True

        raise PermissionDenied({
            "detail": "Verboten. Nur der Ersteller des Kommentars darf ihn löschen."
        })
    
    def _has_read_or_write_permission(self, request, task):
        if (
            task.owner_id == request.user.id
            or task.board.owner_id == request.user.id
            or task.board.member.filter(user=request.user).exists()
        ):
            return True

        raise PermissionDenied({
            "detail": "Verboten. Der Benutzer muss Mitglied des Boards sein, zu dem die Task gehört."
        })

