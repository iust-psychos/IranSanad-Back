import pytest
from rest_framework import status
from django.contrib.auth import get_user_model
from model_bakery import baker
from datetime import timedelta
from django.utils import timezone
from authentication.models import ForgetPasswordVerification

User = get_user_model()

@pytest.fixture
def base_auth_url():
    return "/api/v1/auth/"

@pytest.mark.django_db
class TestUserPasswordManagement:
    def test_change_password_with_valid_data(self, api_client, base_auth_url):
        user = baker.make(User)
        user.set_password("old_password")
        user.save()
        api_client.force_authenticate(user=user)

        data = {
            "old_password": "old_password",
            "new_password": "NewPassword123!",
            "new_password2": "NewPassword123!",
        }

        response = api_client.post(f"{base_auth_url}change_password/", data=data)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        user.refresh_from_db()
        assert user.check_password("NewPassword123!")

    def test_change_password_with_invalid_old_password(self, api_client, base_auth_url):
        user = baker.make(User)
        user.set_password("old_password")
        user.save()
        api_client.force_authenticate(user=user)

        data = {
            "old_password": "wrong_password",
            "new_password": "NewPassword123!",
            "new_password2": "NewPassword123!",
        }

        response = api_client.post(f"{base_auth_url}change_password/", data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_change_password_with_mismatched_new_passwords(self, api_client, base_auth_url):
        user = baker.make(User)
        user.set_password("old_password")
        user.save()
        api_client.force_authenticate(user=user)

        data = {
            "old_password": "old_password",
            "new_password": "NewPassword123!",
            "new_password2": "DifferentPassword123!",
        }

        response = api_client.post(f"{base_auth_url}change_password/", data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_change_password_unauthenticated(self, api_client, base_auth_url):
        data = {
            "old_password": "old_password",
            "new_password": "NewPassword123!",
            "new_password2": "NewPassword123!",
        }

        response = api_client.post(f"{base_auth_url}change_password/", data=data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_forget_password_with_valid_email(self, api_client, base_auth_url):
        user = baker.make(User, email="testuser@example.com")

        data = {
            "email": "testuser@example.com",
        }

        response = api_client.post(f"{base_auth_url}verification/forget_password/", data=data)

        assert response.status_code == status.HTTP_200_OK
        assert "message" in response.data

    def test_forget_password_with_invalid_email(self, api_client, base_auth_url):
        data = {
            "email": "nonexistent@example.com",
        }

        response = api_client.post(f"{base_auth_url}verification/forget_password/", data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data

    def test_forget_password_verification_with_valid_data(self, api_client, base_auth_url):
        user = baker.make(User, email="testuser@example.com")
        verification = baker.make(
            ForgetPasswordVerification,
            user=user,
            code="12345",
            expire_at=timezone.now() + timedelta(minutes=10),
        )

        data = {
            "email": "testuser@example.com",
            "code": "12345",
            "new_password": "NewPassword123!",
            "new_password2": "NewPassword123!",
        }

        response = api_client.post(f"{base_auth_url}verification/forget_password_verify/", data=data)

        assert response.status_code == status.HTTP_201_CREATED
        user.refresh_from_db()
        assert user.check_password("NewPassword123!")

    def test_forget_password_verification_with_invalid_code(self, api_client, base_auth_url):
        user = baker.make(User, email="testuser@example.com")
        verification = baker.make(
            ForgetPasswordVerification,
            user=user,
            code="12345",
            expire_at=timezone.now() + timedelta(minutes=10),
        )

        data = {
            "email": "testuser@example.com",
            "code": "wrongcode",
            "new_password": "NewPassword123!",
            "new_password2": "NewPassword123!",
        }

        response = api_client.post(f"{base_auth_url}verification/forget_password_verify/", data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "code" in response.data

    def test_forget_password_verification_with_expired_code(self, api_client, base_auth_url):
        user = baker.make(User, email="testuser@example.com")
        verification = baker.make(
            ForgetPasswordVerification,
            user=user,
            code="12345",
            expire_at=timezone.now() - timedelta(minutes=10),
        )

        data = {
            "email": "testuser@example.com",
            "code": "12345",
            "new_password": "NewPassword123!",
            "new_password2": "NewPassword123!",
        }

        response = api_client.post(f"{base_auth_url}verification/forget_password_verify/", data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "code" in response.data

    def test_forget_password_verification_with_mismatched_passwords(self, api_client, base_auth_url):
        user = baker.make(User, email="testuser@example.com")
        verification = baker.make(
            ForgetPasswordVerification,
            user=user,
            code="12345",
            expire_at=timezone.now() + timedelta(minutes=10),
        )

        data = {
            "email": "testuser@example.com",
            "code": "12345",
            "new_password": "NewPassword123!",
            "new_password2": "DifferentPassword123!",
        }

        response = api_client.post(f"{base_auth_url}verification/forget_password_verify/", data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "new_password2" in response.data