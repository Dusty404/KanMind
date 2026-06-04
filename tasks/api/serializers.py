from rest_framework import serializers

from auth_app.models import User
from auth_app.api.serializers import UserShortProfileSerializer
from ..models import Task


class TaskSerializer(serializers.ModelSerializer):
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
        exclude_fields = kwargs.pop("exclude_fields", [])
        super().__init__(*args, **kwargs)
        self._remove_excluded_fields(exclude_fields)

    def get_comments_count(self, obj):
        return obj.comments.count()

    def _remove_excluded_fields(self, exclude_fields):
        for field in exclude_fields:
            self.fields.pop(field)