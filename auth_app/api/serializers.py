from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from auth_app.models import UserProfile


class RegistrationSerializer(serializers.ModelSerializer):
    fullname = serializers.CharField(max_length=150)
    repeated_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'fullname', 'email', 'password', 'repeated_password']
        extra_kwargs = {
            'password': {'write_only': True},
            'id': {'read_only': True},
        }

    def validate(self, data):
        if data['password'] != data['repeated_password']:
            raise serializers.ValidationError({
                'password': 'Passwords do not match.'
            })

        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({
                'email': 'Email already exists.'
            })

        return data

    def create(self, validated_data):
        fullname = validated_data.pop('fullname')
        validated_data.pop('repeated_password')

        email = validated_data['email']
        password = validated_data['password']

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password
        )

        UserProfile.objects.create(
            user=user,
            fullname=fullname
        )

        return user


class CustomLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        try:
            user_data = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Ungültige Anfragedaten.")

        user = authenticate(
            username=user_data.username,
            password=password
        )

        if not user:
            raise serializers.ValidationError("Ungültige Anfragedaten.")

        data["user"] = user
        return data
