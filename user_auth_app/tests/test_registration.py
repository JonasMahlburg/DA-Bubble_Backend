from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth.models import User
from user_auth_app.models import UserProfile 
import uuid 


class RegistrationTests(APITestCase):
    """
    Tests for successful user registration.
    """
    def setUp(self):
        self.client = APIClient()

    def test_post_registration_success(self):
        """
        Tests happy user registration with unique credentials.
        """
        unique_username = f"user_{uuid.uuid4().hex[:8]}"
        unique_email = f"email_{uuid.uuid4().hex[:8]}@example.com"
        data = {
            "username": unique_username,
            "email": unique_email,
            "password": "examplePassword123",
            "repeated_password": "examplePassword123",
        }
        url = 'http://127.0.0.1:8000/api/registration/'

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue('token' in response.data)
        self.assertEqual(User.objects.filter(email=unique_email).count(), 1)
        self.assertEqual(UserProfile.objects.filter(user__email=unique_email).count(), 1)


class NegativeRegistrationTests(APITestCase):
    """
    Tests for unhappy user registration scenarios.
    """
    def setUp(self):
        self.client = APIClient()
        self.existing_user_email = f"existing_{uuid.uuid4().hex[:8]}@mail.de"
        self.existing_user_username = f"existing_user_{uuid.uuid4().hex[:8]}"
        self.user = User.objects.create_user(
            username=self.existing_user_username,
            email=self.existing_user_email,
            password='newpassword123'
        )
        UserProfile.objects.create(user=self.user)
    
    def test_post_already_existing_user_data(self):
        """
        Tests registration with username and email that already exist.
        Should return HTTP 400 Bad Request.
        """
        data = {
            "username": self.existing_user_username,
            "email": self.existing_user_email,    
            "password": "newpassword123",
            "repeated_password": "newpassword123",
        }
        url = 'http://127.0.0.1:8000/api/registration/'

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn("already taken", str(response.data['error']))

    def test_duplicate_email_registration(self):
        """
        Tests registering the same email twice.
        The first should succeed, the second should fail with HTTP 400.
        """
        unique_username_1 = f"test_dup_user_1_{uuid.uuid4().hex[:8]}"
        unique_username_2 = f"test_dup_user_2_{uuid.uuid4().hex[:8]}"
        unique_email = f"duplicate_test_{uuid.uuid4().hex[:8]}@example.com"

        registration_data = {
            "username": unique_username_1,
            "email": unique_email,
            "password": "securepass123",
            "repeated_password": "securepass123",
        }
        url = 'http://127.0.0.1:8000/api/registration/'

        response1 = self.client.post(url, registration_data, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        registration_data_duplicate_email = registration_data.copy()
        registration_data_duplicate_email['username'] = unique_username_2

        response2 = self.client.post(url, registration_data_duplicate_email, format='json')
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response2.data)
        self.assertIn("This email is already taken", str(response2.data['error']))

    def test_duplicate_username_registration(self):
        """
        Tests registering the same username twice.
        The first should succeed, the second should fail with HTTP 400.
        """
        unique_username = f"test_dup_user_{uuid.uuid4().hex[:8]}"
        unique_email_1 = f"duplicate_test_email_1_{uuid.uuid4().hex[:8]}@example.com"
        unique_email_2 = f"duplicate_test_email_2_{uuid.uuid4().hex[:8]}@example.com"

        registration_data = {
            "username": unique_username,
            "email": unique_email_1,
            "password": "securepass123",
            "repeated_password": "securepass123",
        }
        url = 'http://127.0.0.1:8000/api/registration/'
        response1 = self.client.post(url, registration_data, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        registration_data_duplicate_username = registration_data.copy()
        registration_data_duplicate_username['email'] = unique_email_2

        response2 = self.client.post(url, registration_data_duplicate_username, format='json')
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response2.data)
        self.assertIn("This username is already taken", str(response2.data['error']))

    def test_passwords_do_not_match(self):
        """
        Tests registration when password and repeated_password do not match.
        Should return HTTP 400 Bad Request.
        """
        unique_username = f"user_nomatch_{uuid.uuid4().hex[:8]}"
        unique_email = f"email_nomatch_{uuid.uuid4().hex[:8]}@example.com"

        data = {
            "username": unique_username,
            "email": unique_email,
            "password": "password1",
            "repeated_password": "password2",
        }
        url = 'http://127.0.0.1:8000/api/registration/'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Passwords do not match')
