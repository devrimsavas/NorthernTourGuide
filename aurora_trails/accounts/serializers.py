from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "password"]
        extra_kwargs = {
            "first_name": {"required": True},
            "last_name": {"required": True},
        }

    def validate_email(self, value):
        value = value.lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data["email"],
            role=User.Role.CUSTOMER,
            **validated_data,
        )

class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "role"]
        read_only_fields = fields


class GuideSerializer(serializers.ModelSerializer):
    bio = serializers.CharField(source="guide_profile.bio", read_only=True)
    languages = serializers.CharField(source="guide_profile.languages", read_only=True)
    years_of_experience = serializers.IntegerField(
        source="guide_profile.years_of_experience", read_only=True
    )
    base_location = serializers.CharField(
        source="guide_profile.base_location.name", read_only=True
    )
    photo=serializers.ImageField(source="guide_profile.photo",read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "bio",
            "languages",
            "years_of_experience",
            "base_location",
            "photo"
        ]