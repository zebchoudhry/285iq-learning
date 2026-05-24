"""Tests for users app - authentication and profile."""
import pytest
pytestmark = pytest.mark.django_db

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from .models import UserProfile

User = get_user_model()


class AuthAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = '/api/users/auth/register/'
        self.login_url = '/api/users/auth/login/'
        self.logout_url = '/api/users/auth/logout/'
        self.current_user_url = '/api/users/auth/current-user/'

    def test_register_success(self):
        response = self.client.post(
            self.register_url,
            data={
                'username': 'testuser',
                'email': 'test@example.com',
                'password': 'SecurePass123!',
                'password_confirm': 'SecurePass123!',
            },
            content_type='application/json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.json())
        self.assertEqual(response.json()['user']['username'], 'testuser')
        self.assertTrue(User.objects.filter(username='testuser').exists())
        self.assertTrue(UserProfile.objects.filter(student__username='testuser').exists())

    def test_register_password_mismatch(self):
        response = self.client.post(
            self.register_url,
            data={
                'username': 'testuser2',
                'email': 'test2@example.com',
                'password': 'SecurePass123!',
                'password_confirm': 'DifferentPass!',
            },
            content_type='application/json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        User.objects.create_user(username='logintest', email='login@test.com', password='TestPass123!')
        response = self.client.post(
            self.login_url,
            data={'username': 'logintest', 'password': 'TestPass123!'},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.json())

    def test_login_invalid_password(self):
        User.objects.create_user(username='logintest2', email='login2@test.com', password='TestPass123!')
        response = self.client.post(
            self.login_url,
            data={'username': 'logintest2', 'password': 'WrongPassword'},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_current_user_requires_auth(self):
        response = self.client.get(self.current_user_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
