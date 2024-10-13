from django.test import TestCase

# Create your tests here.
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Profile


class AccountsTestCase(TestCase):
    def setUp(self):
        self.signup_url = reverse('accounts:account_signup')
        self.login_url = reverse('accounts:account_login')
        self.profile_url = reverse('accounts:account_profile')
        self.user = User.objects.create_user(username='testuser', email='testuser@example.com', password='password123')

    def test_signup_view(self):
        response = self.client.get(self.signup_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/signup.html')

    def test_user_signup(self):
        response = self.client.post(self.signup_url, {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'agency': 1,  # Assuming agency with ID 1 exists
            'password1': 'strongpassword123',
            'password2': 'strongpassword123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after successful signup
        self.assertTrue(User.objects.filter(username='newuser').exists())
        new_user = User.objects.get(username='newuser')
        self.assertTrue(hasattr(new_user, 'profile'))
        self.assertEqual(new_user.profile.agency.id, 1)

    def test_login_view(self):
        response = self.client.post(self.login_url, {
            'login': 'testuser@example.com',  # Allauth uses 'login' field for email
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after successful login
        self.assertTrue('_auth_user_id' in self.client.session)

    def test_profile_view_authenticated(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/profile.html')

    def test_profile_view_unauthenticated(self):
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login