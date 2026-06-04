from rest_framework import serializers

from auth_app.models import User
from auth_app.api.serializers import UserShortProfileSerializer
from ..models import Task


class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer für Tasks.

    Stellt Task-Daten für die API bereit und verarbeitet die Erstellung neuer Tasks inklusive Berechtigungsprüfung und automatischer Mitgliederverwaltung.
    """
    assignee_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="assignee",
        write_only=True,
        required=False,
        allow_null=True,
    )
    reviewer_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="reviewer",
        write_only=True,
        required=False,
        allow_null=True,
    )
    assignee = UserShortProfileSerializer(
        source="assignee.profile",
        read_only=True,
        required=False,
        allow_null=True,
    )
    reviewer = UserShortProfileSerializer(
        source="reviewer.profile",
        read_only=True,
        required=False,
        allow_null=True,
    )
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id",
            "board",
            "title",
            "description",
            "status",
            "priority",
            "assignee_id",
            "reviewer_id",
            "assignee",
            "reviewer",
            "due_date",
            "comments_count",
        ]

    def __init__(self, *args, **kwargs):
        """
        Initialisiert den Serializer und entfernt optional angegebene Felder aus der Serialisierung.
        """
        exclude_fields = kwargs.pop("exclude_fields", [])
        super().__init__(*args, **kwargs)
        self._remove_excluded_fields(exclude_fields)

    def get_comments_count(self, obj):
        """
        Ermittelt die Anzahl der Kommentare einer Task.
        """
        return obj.comments.count()

    def _remove_excluded_fields(self, exclude_fields):
        """
        Entfernt die angegebenen Felder dynamisch aus dem Serializer.
        """
        for field in exclude_fields:
            self.fields.pop(field, None)

    def validate(self, attrs):
        """
        Prüft, ob der aktuelle Benutzer auf dem angegebenen Board
        Tasks erstellen darf.
        """
        board = attrs.get("board")

        if board and not self._can_create_task(board):
            raise serializers.ValidationError({
                "permission": "Der Benutzer darf auf diesem Board keine Task erstellen."
            })

        return attrs

    def create(self, validated_data):
        """
        Erstellt eine neue Task und fügt Assignee und Reviewer
        bei Bedarf automatisch als Board-Mitglieder hinzu.
        """
        request = self.context["request"]
        task = Task.objects.create(owner=request.user, **validated_data)
        self._add_profiles_to_board(task)
        return task

    def _can_create_task(self, board):
        """
        Prüft, ob der aktuelle Benutzer auf dem Board
        Tasks erstellen darf.

        Erlaubt sind:
        - der Board-Eigentümer
        - Mitglieder des Boards
        """
        request = self.context["request"]

        return (
            board.owner_id == request.user.id
            or board.member.filter(user=request.user).exists()
        )

    def _add_profiles_to_board(self, task):
        """
        Fügt Assignee und Reviewer der Task automatisch
        als Mitglieder zum Board hinzu.
        """
        profiles = []

        if task.assignee:
            profiles.append(task.assignee.profile)

        if task.reviewer:
            profiles.append(task.reviewer.profile)

        if profiles:
            task.board.member.add(*profiles)

class TaskPatchSerializer(TaskSerializer):
    """
    Serializer für Teilaktualisierungen einer Task.

    Erlaubt das Bearbeiten von Task-Daten ohne Änderung
    der Board-Zuordnung.
    """
    class Meta(TaskSerializer.Meta):
        fields = [
            "id",
            "title",
            "description",
            "status",
            "priority",
            "assignee_id",
            "reviewer_id",
            "assignee",
            "reviewer",
            "due_date",
        ]

    def validate(self, attrs):
        """
        Überschreibt die Create-Validierung, da bei einem Patch keine Board-Berechtigung geprüft werden muss.
        """
        return attrs