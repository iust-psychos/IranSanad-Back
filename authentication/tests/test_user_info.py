import pytest
from rest_framework import status
from django.contrib.auth import get_user_model
from model_bakery import baker

User = get_user_model()


@pytest.fixture
def base_auth_url():
    return "/api/v1/auth/"


@pytest.mark.django_db
class TestUserInfo:
    def test_get_user_info_authenticated(self, api_client, base_auth_url):
        user = baker.make(User)
        api_client.force_authenticate(user=user)

        response = api_client.get(f"{base_auth_url}info/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == user.username
        assert response.data["email"] == user.email
        assert response.data["phone_number"] == user.phone_number

    def test_get_user_info_unauthenticated(self, api_client, base_auth_url):
        response = api_client.get(f"{base_auth_url}info/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.data

    def test_update_user_info_with_put(self, api_client, base_auth_url):
        user = baker.make(User, first_name="OldName", last_name="OldLastName")
        api_client.force_authenticate(user=user)

        data = {
            "first_name": "NewName",
            "last_name": "NewLastName",
        }

        response = api_client.put(f"{base_auth_url}info/", data=data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == data["first_name"]
        assert response.data["last_name"] == data["last_name"]

        user.refresh_from_db()
        assert user.first_name == data["first_name"]
        assert user.last_name == data["last_name"]

    def test_partial_update_user_info_with_patch(self, api_client, base_auth_url):
        user = baker.make(User, first_name="OldName", last_name="OldLastName")
        api_client.force_authenticate(user=user)

        data = {
            "first_name": "NewName",
        }

        response = api_client.patch(f"{base_auth_url}info/", data=data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == data["first_name"]
        assert response.data["last_name"] == user.last_name

        user.refresh_from_db()
        assert user.first_name == data["first_name"]
        assert user.last_name == "OldLastName"

    def test_update_user_info_with_invalid_data(self, api_client, base_auth_url):
        user = baker.make(User)
        api_client.force_authenticate(user=user)

        data = {
            "email": "invalid-email",
        }

        response = api_client.put(f"{base_auth_url}info/", data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data

    def test_partial_update_user_info_with_invalid_data(self, api_client, base_auth_url):
        user = baker.make(User)
        api_client.force_authenticate(user=user)

        data = {
            "email": "invalid-email",
        }

        response = api_client.patch(f"{base_auth_url}info/", data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data

    def test_update_user_info_unauthenticated(self, api_client, base_auth_url):
        data = {
            "first_name": "NewName",
        }

        response = api_client.put(f"{base_auth_url}info/", data=data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.data

    def test_partial_update_user_info_unauthenticated(self, api_client, base_auth_url):
        data = {
            "first_name": "NewName",
        }

        response = api_client.patch(f"{base_auth_url}info/", data=data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.data
        
