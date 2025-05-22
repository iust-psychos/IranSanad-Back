import pytest
from rest_framework import status
from iransanad.settings import BASE_URL
from django.contrib.auth import get_user_model
from authentication.models import ProfileImage
from model_bakery import baker

User = get_user_model()


@pytest.fixture
def base_auth_url():
    return f"/{BASE_URL}/auth"


@pytest.fixture
def user():
    pass


@pytest.mark.django_db
class TestUserProfile:
    def test_patch_username_valid_username_return_200(self, api_client, base_auth_url):
        user = baker.make(User)
        user.username = "username1"
        api_client.force_authenticate(user=user)
        new_valid_username = "UserName2_@+-."
        data = {"username": new_valid_username}

        response = api_client.patch(f"{base_auth_url}/info/", data=data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == new_valid_username

    def test_patch_username_invalid_characters_return_400(
        self, api_client, base_auth_url
    ):
        user = baker.make(User)
        valid_username = "user1"
        user.username = valid_username
        api_client.force_authenticate(user=user)

        new_invalid_username = "User name ! #"
        data = {"username": new_invalid_username}
        response = api_client.patch(f"{base_auth_url}/info/", data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_patch_username_max_characters_return_400(self, api_client, base_auth_url):
        user = baker.make(User)
        user.username = "user1"
        api_client.force_authenticate(user=user)

        new_invalid_username = "a" * 170
        data = {"username": new_invalid_username}
        response = api_client.patch(f"{base_auth_url}/info/", data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_patch_username_duplicate_username_return_400(
        self, api_client, base_auth_url
    ):
        user1 = baker.make(User)
        user1.save()
        user2 = baker.make(User)
        api_client.force_authenticate(user=user2)
        data = {"username": user1.username}
        response = api_client.patch(f"{base_auth_url}/info/", data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_patch_valid_firstname_return_200(self, api_client, base_auth_url):
        user = baker.make(User)
        user.first_name = "Ali"
        api_client.force_authenticate(user=user)
        new_firstname = "Bahman"
        data = {"first_name": new_firstname}
        response = api_client.patch(f"{base_auth_url}/info/", data=data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == new_firstname

    def test_patch_empty_firstname_return_200(self, api_client, base_auth_url):
        user = baker.make(User)
        user.first_name = "Ali"
        api_client.force_authenticate(user=user)
        data = {"first_name": ""}
        response = api_client.patch(f"{base_auth_url}/info/", data=data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == ""

    def test_patch_firstname_max_character_return_400(self, api_client, base_auth_url):
        user = baker.make(User)
        api_client.force_authenticate(user=user)

        data = {"first_name": "a" * 160}
        response = api_client.patch(f"{base_auth_url}/info/", data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_patch_valid_lastname_return_200(self, api_client, base_auth_url):
        user = baker.make(User)
        user.last_name = "Shokri"
        api_client.force_authenticate(user=user)
        new_lastname = "Bahman"
        data = {"last_name": new_lastname}
        response = api_client.patch(f"{base_auth_url}/info/", data=data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["last_name"] == new_lastname

    def test_patch_empty_lastname_return_200(self, api_client, base_auth_url):
        user = baker.make(User)
        user.last_name = "Bakhtiari"
        api_client.force_authenticate(user=user)
        data = {"last_name": ""}
        response = api_client.patch(f"{base_auth_url}/info/", data=data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["last_name"] == ""

    def test_patch_lastname_max_character_return_400(self, api_client, base_auth_url):
        user = baker.make(User)
        api_client.force_authenticate(user=user)

        data = {"last_name": "a" * 160}
        response = api_client.patch(f"{base_auth_url}/info/", data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_patch_valid_phonenumber_return_200(self, api_client, base_auth_url):
        user = baker.make(User)
        api_client.force_authenticate(user=user)
        new_phonenumber1 = "+9891234567890"
        new_phonenumber2 = "9891234567890"
        data1 = {"phone_number": new_phonenumber1}
        data2 = {"phone_number": new_phonenumber2}
        response1 = api_client.patch(f"{base_auth_url}/info/", data=data1)
        response2 = api_client.patch(f"{base_auth_url}/info/", data=data2)
        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK

    def test_patch_invalid_phonenumber_return_400(self, api_client, base_auth_url):
        user = baker.make(User)
        api_client.force_authenticate(user=user)
        too_short_phonenumber = "+98987654321"
        too_long_phonenumber = "+9898765432198765"
        invalid_format_phonenumber = "a98123456789123"
        data1 = {"phone_number": too_short_phonenumber}
        data2 = {"phone_number": too_long_phonenumber}
        data3 = {"phone_number": invalid_format_phonenumber}
        response1 = api_client.patch(f"{base_auth_url}/info/", data=data1)
        response2 = api_client.patch(f"{base_auth_url}/info/", data=data2)
        response3 = api_client.patch(f"{base_auth_url}/info/", data=data3)
        assert response1.status_code == status.HTTP_400_BAD_REQUEST
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        assert response3.status_code == status.HTTP_400_BAD_REQUEST

    def test_patch_null_phonenumber_return_200(self, api_client, base_auth_url):
        user = baker.make(User)
        api_client.force_authenticate(user=user)
        data = {"phone_number": ""}
        response = api_client.patch(f"{base_auth_url}/info/", data=data)
        assert response.status_code == status.HTTP_200_OK

    def test_patch_valid_profileimage_return_200(self, api_client, base_auth_url):
        user = baker.make(User)
        api_client.force_authenticate(user=user)
        base64pic = "data:image/png;base64,iVBORw0KGgoAAA\
            ANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAAXNSR0IArs4\
                c6QAAAHRJREFUGFcBaQCW/wEPPt3/xXXzAP0uhwA+\
                    XqMA5jcCAAESurL/fzDlAAxBsgC+yJ0ATgs2A\
                        AH9QFz/X+7nAHNwNgB9ipIA9KC0AAFE+c\
                            j/e3S9APIYvQBqPxQAZUKtAAEP5yz\
                                /5SxKALmQvgAkS3wA7BfXAPhA\
                                    KsRsjXB5AAAAAElFTkSuQmCC"
        data = {"profile_image": base64pic}
        response = api_client.post(f"{base_auth_url}/profile/", data=data)
        # This status code seems wrong. Should be changed in future.
        assert response.status_code == status.HTTP_204_NO_CONTENT
