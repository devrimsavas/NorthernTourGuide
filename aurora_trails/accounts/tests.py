from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User


class RegisterApiTests(APITestCase):
    """Tests for self-registration: always a customer, unique email, strong password."""

    def setUp(self):
        self.url = reverse("register")

    def test_register_creates_customer_and_returns_tokens(self):
        """A new account is always a customer, even if another role is sent."""
        response = self.client.post(
            self.url,
            {
                "email": "alex@test.no",
                "first_name": "Alex",
                "last_name": "Smith",
                "password": "StrongPass2026",
                "role": "admin",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertNotIn("password", response.data["user"])

        user = User.objects.get(email="alex@test.no")
        self.assertEqual(user.role, User.Role.CUSTOMER)
        self.assertTrue(user.check_password("StrongPass2026"))

    def test_register_rejects_duplicate_email_ignoring_case(self):
        """An email that already exists cannot be registered again, regardless of case."""
        User.objects.create_user(username="alex", email="alex@test.no", password="StrongPass2026")

        response = self.client.post(
            self.url,
            {
                "email": "ALEX@test.no",
                "first_name": "Alex",
                "last_name": "Smith",
                "password": "StrongPass2026",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)

    def test_register_rejects_weak_password(self):
        """Django's password validators reject weak passwords."""
        response = self.client.post(
            self.url,
            {
                "email": "alex@test.no",
                "first_name": "Alex",
                "last_name": "Smith",
                "password": "12345678",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)


class MeApiTests(APITestCase):
    """Tests for the endpoint that returns the logged-in user."""

    def test_me_returns_the_current_user(self):
        """The endpoint returns the authenticated user's details and role."""
        guide = User.objects.create_user(
            username="kari", email="kari@test.no", password="StrongPass2026", role=User.Role.GUIDE
        )
        self.client.force_authenticate(user=guide)

        response = self.client.get(reverse("me"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "kari@test.no")
        self.assertEqual(response.data["role"], "guide")

    def test_me_requires_authentication(self):
        """Anonymous requests are rejected with 401."""
        response = self.client.get(reverse("me"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


