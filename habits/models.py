from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

User = get_user_model()


class Habit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="habits")
    place = models.CharField(max_length=255)
    time = models.TimeField(help_text="Время, когда необходимо выполнять привычку")
    action = models.CharField(max_length=255)
    is_pleasant = models.BooleanField(
        default=False, help_text="Признак приятной привычки"
    )
    related_habit = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={"is_pleasant": True},
        related_name="related_to",
        help_text="Связанная приятная привычка (только для полезных привычек)",
    )
    periodicity = models.PositiveIntegerField(
        default=1, help_text="Периодичность в днях"
    )
    reward = models.CharField(max_length=255, blank=True, null=True)
    duration_seconds = models.PositiveIntegerField(
        help_text="Время на выполнение в секундах"
    )
    is_public = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.related_habit and self.reward:
            raise ValidationError(
                _("Нельзя одновременно указать связанную привычку и вознаграждение")
            )

        if self.duration_seconds > 120:
            raise ValidationError(_("Время выполнения не должно превышать 120 секунд"))

        if self.related_habit and not self.related_habit.is_pleasant:
            raise ValidationError(_("Связанная привычка должна быть приятной"))

        if self.is_pleasant and (self.reward or self.related_habit):
            raise ValidationError(
                _(
                    "У приятной привычки не может быть вознаграждения или связанной привычки"
                )
            )

        if self.periodicity < 1 or self.periodicity > 7:
            raise ValidationError(_("Периодичность должна быть от 1 до 7 дней"))

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.action} at {self.time} in {self.place} ({self.user.username})"
