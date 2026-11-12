from rest_framework import serializers

from .models import Habit


class HabitFullSerializer(serializers.ModelSerializer):
    class Meta:
        model = Habit
        fields = "__all__"
        read_only_fields = ("owner",)

    def validate(self, attrs):
        related_habit = attrs.get(
            "related_habit", getattr(self.instance, "related_habit", None)
        )
        remuneration = attrs.get(
            "remuneration", getattr(self.instance, "remuneration", "")
        )
        is_pleasant = attrs.get(
            "is_pleasant", getattr(self.instance, "is_pleasant", False)
        )
        owner = self.instance.owner if self.instance else self.context["request"].user

        if related_habit and remuneration:
            raise serializers.ValidationError(
                "Нельзя одновременно заполнить вознаграждение и связанную привычку"
            )

        if related_habit and not related_habit.is_pleasant:
            raise serializers.ValidationError(
                "Связанная привычка должна быть приятной привычкой"
            )

        if is_pleasant and (remuneration or related_habit):
            raise serializers.ValidationError(
                "У приятной привычки не может быть вознаграждения или связанной привычки"
            )

        if related_habit and self.instance and related_habit.pk == self.instance.pk:
            raise serializers.ValidationError(
                "Привычка не может ссылаться сама на себя"
            )

        if related_habit and related_habit.owner != owner:
            raise serializers.ValidationError(
                "Связанная привычка должна принадлежать тому же пользователю"
            )

        return attrs
