from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied

class CommentPermission(permissions.BasePermission):
    """
    Regelt den Zugriff auf Kommentare und kommentierbare Tasks.

    Lesen und Erstellen von Kommentaren ist für den Task-Eigentümer, den Board-Eigentümer sowie für Mitglieder des zugehörigen Boards erlaubt.

    Das Löschen eines Kommentars ist ausschließlich dem Ersteller des Kommentars gestattet.
    """
    def has_object_permission(self, request, view, obj):
        """
        Prüft die Berechtigung für die angeforderte Aktion.

        Für Lese- und Schreiboperationen wird die Berechtigung anhand der zugehörigen Task geprüft.

        Für Löschoperationen wird die Berechtigung anhand des Kommentars selbst geprüft.
        """
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
        """
        Erlaubt das Löschen eines Kommentars ausschließlich für dessen Ersteller.
        """
        if comment.owner_id == request.user.id:
            return True

        raise PermissionDenied({
            "detail": "Verboten. Nur der Ersteller des Kommentars darf ihn löschen."
        })
    
    def _has_read_or_write_permission(self, request, task):
        """
        Erlaubt das Lesen und Erstellen von Kommentaren für:

        - den Eigentümer der Task
        - den Eigentümer des Boards
        - Mitglieder des zugehörigen Boards
        """
        if (
            task.owner_id == request.user.id
            or task.board.owner_id == request.user.id
            or task.board.member.filter(user=request.user).exists()
        ):
            return True

        raise PermissionDenied({
            "detail": "Verboten. Der Benutzer muss Mitglied des Boards sein, zu dem die Task gehört."
        })