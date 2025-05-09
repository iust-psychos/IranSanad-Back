from rest_framework import status
from django.conf import settings
from django.contrib.auth import get_user_model
from model_bakery import baker
from datetime import timedelta
from django.utils import timezone
from authentication.models import SignupEmailVerification
import pytest

User = get_user_model()



@pytest.fixture
def base_auth_url():
    return f"/api/v{settings.VERSION}/auth/"


@pytest.mark.django_db
class TestUserLogin:
    def test_login_with_valid_username_and_password(self, api_client, base_auth_url):
        user = baker.make(User)
        user.set_password("password")
        user.save()
        data = {
            "username": user.username,
            "password": "password",
        }

        response = api_client.post(f"{base_auth_url}login/", data=data)
        
        assert response.status_code == status.HTTP_200_OK
        assert "tokens" in response.data

    def test_login_with_valid_email_and_password(self, api_client, base_auth_url):
        user = baker.make(User)
        user.set_password("password")
        user.save()
        data = {
            "email": user.email,
            "password": "password",
        }

        response = api_client.post(f"{base_auth_url}login/", data=data)
        
        assert response.status_code == status.HTTP_200_OK
        assert "tokens" in response.data

    def test_login_with_invalid_username_get400(self, api_client, base_auth_url):
        user = baker.make(User)
        user.set_password("password")
        user.save()
        data = {
            "username": "invalid_username",
            "password": "password",
        }

        response = api_client.post(f"{base_auth_url}login/", data=data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data

    def test_login_with_invalid_email_get400(self, api_client, base_auth_url):
        user = baker.make(User)
        user.set_password("password")
        user.save()
        data = {
            "email": "invalid_email@example.com",
            "password": "password",
        }

        response = api_client.post(f"{base_auth_url}login/", data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data


    def test_if_send_both_username_and_email_get400(self, api_client, base_auth_url):
        user = baker.make(User)
        user.set_password("password")
        user.save()
        data = {
            "username": user.username,
            "email": user.email,
            "password": "password",
        }

        response = api_client.post(f"{base_auth_url}login/", data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data

    def test_login_with_invalid_password_get400(self, api_client, base_auth_url):
        user = baker.make(User)
        user.set_password("password")
        user.save()
        data = {
            "username": user.username,
            "password": "invalid_password",
        }

        response = api_client.post(f"{base_auth_url}login/", data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data

    def test_login_with_no_username_or_email_get400(self, api_client, base_auth_url):
        user = baker.make(User)
        user.set_password("password")
        user.save()
        data = {
            "password": "password",
        }

        response = api_client.post(f"{base_auth_url}login/", data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data
    

    def test_login_with_no_password_get400(self, api_client, base_auth_url):
        user = baker.make(User)
        user.set_password("password")
        user.save()
        data = {
            "username": user.username,
        }

        response = api_client.post(f"{base_auth_url}login/", data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password" in response.data

    def test_login_with_no_username_email_and_password_get400(self, api_client, base_auth_url):
        user = baker.make(User)
        user.set_password("password")
        user.save()
        data = {}

        response = api_client.post(f"{base_auth_url}login/", data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password" in response.data



@pytest.mark.django_db
class TestUserSignup:
    def test_signup_with_valid_data(self, api_client, base_auth_url):
        data = {
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "StrongPassword123!",
            "password2": "StrongPassword123!",
            "phone_number": "+989123456789",
            "code": "12345",
        }

        verification = baker.make(SignupEmailVerification, email=data["email"], code=data["code"], is_verified=False, expire_at=timezone.now() + timedelta(minutes=10))


        response = api_client.post(f"{base_auth_url}register/", data=data)

        assert response.status_code == status.HTTP_201_CREATED
        assert "tokens" in response.data
        assert response.data["username"] == data["username"]
        assert response.data["email"] == data["email"]

    def test_signup_with_existing_email(self, api_client, base_auth_url):
        existing_user = baker.make(User, email="existing@example.com")
        data = {
            "username": "newuser",
            "email": existing_user.email,
            "password": "StrongPassword123!",
            "password2": "StrongPassword123!",
            "phone_number": "+989123456789",
            "code": "12345",
        }

        response = api_client.post(f"{base_auth_url}register/", data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_signup_with_existing_username(self, api_client, base_auth_url):
        existing_user = baker.make(User, username="existinguser")
        data = {
            "username": existing_user.username,
            "email": "newuser@example.com",
            "password": "StrongPassword123!",
            "password2": "StrongPassword123!",
            "phone_number": "+989123456789",
            "code": "12345",
        }

        response = api_client.post(f"{base_auth_url}register/", data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_signup_with_invalid_verification_code(self, api_client, base_auth_url):
        data = {
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "StrongPassword123!",
            "password2": "StrongPassword123!",
            "phone_number": "+989123456789",
            "code": "wrongcode",
        }

        verification = baker.make(SignupEmailVerification, email=data["email"], code="12345", is_verified=False, expire_at=timezone.now() + timedelta(minutes=10))

        response = api_client.post(f"{base_auth_url}register/", data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_signup_with_expired_verification_code(self, api_client, base_auth_url):
        data = {
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "StrongPassword123!",
            "password2": "StrongPassword123!",
            "phone_number": "+989123456789",
            "code": "12345",
        }

        verification = baker.make(SignupEmailVerification, email=data["email"], code=data["code"], is_verified=False, expire_at=timezone.now() - timedelta(minutes=10))

        response = api_client.post(f"{base_auth_url}register/", data=data)

        assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE

    def test_signup_with_mismatched_passwords(self, api_client, base_auth_url):
        data = {
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "StrongPassword123!",
            "password2": "DifferentPassword123!",
            "phone_number": "+989123456789",
            "code": "12345",
        }
        
        verification = baker.make(SignupEmailVerification, email=data["email"], code=data["code"], is_verified=False, expire_at=timezone.now() + timedelta(minutes=10))

        response = api_client.post(f"{base_auth_url}register/", data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


    def test_signup_with_missing_required_fields(self, api_client, base_auth_url):
        data = {
            "username": "",
            "email": "",
            "password": "",
            "password2": "",
            "phone_number": "",
            "code": "",
        }

        response = api_client.post(f"{base_auth_url}register/", data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "username" in response.data
        assert "email" in response.data
        assert "password" in response.data
        assert "code" in response.data