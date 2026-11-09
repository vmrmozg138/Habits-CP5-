from datetime import timedelta
import requests
from  config import settings
from .models import Habit, Reminder


def send_tg_message(chat_id, message):
    params = {
        'chat_id': chat_id,
        'text': message
    }

    response = requests.get(
        f'{settings.TG_URL}{settings.TG_BOT_TOKEN}/sendMessage',
        params=params,
        timeout=10
    )
    '''
    print(response.status_code)
    print(response.json())'''
    data = response.json()

    return response.status_code == 200 and data.get('ok') is True


def get_next_execution(execute_at, periodicity, now):
    next_execution = execute_at
    if execute_at <= now:
        while next_execution <= now:
            next_execution += timedelta(days=periodicity)

    return next_execution


def is_reminder_time(execute_at, periodicity, now):
    next_execution = get_next_execution(execute_at, periodicity, now)
    reminder_at = next_execution - timedelta(minutes=10)

    return reminder_at <= now < reminder_at + timedelta(minutes=5)
