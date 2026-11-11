from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "password",
            "phone_number",
            "city",
            "avatar",
        )
        extra_kwargs = {
            "password": {"write_only": True},
        }

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class TelegramChatIdSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ("tg_chat_id",)
