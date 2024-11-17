# /workspace/shiftwise/accounts/tests.py

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse

from shifts.models import Shift, ShiftAssignment
from subscriptions.models import Plan, Subscription

from .models import Agency, Invitation, Profile


class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="password123"
        )
        self.group = Group.objects.create(name="Agency Staff")
        self.user.groups.add(self.group)
        self.agency = Agency.objects.create(name="Test Agency", email="agency@test.com")
        self.user.profile.agency = self.agency
        self.user.profile.save()

    def test_login_view(self):
        response = self.client.post(
            reverse("accounts:login_view"),
            {"username": "testuser", "password": "password123"},
        )
        self.assertRedirects(response, reverse("accounts:staff_dashboard"))
        self.assertTrue("_auth_user_id" in self.client.session)

    def test_invalid_login(self):
        response = self.client.post(
            reverse("accounts:login_view"),
            {"username": "testuser", "password": "wrongpassword"},
        )
        self.assertContains(response, "Invalid username or password.")
        self.assertFalse("_auth_user_id" in self.client.session)
