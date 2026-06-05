from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied

class TaskPermission(permissions.BasePermission):
    """
    Controls access to tasks.

    Viewing and updating a task is allowed for the task owner,
    the board owner, and members of the associated board.

    Deleting a task is restricted to the task owner or the board owner.
    """
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