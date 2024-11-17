# /workspace/shiftwise/subscriptions/tests.py

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Agency, Profile
from shifts.models import Shift
from subscriptions.models import Plan, Subscription


class UsageLimitTestCase(TestCase):
    def setUp(self):
        # Create user and assign to Agency Owners group
        self.user = User.objects.create_user(username="owner", password="pass")
        self.agency_owner_group, _ = Group.objects.get_or_create(name="Agency Owners")
        self.user.groups.add(self.agency_owner_group)
        self.agency = Agency.objects.create(
            name="Test Agency", email="agency@example.com"
        )
        self.profile = Profile.objects.create(user=self.user, agency=self.agency)

        # Create plans
        self.basic_plan = Plan.objects.create(
            name="Basic",
            billing_cycle="monthly",
            description="Basic Plan",
            stripe_product_id="prod_basic",
            stripe_price_id="price_basic_monthly",
            price=29.00,
            notifications_enabled=True,
            advanced_reporting=False,
            priority_support=False,
            shift_management=True,
            staff_performance=False,
            custom_integrations=False,
            is_active=True,
            shift_limit=10,
        )
        self.pro_plan = Plan.objects.create(
            name="Pro",
            billing_cycle="monthly",
            description="Pro Plan",
            stripe_product_id="prod_pro",
            stripe_price_id="price_pro_monthly",
            price=49.00,
            notifications_enabled=True,
            advanced_reporting=True,
            priority_support=True,
            shift_management=True,
            staff_performance=True,
            custom_integrations=True,
            is_active=True,
            shift_limit=50,
        )

        # Assign subscription to basic_plan
        self.subscription = Subscription.objects.create(
            agency=self.agency,
            plan=self.basic_plan,
            stripe_subscription_id="sub_basic",
            is_active=True,
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30),
        )

    def test_needs_upgrade_flag_when_shift_limit_reached(self):
        # Create shifts equal to shift_limit
        for i in range(self.basic_plan.shift_limit):
            Shift.objects.create(
                name=f"Shift {i+1}",
                shift_date=timezone.now().date() + timezone.timedelta(days=i),
                start_time=timezone.now().time(),
                end_time=(timezone.now() + timezone.timedelta(hours=4)).time(),
                capacity=1,
                agency=self.agency,
                hourly_rate=15.00,
            )

        # Fetch the subscription home page
        self.client.login(username="owner", password="pass")
        response = self.client.get(reverse("subscriptions:subscription_home"))
        self.assertEqual(response.status_code, 200)

        # Check if 'needs_upgrade' is True
        self.assertTrue(response.context["needs_upgrade"])

    def test_needs_upgrade_flag_when_under_shift_limit(self):
        # Create fewer shifts than shift_limit
        for i in range(self.basic_plan.shift_limit - 1):
            Shift.objects.create(
                name=f"Shift {i+1}",
                shift_date=timezone.now().date() + timezone.timedelta(days=i),
                start_time=timezone.now().time(),
                end_time=(timezone.now() + timezone.timedelta(hours=4)).time(),
                capacity=1,
                agency=self.agency,
                hourly_rate=15.00,
            )

        # Fetch the subscription home page
        self.client.login(username="owner", password="pass")
        response = self.client.get(reverse("subscriptions:subscription_home"))
        self.assertEqual(response.status_code, 200)

        # Check if 'needs_upgrade' is False
        self.assertFalse(response.context["needs_upgrade"])
