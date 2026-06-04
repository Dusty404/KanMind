from rest_framework import serializers
from ..models import Board
from auth_app.api.serializers import UserShortProfileSerializer
from auth_app.models import UserProfile
from tasks.api.serializers import TaskSerializer


class BoardsSerializer(serializers.ModelSerializer):
    """
    Serializer für die Board-Übersicht.

    Stellt die Basisinformationen eines Boards sowie aggregierte Kennzahlen wie Mitglieder-, Ticket- und Aufgabenstatistiken bereit.
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
        """
        Ermittelt die Anzahl der Mitglieder des Boards.
        """
        return obj.member.count()

    def get_ticket_count(self, obj):
        """
        Ermittelt die Gesamtanzahl der Tasks des Boards.
        """
        return obj.tasks.count()

    def get_tasks_to_do_count(self, obj):
        """
        Ermittelt die Anzahl der Tasks mit dem Status 'to-do'.
        """
        return obj.tasks.filter(status="to-do").count()

    def get_tasks_high_prio_count(self, obj):
        """
        Ermittelt die Anzahl der Tasks mit hoher Priorität.
        """
        return obj.tasks.filter(priority="high").count()
    

class BoardCreateSerializer(serializers.ModelSerializer):
    """
    Serializer zum Erstellen neuer Boards.

    Validiert die übergebenen Mitglieder-IDs und erstellt anschließend das Board inklusive der zugehörigen Mitglieder.
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
        Prüft, ob für alle übergebenen Benutzer-IDs entsprechende Benutzerprofile existieren.
        """
        profiles = UserProfile.objects.filter(user_id__in=member_ids)

        if profiles.count() != len(member_ids):
            raise serializers.ValidationError(
                "Ungültige Anfragedaten. Möglicherweise sind einige Benutzer-Email-Adressen ungültig."
            )

        return profiles

    def create(self, validated_data):
        """
        Erstellt ein neues Board und verknüpft die angegebenen Mitglieder mit dem Board.
        """
        profiles = validated_data.pop("members", [])
        owner = self.context["request"].user

        board = Board.objects.create(owner=owner, **validated_data)
        board.member.set(profiles)

        return board


class BoardDetailSerializer(serializers.ModelSerializer):
    """
    Serializer für die Detailansicht eines Boards.

    Enthält die vollständigen Board-Informationen inklusive Mitglieder und zugehöriger Tasks.
    """
    tasks = TaskSerializer(many=True, read_only=True, exclude_fields=["board"])
    members = UserShortProfileSerializer(source="member", many=True, read_only=True)

    class Meta:
        model = Board
        fields = ["id", "title", "owner_id", "members", "tasks"]
        read_only_fields = ["id", "owner_id", "tasks"]


class BoardPatchSerializer(serializers.ModelSerializer):
    """
    Serializer für Teilaktualisierungen eines Boards.

    Unterstützt das Ändern des Board-Titels sowie das Aktualisieren der Mitgliederliste.
    """
    members = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
    )

    class Meta:
        model = Board
        fields = ["title", "members"]

    def validate_members(self, member_ids):
        """
        Prüft, ob für alle übergebenen Benutzer-IDs
        entsprechende Benutzerprofile existieren.
        """
        profiles = UserProfile.objects.filter(user_id__in=member_ids)

        if profiles.count() != len(member_ids):
            raise serializers.ValidationError(
                "Ungültige Anfragedaten. Möglicherweise sind einige Benutzer-Email-Adressen ungültig."
            )

        return profiles

    def update(self, instance, validated_data):
        """
        Aktualisiert die Board-Daten und ersetzt bei Bedarf die bestehende Mitgliederliste.
        """
        profiles = validated_data.pop("members", None)

        instance = super().update(instance, validated_data)

        if profiles is not None:
            instance.member.set(profiles)

        return instance


class BoardUpdateResponseSerializer(serializers.ModelSerializer):
    """
    Serializer für die Antwort nach einer erfolgreichen Board-Aktualisierung.

    Ergänzt die Board-Daten um detaillierte Informationen zum Eigentümer und zu allen Mitgliedern.
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
        """
        Erstellt die Profildaten des Board-Eigentümers
        für die API-Antwort.
        """
        return {
            "id": obj.owner.id,
            "email": obj.owner.email,
            "fullname": obj.owner.profile.fullname,
        }