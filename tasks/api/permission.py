from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied

class TaskPermission(permissions.BasePermission):
    """
    Regelt den Zugriff auf Tasks.

    Lesen und Bearbeiten einer Task ist für den Task-Eigentümer, den Board-Eigentümer sowie für Mitglieder des zugehörigen Boards erlaubt.

    Das Löschen einer Task ist ausschließlich dem Task-Eigentümer oder dem Board-Eigentümer gestattet.
    """
    def has_object_permission(self, request, view, task):
        """
        Prüft die Berechtigung für die angeforderte Aktion anhand der verwendeten HTTP-Methode.
        """
        if request.method == "DELETE":
            return self._has_delete_permission(request, task)

        if request.method in ["GET", "PATCH", "PUT"]:
            return self._has_read_or_write_permission(request, task)

        return False

    def _has_delete_permission(self, request, task):
        """
        Erlaubt das Löschen einer Task für:

        - den Eigentümer der Task
        - den Eigentümer des zugehörigen Boards
        """
        if self._is_owner_or_board_owner(request, task):
            return True

        raise PermissionDenied({
            "detail": "Verboten. Nur der Ersteller der Task oder der Board-Eigentümer kann die Task löschen."
        })

    def _has_read_or_write_permission(self, request, task):
        """
        Erlaubt Lese- und Schreibzugriffe für:

        - den Eigentümer der Task
        - den Eigentümer des Boards
        - Mitglieder des zugehörigen Boards
        """
        if self._is_owner_board_owner_or_member(request, task):
            return True

        raise PermissionDenied({
            "detail": "Verboten. Der Benutzer muss Mitglied des Boards sein, zu dem die Task gehört."
        })

    def _is_owner_or_board_owner(self, request, task):
        """
        Prüft, ob der aktuelle Benutzer Eigentümer der Task oder Eigentümer des zugehörigen Boards ist.
        """
        return task.owner_id == request.user.id or task.board.owner_id == request.user.id

    def _is_owner_board_owner_or_member(self, request, task):
        """
        Prüft, ob der aktuelle Benutzer Zugriff auf die Task besitzt.

        Zugriff erhalten:
        - der Eigentümer der Task
        - der Eigentümer des Boards
        - Mitglieder des zugehörigen Boards
        """
        return (
            self._is_owner_or_board_owner(request, task)
            or task.board.member.filter(user=request.user).exists()
        )