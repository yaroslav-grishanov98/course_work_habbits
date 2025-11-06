from rest_framework import serializers
from .models import Habit


class HabitSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Habit
        fields = [
            "id",
            "user",
            "place",
            "time",
            "action",
            "is_pleasant",
            "related_habit",
            "periodicity",
            "reward",
            "duration_seconds",
            "is_public",
        ]

    def validate(self, data):
        related_habit = data.get("related_habit")
        reward = data.get("reward")
        is_pleasant = data.get("is_pleasant", False)
        periodicity = data.get("periodicity", 1)
        duration_seconds = data.get("duration_seconds")

        if related_habit and reward:
            raise serializers.ValidationError(
                "Нельзя одновременно указывать связанную привычку и вознаграждение."
            )

        if duration_seconds and duration_seconds > 120:
            raise serializers.ValidationError(
                "Время выполнения не должно превышать 120 секунд."
            )

        if related_habit and not related_habit.is_pleasant:
            raise serializers.ValidationError(
                "Связанная привычка должна быть приятной."
            )

        if is_pleasant and (reward or related_habit):
            raise serializers.ValidationError(
                "У приятной привычки не может быть вознаграждения или связанной привычки."
            )

        if periodicity < 1 or periodicity > 7:
            raise serializers.ValidationError(
                "Периодичность должна быть от 1 до 7 дней."
            )

        return data
