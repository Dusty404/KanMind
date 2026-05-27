from rest_framework import serializers

from auth_app.models import User, UserProfile
from kanban_app.models import Board, Comment, Task


class UserShortProfileSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="user.id", read_only=True)
    email = serializers.EmailField(source="user.email")

    class Meta:
        model = UserProfile
        fields = ["id", "email", "fullname"]


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


class BoardsSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()
    ticket_count = serializers.SerializerMethodField()
    tasks_to_do_count = serializers.SerializerMethodField()
    tasks_high_prio_count = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = [
            "id",
            "title",
            "member_count",
            "ticket_count",
            "tasks_to_do_count",
            "tasks_high_prio_count",
            "owner_id",
        ]
        read_only_fields = ["id", "owner_id"]

    def get_member_count(self, obj):
        return obj.member.count()

    def get_ticket_count(self, obj):
        return obj.tasks.count()

    def get_tasks_to_do_count(self, obj):
        return obj.tasks.filter(status="to-do").count()

    def get_tasks_high_prio_count(self, obj):
        return obj.tasks.filter(priority="high").count()


class BoardDetailSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True, exclude_fields=["board"])
    members = UserShortProfileSerializer(source="member", many=True, read_only=True)

    class Meta:
        model = Board
        fields = ["id", "title", "owner_id", "members", "tasks"]
        read_only_fields = ["id", "owner_id", "tasks"]


class BoardPatchSerializer(serializers.ModelSerializer):
    members = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
    )

    class Meta:
        model = Board
        fields = ["title", "members"]


class BoardUpdateResponseSerializer(serializers.ModelSerializer):
    owner_data = serializers.SerializerMethodField()
    members_data = UserShortProfileSerializer(
        source="member",
        many=True,
        read_only=True,
    )

    class Meta:
        model = Board
        fields = ["id", "title", "owner_data", "members_data"]

    def get_owner_data(self, obj):
        return {
            "id": obj.owner.id,
            "email": obj.owner.email,
            "fullname": obj.owner.profile.fullname,
        }


class CommentsSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="owner.profile.fullname", read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "created_at", "author", "content"]
        read_only_fields = ["id", "created_at", "author"]
