from rest_framework import serializers
from kanban_app.models import Board
from auth_app.api.serializers import UserShortProfileSerializer
from kanban_app.api.serializers import TaskSerializer


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