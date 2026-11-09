from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.core.exceptions import ValidationError
from users.models import User


class Habit(models.Model):
    name = models.CharField(max_length=100, verbose_name="Имя/наименование")
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="habits",
        verbose_name="Владелец"
    )
    place = models.CharField(verbose_name="Место", max_length=255)
    execute_at = models.DateTimeField(verbose_name="Время выполнения")
    action = models.CharField(max_length=100, verbose_name="Действие")
    is_pleasant = models.BooleanField(
        default=False, verbose_name="Признак приятной привычки"
    )

    related_habit = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        verbose_name="Связанная привычка",
        related_name="habits_using_as_reward",
        null=True,
        blank=True,
    )
    periodicity = models.PositiveIntegerField(
        verbose_name="Периодичность в днях",
        validators=[
            MinValueValidator(1),
            MaxValueValidator(7),
        ],
    )

    remuneration = models.CharField(
        max_length=255,
        verbose_name="Вознаграждение",
        blank=True
    )
    execution_time = models.PositiveIntegerField(
        verbose_name="Время на выполнение",
        validators=[
            MinValueValidator(1),
            MaxValueValidator(120),
        ],
    )
    is_public = models.BooleanField(default=False, verbose_name="Признак публичности")

    def clean(self):
        """валидация - не должно быть заполнено одновременно и поле вознаграждения, и поле связанной привычки"""
        if self.related_habit and self.remuneration:
            raise ValidationError(
                "Ошибка! Нельзя заполнить одновременно и поле вознаграждения, и поле связанной привычки"
            )
        """валидация - связання привычка - только с признаком приятной привычки"""
        if self.related_habit and not self.related_habit.is_pleasant:
            raise ValidationError("Связанная привычка должна быть приятной привычкой")
        """валидация - у приятной привычки не может быть вознаграждения или связанной привычки"""
        if self.is_pleasant and (self.remuneration or self.related_habit):
            raise ValidationError(
                "У приятной привычки не может быть вознаграждения или связанной привычки"
            )
        """привычка не должна ссылаться на саму себя"""
        if self.related_habit and self.related_habit == self:
            raise ValidationError(
                "Привычка не может ссылаться сама на себя"
            )
        """связанная привычка должна принадлежать тому же владельцу"""
        if self.related_habit and self.related_habit.owner != self.owner:
            raise ValidationError(
                "Связанная привычка должна принадлежать тому же пользователю"
            )

    def __str__(self):
        return self.name

class Reminder(models.Model):
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, verbose_name="Привычка")
    execution_at = models.DateTimeField(verbose_name="Время выполнения")
    reminder_at = models.DateTimeField(verbose_name="Время отправки уведомления")

    sent_at = models.DateTimeField(verbose_name="Фактическое время отправки", null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["habit", "execution_at"],
                name="unique_habit_execution_reminder"
            )
        ]

    def __str__(self):
        return f"{self.habit.name} (отправлено: {self.sent_at is not None})"