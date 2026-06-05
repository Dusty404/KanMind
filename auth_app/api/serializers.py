from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import serializers

from auth_app.models import UserProfile


class RegistrationSerializer(serializers.ModelSerializer):
    """
    Validates data for creating a new account in the database.

    Returns an error if the provided email address already exists.

    Creates two database entries:
    - User for login credentials
    - UserProfile for all board, task, and comment relations

    User and UserProfile IDs may be different.
    """
    fullname = serializers.CharField(max_length=150)
    repeated_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "fullname", "email", "password", "repeated_password"]
        extra_kwargs = {
            "password": {"write_only": True},
            "id": {"read_only": True},
        }

    def validate(self, data):
        self.validate_passwords(data)
        self.validate_email_is_unique(data["email"])
        return data

    def validate_passwords(self, data):
        if data["password"] != data["repeated_password"]:
            raise serializers.ValidationError({
                "password": "Passwords do not match."
            })

    def validate_email_is_unique(self, email):
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({
                "email": "Email already exists."
            })

    def create(self, validated_data):
        """
        Coordinates the creation of a User and UserProfile in the database.
        """
        fullname = validated_data.pop("fullname")
        validated_data.pop("repeated_password")
        user = self.create_user(validated_data)
        self.create_profile(user, fullname)
        return user

    def create_user(self, validated_data):
        email = validated_data["email"]
        return User.objects.create_user(
            username=email,
            email=email,
            password=validated_data["password"],
        )

    def create_profile(self, user, fullname):
        UserProfile.objects.create(
            user=user,
            fullname=fullname,
        )


class CustomLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user_data = self.get_user_by_email(data.get("email"))
        user = self.authenticate_user(user_data, data.get("password"))
        data["user"] = user
        return data

    def get_user_by_email(self, email):
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Ungültige Anfragedaten.")

    def authenticate_user(self, user_data, password):
        user = authenticate(username=user_data.username, password=password)
        if not user:
            raise serializers.ValidationError("Ungültige Anfragedaten.")
        return user

class UserShortProfileSerializer(serializers.ModelSerializer):
    """
    Serializes UserProfile data for use in other serializers.
    """
    id = serializers.IntegerField(source="user.id", read_only=True)
    email = serializers.EmailField(source="user.email")

    class Meta:
        model = UserProfile
        fields = ["id", "email", "fullname"]