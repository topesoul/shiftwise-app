from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Subscription

User = get_user_model()


class SubscriptionTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.subscription = Subscription.objects.create(user=self.user, plan="pro")

    def test_user_with_active_subscription_can_access(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("shifts:shift_list"))
        self.assertEqual(response.status_code, 200)

    def test_user_without_subscription_cannot_access(self):
        self.client.logout()
        user2 = User.objects.create_user(username="newuser", password="newpass")
        self.client.login(username="newuser", password="newpass")
        response = self.client.get(reverse("shifts:shift_list"))
        self.assertEqual(response.status_code, 302)  # Redirects to subscription page
