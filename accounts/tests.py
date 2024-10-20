# accounts/tests.py

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Profile
from shifts.models import Agency
from .forms import CustomSignupForm

class CustomSignupFormTests(TestCase):
    def setUp(self):
        self.agency = Agency.objects.create(
            name='Test Agency',
            postcode='NW1 6XE',
            address_line1='123 Baker Street',
            city='London',
            email='agency@test.com'
        )

    def test_signup_form_valid_data(self):
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'StrongPassw0rd!',
            'password2': 'StrongPassw0rd!',
            'agency': self.agency.id
        }
        form = CustomSignupForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_signup_form_missing_fields(self):
        form_data = {
            'username': '',
            'email': '',
            'password1': '',
            'password2': '',
            'agency': ''
        }
        form = CustomSignupForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
        self.assertIn('email', form.errors)
        self.assertIn('password1', form.errors)
        self.assertIn('agency', form.errors)

    def test_signup_form_password_mismatch(self):
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'StrongPassw0rd!',
            'password2': 'DifferentPassw0rd!',
            'agency': self.agency.id
        }
        form = CustomSignupForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

class AccountViewsTests(TestCase):
    def setUp(self):
        self.agency = Agency.objects.create(
            name='Test Agency',
            postcode='NW1 6XE',
            address_line1='123 Baker Street',
            city='London',
            email='agency@test.com'
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password123'
        )
        self.user.profile.agency = self.agency
        self.user.profile.save()
        self.client.login(username='testuser', password='password123')

    def test_profile_view_get(self):
        response = self.client.get(reverse('accounts:account_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/profile.html')
        self.assertContains(response, 'testuser')

    def test_profile_view_post(self):
        response = self.client.post(reverse('accounts:account_profile'), {
            'first_name': 'Updated',
            'last_name': 'User',
            'email': 'updated@example.com'
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.email, 'updated@example.com')

    def test_profile_view_unauthenticated(self):
        self.client.logout()
        response = self.client.get(reverse('accounts:account_profile'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"{reverse('account_login')}?next={reverse('accounts:account_profile')}")
