from django.db import IntegrityError, transaction
from django.test import TestCase

from users.models import User


class UserModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="testpassword123"
        )

    def test_user_creation(self):
        self.assertIsInstance(self.user, User)
        self.assertEqual(self.user.email, "test@example.com")

    def test_user_password(self):
        self.assertNotEqual(self.user.password, "testpassword123")
        self.assertTrue(self.user.check_password("testpassword123"))

    def test_user_without_email(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password="123456")

    def test_user_without_password(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email="test@mail.ru", password="")

    def test_user_email_unique(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                User.objects.create_user(email="test@example.com", password="987654321")
