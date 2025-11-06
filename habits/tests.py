from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth.models import User
from .models import Habit
from datetime import time


class HabitAPITestCase(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="user1", password="pass1234")
        self.user2 = User.objects.create_user(username="user2", password="pass1234")

        self.client1 = APIClient()
        self.client1.force_authenticate(user=self.user1)

        self.client2 = APIClient()
        self.client2.force_authenticate(user=self.user2)

        self.pleasant_habit = Habit.objects.create(
            user=self.user1,
            place="Дома",
            time=time(9, 0),
            action="Принять ванну с пеной",
            is_pleasant=True,
            periodicity=1,
            duration_seconds=60,
            is_public=True,
        )

    def test_create_useful_habit_with_related_pleasant(self):
        url = reverse("habit-list")
        data = {
            "place": "Парк",
            "time": "18:00:00",
            "action": "Погулять вокруг квартала",
            "is_pleasant": False,
            "related_habit": self.pleasant_habit.id,
            "periodicity": 1,
            "duration_seconds": 120,
            "reward": "",
            "is_public": True,
        }
        response = self.client1.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        habit = Habit.objects.get(id=response.data["id"])
        self.assertEqual(habit.related_habit, self.pleasant_habit)
        self.assertFalse(habit.is_pleasant)

    def test_create_habit_with_both_related_and_reward_fails(self):
        url = reverse("habit-list")
        data = {
            "place": "Кафе",
            "time": "12:00:00",
            "action": "Встреча с друзьями",
            "is_pleasant": False,
            "related_habit": self.pleasant_habit.id,
            "reward": "Десерт",
            "periodicity": 1,
            "duration_seconds": 60,
            "is_public": False,
        }
        response = self.client1.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "Нельзя одновременно указывать связанную привычку и вознаграждение",
            str(response.data),
        )

    def test_pleasant_habit_cannot_have_reward_or_related(self):
        url = reverse("habit-list")
        data = {
            "place": "Дома",
            "time": "20:00:00",
            "action": "Принять ванну",
            "is_pleasant": True,
            "reward": "Чай",
            "related_habit": None,
            "periodicity": 1,
            "duration_seconds": 30,
            "is_public": False,
        }
        response = self.client1.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "У приятной привычки не может быть вознаграждения или связанной привычки",
            str(response.data),
        )

    def test_duration_seconds_greater_than_120_fails(self):
        url = reverse("habit-list")
        data = {
            "place": "Дома",
            "time": "08:00:00",
            "action": "Утренняя зарядка",
            "is_pleasant": False,
            "reward": "Кофе",
            "periodicity": 1,
            "duration_seconds": 121,
            "is_public": False,
        }
        response = self.client1.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "Время выполнения не должно превышать 120 секунд",
            str(response.data),
        )

    def test_user_cannot_access_others_private_habits(self):
        habit = Habit.objects.create(
            user=self.user1,
            place="Офис",
            time=time(10, 0),
            action="Проверить почту",
            is_pleasant=False,
            reward="Кофе",
            periodicity=1,
            duration_seconds=60,
            is_public=False,
        )
        url = reverse("habit-detail", args=[habit.id])
        response = self.client2.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_public_habits_list_accessible_without_auth(self):
        Habit.objects.create(
            user=self.user2,
            place="Парк",
            time=time(7, 0),
            action="Утренняя пробежка",
            is_pleasant=False,
            reward="Заряд бодрости",
            periodicity=1,
            duration_seconds=90,
            is_public=True,
        )
        url = reverse("habit-public-list")
        client = APIClient()
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data["results"]) >= 1)

    def test_pagination_returns_five_items_per_page(self):
        for i in range(7):
            Habit.objects.create(
                user=self.user1,
                place=f"Place {i}",
                time=time(9, 0),
                action=f"Action {i}",
                is_pleasant=False,
                reward="Reward",
                periodicity=1,
                duration_seconds=60,
                is_public=False,
            )
        url = reverse("habit-list")
        response = self.client1.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 5)
