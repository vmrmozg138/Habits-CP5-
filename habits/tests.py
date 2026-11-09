from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from habits.services import get_next_execution, is_reminder_time, send_tg_message
from users.models import User
from habits.models import Habit, Reminder
from django.core.exceptions import ValidationError
from datetime import timedelta, datetime
from unittest.mock import patch, Mock
from habits.tasks import send_habit_reminder, create_habit_reminder, send_pending_reminders


'''тестирование модели Habit и ее ограничений'''

class HabitModelTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="habit_test@mail.ru",
            password="12345678"
        )

        self.habit = Habit.objects.create(
            name="Зарядка",
            owner=self.user,
            place="Дом",
            execute_at=timezone.now(),
            action="Делать зарядку",
            periodicity=1,
            execution_time=10,
        )

    def test_habit_creation(self):
        self.assertIsInstance(self.habit, Habit)
        self.assertEqual(str(self.habit), "Зарядка")
        self.assertEqual(self.habit.owner, self.user)

    def test_periodicity_min_value(self):
        with self.assertRaises(ValidationError):
            self.habit.periodicity = 0
            self.habit.full_clean()

    def test_periodicity_max_value(self):
        with self.assertRaises(ValidationError):
            self.habit.periodicity = 8
            self.habit.full_clean()

    def test_execution_time_min_value(self):
        with self.assertRaises(ValidationError):
            self.habit.execution_time = 0
            self.habit.full_clean()

    def test_execution_time_max_value(self):
        with self.assertRaises(ValidationError):
            self.habit.execution_time = 121
            self.habit.full_clean()

    def test_related_habit_and_remuneration(self):
        pleasant_habit = Habit.objects.create(
            name="Отдых",
            owner=self.user,
            place="Дом",
            execute_at=timezone.now(),
            action="Посмотреть фильм",
            is_pleasant=True,
            periodicity=1,
            execution_time=30,
        )
        self.habit.related_habit = pleasant_habit
        self.habit.remuneration = "получить награду"
        with self.assertRaises(ValidationError):
            self.habit.full_clean()

    def test_related_habit_not_pleasant(self):
        usual_habit = Habit.objects.create(
            name="Добавлять чеснок в еду",
            owner=self.user,
            place="Дом",
            execute_at=timezone.now(),
            action="Добавить чеснок в еду",
            is_pleasant=False,
            periodicity=1,
            execution_time=30,
        )
        self.habit.related_habit = usual_habit
        with self.assertRaises(ValidationError):
            self.habit.full_clean()

    def test_pleasant_habits_remuneration(self):
        pleasant_habit = Habit.objects.create(
            name="Отдых",
            owner=self.user,
            place="Дом",
            execute_at=timezone.now(),
            action="Посмотреть фильм",
            is_pleasant=True,
            periodicity=1,
            execution_time=30,
            remuneration = "Получение награды"
        )
        with self.assertRaises(ValidationError):
            pleasant_habit.full_clean()


    def test_pleasant_habits_related_habit(self):
        pleasant_habit = Habit.objects.create(
            name="Отдых",
            owner=self.user,
            place="Дом",
            execute_at=timezone.now(),
            action="Посмотреть фильм",
            is_pleasant=True,
            periodicity=1,
            execution_time=30,
            related_habit = self.habit,
        )
        with self.assertRaises(ValidationError):
            pleasant_habit.full_clean()

    def test_habit_self_related(self):
        self_related_habit = Habit.objects.create(
            name="Отдых",
            owner=self.user,
            place="Дом",
            execute_at=timezone.now(),
            action="Посмотреть фильм",
            is_pleasant=False,
            periodicity=1,
            execution_time=30,
        )
        self_related_habit.related_habit = self_related_habit
        with self.assertRaises(ValidationError):
            self_related_habit.full_clean()

    def test_habit_wrong_owner(self):
        second_user = User.objects.create_user(
            email="habit_test2@mail.ru",
            password="98765432"
        )

        habit = Habit.objects.create(
            name="Отдых",
            owner=second_user,
            place="Дом",
            execute_at=timezone.now(),
            action="Посмотреть фильм",
            is_pleasant=True,
            periodicity=1,
            execution_time=30,
        )
        self.habit.related_habit = habit
        with self.assertRaises(ValidationError):
            self.habit.full_clean()

'''тестирование модели Reminder и ее ограничений'''

class ReminderModelTestCase(TestCase):

    def setUp(self):
        self.now = timezone.now()

        self.user = User.objects.create_user(
            email="habit_test@mail.ru",
            password="12345678"
        )

        self.habit = Habit.objects.create(
            name="Зарядка",
            owner=self.user,
            place="Дом",
            execute_at=timezone.now(),
            action="Делать зарядку",
            periodicity=1,
            execution_time=10,
        )

        self.reminder = Reminder.objects.create(
            habit=self.habit,
            execution_at=self.now,
            reminder_at=self.now - timedelta(minutes=10)
        )

    def test_reminder_creation(self):
        self.assertIsInstance(self.reminder, Reminder)
        self.assertEqual(str(self.reminder), f"Зарядка (отправлено: False)")

    def test_reminder_str_sent_true(self):
        self.reminder.sent_at = self.now - timedelta(minutes=15)
        self.assertEqual(str(self.reminder), f"Зарядка (отправлено: True)")

    def test_reminder_unique_execution_at(self):
        test_reminder = Reminder(
            habit=self.habit,
            execution_at=self.now,
            reminder_at=self.now - timedelta(minutes=15)
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                test_reminder.save()

    def test_delete_reminders_after_habit_delete(self):
        habit_id = self.habit.pk
        self.habit.delete()

        self.assertEqual(
            Reminder.objects.filter(habit_id=habit_id).count(),
            0
        )

'''Тестирование services'''

class HabitServicesTestCase(TestCase):

    def setUp(self):
        self.now = timezone.now()

    def test_get_next_execution_future(self):
        execute_at = self.now + timedelta(hours=1)
        result = get_next_execution(
            execute_at=execute_at,
            periodicity=1,
            now=self.now
        )
        self.assertEqual(result, execute_at)

    def test_get_next_execution_past(self):
        execute_at = self.now - timedelta(hours=1)
        next_execution = execute_at + timedelta(days=1)
        result = get_next_execution(
            execute_at=execute_at,
            periodicity=1,
            now=self.now
        )
        self.assertEqual(result, next_execution)

    def test_get_next_execution_past_several_days(self):
        execute_at = self.now - timedelta(days=3)
        next_execution = self.now + timedelta(days=1)
        result = get_next_execution(
            execute_at=execute_at,
            periodicity=1,
            now=self.now
        )
        self.assertEqual(result, next_execution)

    def test_is_reminder_time_too_early(self):
         execute_at = self.now + timedelta(hours=1)
         result = is_reminder_time(execute_at=execute_at, periodicity=1, now=self.now)
         self.assertFalse(result)

    def test_is_reminder_time_true(self):
        execute_at = self.now + timedelta(minutes=7)
        result = is_reminder_time(execute_at=execute_at, periodicity=1, now=self.now)
        self.assertTrue(result)

    def test_is_reminder_time_too_late(self):
        execute_at = self.now + timedelta(minutes=4)
        result = is_reminder_time(execute_at=execute_at, periodicity=1, now=self.now)
        self.assertFalse(result)

    @patch('habits.services.requests.get')
    def test_send_tg_message(self, mock_get):
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"ok": True}
        mock_get.return_value = mock_resp

        result = send_tg_message(123, "test message")
        self.assertTrue(result)

    @patch('habits.services.requests.get')
    def test_send_tg_message_wrong_answer(self, mock_get):
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"ok": False}
        mock_get.return_value = mock_resp

        result = send_tg_message(123, "test message")
        self.assertFalse(result)

    @patch('habits.services.requests.get')
    def test_send_tg_message_wrong_status_code(self, mock_get):
        mock_resp = Mock()
        mock_resp.status_code = 400
        mock_resp.json.return_value = {"ok": True}
        mock_get.return_value = mock_resp

        result = send_tg_message(123, "test message")
        self.assertFalse(result)

'''тестирование tasks'''
class HabitTasksTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="tasks_test@mail.ru",
            password="12345678",
            tg_chat_id="123456789"
        )

        self.habit = Habit.objects.create(
            name="Зарядка",
            owner=self.user,
            place="Дом",
            execute_at=timezone.now(),
            action="Делать зарядку",
            periodicity=1,
            execution_time=10,
        )

    @patch('habits.tasks.send_tg_message')
    def test_send_habit_reminder(self, mock_send):
        mock_send.return_value = True
        result = send_habit_reminder(self.user.id)
        self.assertEqual(result, "Success")
        mock_send.assert_called_once_with(
            "123456789",
            "Внимание! Пора выполнять привычку"
        )

    @patch('habits.tasks.send_tg_message')
    def test_send_habit_reminder_user_without_chat_id(self, mock_send):
        test_user = User.objects.create_user(
            email="tasks_test1@mail.ru",
            password="246810",
        )
        result = send_habit_reminder(test_user.id)
        self.assertEqual(result, "No Telegram chat_id")
        mock_send.assert_not_called()

    @patch('habits.tasks.send_tg_message')
    def test_send_habit_reminder_error(self, mock_send):
        mock_send.return_value = False

        result = send_habit_reminder(self.user.id)

        self.assertEqual(result, "Error sending Telegram message")

    @patch('habits.tasks.timezone.now')
    def test_create_habit_reminder(self, mock_now):
        fixed_now = timezone.make_aware(
            datetime(2026, 11, 10, 15, 0)
        )
        mock_now.return_value = fixed_now
        self.habit.execute_at = fixed_now + timedelta(minutes=7)
        self.habit.save()
        create_habit_reminder()
        reminder = Reminder.objects.filter(habit=self.habit).first()

        self.assertIsNotNone(reminder)
        self.assertEqual(reminder.execution_at, self.habit.execute_at)
        self.assertEqual(
            reminder.reminder_at,
            fixed_now - timedelta(minutes=3)
        )
        create_habit_reminder()
        self.assertEqual(Reminder.objects.filter(habit=self.habit).count(), 1)

    @patch('habits.tasks.send_tg_message')
    def test_send_pending_reminders(self, mock_send):
        now = timezone.now()
        mock_send.return_value = True
        test_reminder = Reminder.objects.create(
            habit=self.habit,
            execution_at=now + timedelta(minutes=10),
            reminder_at=now
        )
        send_pending_reminders()
        test_reminder.refresh_from_db()
        self.assertIsNotNone(test_reminder.sent_at)
        mock_send.assert_called_once_with(
            self.user.tg_chat_id,
            f'Я буду {self.habit.action} в {test_reminder.execution_at} в {self.habit.place}'
        )

    @patch('habits.tasks.send_tg_message')
    def test_send_pending_reminders_without_chat_id(self, mock_send):
        test_user = User.objects.create_user(
            email="tasks_test2@mail.ru",
            password="246810",
        )
        test_habit = Habit.objects.create(
            name="Тест",
            owner=test_user,
            place="Тестовая локация",
            execute_at=timezone.now(),
            action="Делать тест",
            periodicity=1,
            execution_time=10,
        )
        test_reminder = Reminder.objects.create(
            habit=test_habit,
            execution_at=timezone.now(),
            reminder_at=timezone.now()-timedelta(minutes=10),
        )
        send_pending_reminders()
        self.assertIsNone(test_reminder.sent_at)
        mock_send.assert_not_called()

    @patch('habits.tasks.send_tg_message')
    def test_send_pending_reminders_error(self, mock_send):
        test_reminder = Reminder.objects.create(
            habit=self.habit,
            execution_at=timezone.now(),
            reminder_at=timezone.now() - timedelta(minutes=10),
        )
        mock_send.return_value = False
        send_pending_reminders()
        self.assertIsNone(test_reminder.sent_at)
        mock_send.assert_called_once()

























