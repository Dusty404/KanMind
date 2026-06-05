from rest_framework import serializers
from ..models import Board
from auth_app.api.serializers import UserShortProfileSerializer
from auth_app.models import UserProfile
from tasks.api.serializers import TaskSerializer


class BoardsSerializer(serializers.ModelSerializer):
    """
    Serializes board data for list views.

    ticket_count shows amount of tasks in the board.
    tasks_to_do_count and task_high_prio_count shows how many of all task in the board are high prio and in to_do state.
    """
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
    

class BoardCreateSerializer(serializers.ModelSerializer):
    """
    Validates data for creating a new board with the given member IDs.
    """
    members = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True,
    )

    class Meta:
        model = Board
        fields = ["id", "title", "members", "owner_id"]
        read_only_fields = ["id", "owner_id"]

    def validate_members(self, member_ids):
        """
        Checks if the member id exists in the database.
        profile.count takes the number of all existing profiles and compares this number with the amount of member ids given.
        If it is even it returns the UserProfile data.
        If the numbers are odd it returns a validation error.
        """
        profiles = UserProfile.objects.filter(user_id__in=member_ids)

        if profiles.count() != len(member_ids):
            raise serializers.ValidationError(
                "Ungültige Anfragedaten. Möglicherweise sind einige Benutzer-Email-Adressen ungültig."
            )

        return profiles

    def create(self, validated_data):
        profiles = validated_data.pop("members", [])
        owner = self.context["request"].user

        board = Board.objects.create(owner=owner, **validated_data)
        board.member.set(profiles)

        return board


class BoardDetailSerializer(serializers.ModelSerializer):
    """
    Serializes detailed information about a single board.
    """
    tasks = TaskSerializer(many=True, read_only=True, exclude_fields=["board"])
    members = UserShortProfileSerializer(source="member", many=True, read_only=True)

    class Meta:
        model = Board
        fields = ["id", "title", "owner_id", "members", "tasks"]
        read_only_fields = ["id", "owner_id", "tasks"]


class BoardPatchSerializer(serializers.ModelSerializer):
    """
    Serializer to validate update data for a single board.
    Only the title and members can be modified.
    Checks if all given member ID's exist in the database and returns a validation error message if they don't exist.
    """
    members = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
    )

    class Meta:
        model = Board
        fields = ["title", "members"]

    def validate_members(self, member_ids):
        profiles = UserProfile.objects.filter(user_id__in=member_ids)

        if profiles.count() != len(member_ids):
            raise serializers.ValidationError(
                "Ungültige Anfragedaten. Möglicherweise sind einige Benutzer-Email-Adressen ungültig."
            )

        return profiles

    def update(self, instance, validated_data):
        profiles = validated_data.pop("members", None)

        instance = super().update(instance, validated_data)

        if profiles is not None:
            instance.member.set(profiles)

        return instance


class BoardUpdateResponseSerializer(serializers.ModelSerializer):
    """
    Serializer for board update responses.

    Validates data and forms a detailed response with all data from the updated board.
    Provides more information than BoardPatchSerializer, including owner and member details.
    """
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