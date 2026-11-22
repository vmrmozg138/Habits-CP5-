from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from users.models import User

from .models import Habit, Reminder
from .services import get_next_execution, is_reminder_time, send_tg_message


@shared_task
def send_habit_reminder(user_id: int):
    user = User.objects.get(pk=user_id)
    chat_id = user.tg_chat_id
    message = "Внимание! Пора выполнять привычку"
    if chat_id:
        status = send_tg_message(chat_id, message)

        if status:
            return "Success"

        return "Error sending Telegram message"
    return "No Telegram chat_id"


@shared_task
def create_habit_reminder():
    now = timezone.now()
    habits = Habit.objects.all()
    for habit in habits:
        if is_reminder_time(habit.execute_at, habit.periodicity, now):
            execution_at = get_next_execution(habit.execute_at, habit.periodicity, now)
            reminder_at = execution_at - timedelta(minutes=10)
            Reminder.objects.get_or_create(
                habit=habit,
                execution_at=execution_at,
                defaults={
                    "reminder_at": reminder_at,
                },
            )


@shared_task
def send_pending_reminders():
    now = timezone.now()

    reminders = Reminder.objects.filter(sent_at__isnull=True, reminder_at__lte=now)

    for reminder in reminders:
        habit = reminder.habit
        tg_chat_id = habit.owner.tg_chat_id
        if tg_chat_id:
            message = f"Я буду {habit.action} в {reminder.execution_at} в {habit.place}"
            if send_tg_message(tg_chat_id, message):
                reminder.sent_at = timezone.now()
                reminder.save(update_fields=["sent_at"])
