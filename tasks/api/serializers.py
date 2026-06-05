from rest_framework import serializers

from auth_app.models import User
from auth_app.api.serializers import UserShortProfileSerializer
from ..models import Task


class TaskSerializer(serializers.ModelSerializer):
    """
    Provides task data for the API and handles the creation of new tasks, including permission checks and automatic board member management.
    When a task is created, the serializer automatically adds the assignee and reviewer to the board members if they are not already members.
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
        Initializes the serializer and removes any fields specified in the exclude_fields parameter from the serialization.
        """
        exclude_fields = kwargs.pop("exclude_fields", [])
        super().__init__(*args, **kwargs)
        self._remove_excluded_fields(exclude_fields)

    def get_comments_count(self, obj):
        return obj.comments.count()

    def _remove_excluded_fields(self, exclude_fields):
        for field in exclude_fields:
            self.fields.pop(field, None)

    def validate(self, attrs):
        board = attrs.get("board")

        if board and not self._can_create_task(board):
            raise serializers.ValidationError({
                "permission": "Der Benutzer darf auf diesem Board keine Task erstellen."
            })

        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        task = Task.objects.create(owner=request.user, **validated_data)
        self._add_profiles_to_board(task)
        return task

    def _can_create_task(self, board):
        """
        Checks whether the user is allowed to create a task.

        Users allowed to create a task are:
        - The board owner
        - Members of the board
        """
        request = self.context["request"]

        return (
            board.owner_id == request.user.id
            or board.member.filter(user=request.user).exists()
        )

    def _add_profiles_to_board(self, task):
        """
        Adds the assignee and reviewer to the board members if they are not already members.
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
    Handles updates to existing tasks.

    The board ID cannot be changed during a task update.
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