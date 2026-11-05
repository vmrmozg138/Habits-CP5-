from rest_framework import serializers

from .models import Habit

class HabitFullSerializer(serializers.ModelSerializer):
    class Meta:
        model = Habit
        fields = '__all__'
        read_only_fields = ('owner',)