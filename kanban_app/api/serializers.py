from rest_framework import serializers
from kanban_app.models import Board, Task
from auth_app.models import User, UserProfile

class UserShortProfileSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="user.id", read_only=True)
    email = serializers.EmailField(source="user.email")

    class Meta:
        model = UserProfile
        fields = ["id", "email", "fullname"]


class TaskSerializer(serializers.ModelSerializer):
    board = serializers.PrimaryKeyRelatedField(
        queryset=Board.objects.all()
    )

    class Meta:
        model = Task
        fields = ["id", "title", "board"]


class BoardsSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()
    ticket_count = serializers.SerializerMethodField()
    tasks_to_do_count = serializers.SerializerMethodField()
    tasks_high_prio_count = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = ["id", "title", "member_count", "ticket_count", "tasks_to_do_count", "tasks_high_prio_count", "owner_id"]
        read_only_fields = ["id", "owner_id"]      

    def get_member_count(self, obj):
        return obj.member.count()

    def get_ticket_count(self, obj):
        return obj.tasks.count()

    def get_tasks_to_do_count(self, obj):
        return obj.tasks.filter(status="to_do").count()

    def get_tasks_high_prio_count(self, obj):
        return obj.tasks.filter(priority="high").count()
    

class BoardDetailSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)
    members = UserShortProfileSerializer(source="member", many=True, read_only=True)

    class Meta:
        model = Board
        fields = [
            "id",
            "title",
            "owner_id",
            "members",
            "tasks",
        ]


class BoardCreateSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(queryset=UserProfile.objects.all(), many=True, source="member", write_only=True)
    class Meta:
        model = Board
        fields = [
            "id",
            "title",
            "owner_id",
            "members",
            "tasks",
        ]


class BoardUpdateResponseSerializer(serializers.ModelSerializer):
    owner_data = serializers.SerializerMethodField()
    members_data = UserShortProfileSerializer(source="member", many=True, read_only=True)

    class Meta:
        model = Board
        fields = ["id", "title", "owner_data", "members_data"]

    def get_owner_data(self, obj):
        return {
            "id": obj.owner.id,
            "email": obj.owner.email,
            "fullname": obj.owner.profile.fullname
        }


class TaskSerializer(serializers.ModelSerializer):
    board = serializers.PrimaryKeyRelatedField(
        queryset=Board.objects.all()
    )

    class Meta:
        model = Task
        fields = ["id", "title", "board"]


class TaskDetailSerializer(serializers.ModelSerializer):
    assignee = UserShortProfileSerializer(read_only=True)
    reviewer = UserShortProfileSerializer(read_only=True)
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "reviewer",
            "due_date",
            "comments_count",
        ]

    def get_comments_count(self, obj):
        return obj.comments.count()