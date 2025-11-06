from celery import shared_task
from django.utils import timezone
from .models import Habit
from django.conf import settings
import requests
import logging

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"


@shared_task
def send_habit_reminders():
    now = timezone.now()
    current_time = now.time()

    habits_to_remind = Habit.objects.filter(
        time__hour=current_time.hour,
        time__minute=current_time.minute,
    )

    for habit in habits_to_remind:
        user = habit.user
        chat_id = getattr(getattr(user, "profile", None), "telegram_chat_id", None)
        if not chat_id:
            logger.warning(f"User {user.username} has no telegram_chat_id")
            continue

        text = f"Напоминание: пора выполнить привычку - {habit.action} в {habit.place}."

        try:
            response = requests.post(
                TELEGRAM_API_URL,
                data={
                    "chat_id": chat_id,
                    "text": text,
                },
            )
            response.raise_for_status()
            logger.info(f"Sent reminder to user {user.username} for habit {habit.id}")
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения Telegram: {e}")
