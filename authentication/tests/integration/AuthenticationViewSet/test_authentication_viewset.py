import pytest
from rest_framework import status
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.conf import settings
from model_bakery import baker
from authentication.models import SignupEmailVerification
from authentication.views import AuthenticationViewSet
from datetime import timedelta
from django.utils import timezone

User = get_user_model()


@pytest.fixture
def base_auth_url():
    return f"/api/v{settings.VERSION}/auth/"


@pytest.mark.django_db
class TestInfoEndpoint:
    def test_get_unauthenticated_user_info_return401(self, api_client, base_auth_url):
        response = api_client.get(f"{base_auth_url}info/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.data

    def test_get_authenticated_user_info_return200(self, api_client, base_auth_url):
        user = baker.make(User)
        api_client.force_authenticate(user=user)

        response = api_client.get(f"{base_auth_url}info/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == user.username
        assert response.data["email"] == user.email
        assert response.data["phone_number"] == user.phone_number

    def test_partial_update_unauthenticated_user_info_return401(
        self, api_client, base_auth_url
    ):
        old_first_name = "old first name"
        new_first_name = "new first name"

        user = baker.make(User, first_name=old_first_name)
        user_old_first_name = user.first_name
        data = {
            "first_name": new_first_name,
        }

        response1 = api_client.patch(f"{base_auth_url}info/", data=data)
        response2 = api_client.put(f"{base_auth_url}info/", data=data)

        assert User.objects.count() == 1
        assert old_first_name != new_first_name
        assert response1.status_code == status.HTTP_401_UNAUTHORIZED
        assert response2.status_code == status.HTTP_401_UNAUTHORIZED
        user.refresh_from_db()
        # To make sure nothing is saved in database
        assert user_old_first_name == user.first_name

    def test_patch_username_valid_username_return200(self, api_client, base_auth_url):
        user = baker.make(User, username="username1")
        api_client.force_authenticate(user=user)
        new_valid_username = "UserName2_@+-."
        data = {"username": new_valid_username}

        response = api_client.patch(f"{base_auth_url}info/", data=data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == new_valid_username
        user.refresh_from_db()
        assert user.username == new_valid_username

    def test_patch_username_invalid_characters_return_400(
        self, api_client, base_auth_url
    ):
        user = baker.make(User, username="user1")
        api_client.force_authenticate(user=user)

        new_invalid_username = "User name ! #"
        data = {"username": new_invalid_username}
        response = api_client.patch(f"{base_auth_url}info/", data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        user.refresh_from_db()
        assert user.username != new_invalid_username

    def test_patch_username_max_characters_return_400(self, api_client, base_auth_url):
        user = baker.make(User, username="user1")
        api_client.force_authenticate(user=user)

        new_invalid_username = "a" * 170
        data = {"username": new_invalid_username}
        response = api_client.patch(f"{base_auth_url}info/", data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        user.refresh_from_db()
        assert user.username != new_invalid_username

    def test_patch_username_duplicate_username_return_400(
        self, api_client, base_auth_url
    ):
        user1, user2 = baker.make(User, _quantity=2)
        api_client.force_authenticate(user=user2)
        data = {"username": user1.username}
        response = api_client.patch(f"{base_auth_url}info/", data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        user2.refresh_from_db()
        assert user2.username != user1.username

    def test_patch_valid_firstname_return_200(self, api_client, base_auth_url):
        user = baker.make(User, first_name="Ali")
        api_client.force_authenticate(user=user)
        new_firstname = "Bahman"
        data = {"first_name": new_firstname}
        response = api_client.patch(f"{base_auth_url}info/", data=data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == new_firstname
        user.refresh_from_db()
        assert user.first_name == new_firstname

    def test_patch_empty_firstname_return_200(self, api_client, base_auth_url):
        user = baker.make(User, first_name="Ali")
        api_client.force_authenticate(user=user)
        data = {"first_name": ""}
        response = api_client.patch(f"{base_auth_url}info/", data=data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == ""
        user.refresh_from_db()
        assert user.first_name == ""

    def test_patch_firstname_max_character_return_400(self, api_client, base_auth_url):
        user = baker.make(User)
        user_first_name = user.first_name
        api_client.force_authenticate(user=user)

        data = {"first_name": "a" * 160}
        response = api_client.patch(f"{base_auth_url}info/", data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        user.refresh_from_db()
        assert user.first_name == user_first_name

    def test_patch_valid_lastname_return_200(self, api_client, base_auth_url):
        user = baker.make(User, last_name="Shokri")
        api_client.force_authenticate(user=user)
        new_lastname = "Bahman"
        data = {"last_name": new_lastname}
        response = api_client.patch(f"{base_auth_url}info/", data=data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["last_name"] == new_lastname
        user.refresh_from_db()
        assert user.last_name == new_lastname

    def test_patch_empty_lastname_return_200(self, api_client, base_auth_url):
        user = baker.make(User, last_name="Bakhtiari")
        api_client.force_authenticate(user=user)
        data = {"last_name": ""}
        response = api_client.patch(f"{base_auth_url}info/", data=data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["last_name"] == ""
        user.refresh_from_db()
        assert user.last_name == ""

    def test_patch_lastname_max_character_return_400(self, api_client, base_auth_url):
        user = baker.make(User)
        user_lastname = user.last_name
        api_client.force_authenticate(user=user)

        data = {"last_name": "a" * 160}
        response = api_client.patch(f"{base_auth_url}info/", data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        user.refresh_from_db()
        assert user.last_name == user_lastname

    def test_patch_valid_phonenumber_return_200(self, api_client, base_auth_url):
        user = baker.make(User)
        api_client.force_authenticate(user=user)
        new_phonenumber1 = "+9891234567890"
        new_phonenumber2 = "9891234567890"
        data1 = {"phone_number": new_phonenumber1}
        data2 = {"phone_number": new_phonenumber2}
        response1 = api_client.patch(f"{base_auth_url}info/", data=data1)
        user.refresh_from_db()
        assert user.phone_number == new_phonenumber1
        response2 = api_client.patch(f"{base_auth_url}info/", data=data2)
        user.refresh_from_db()
        assert user.phone_number == new_phonenumber2
        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK

    def test_patch_invalid_phonenumber_return_400(self, api_client, base_auth_url):
        user = baker.make(User)
        api_client.force_authenticate(user=user)
        init_phone_number = user.phone_number
        too_short_phonenumber = "+98987654321"
        too_long_phonenumber = "+9898765432198765"
        invalid_format_phonenumber = "a98123456789123"
        data1 = {"phone_number": too_short_phonenumber}
        data2 = {"phone_number": too_long_phonenumber}
        data3 = {"phone_number": invalid_format_phonenumber}
        response1 = api_client.patch(f"{base_auth_url}info/", data=data1)
        response2 = api_client.patch(f"{base_auth_url}info/", data=data2)
        response3 = api_client.patch(f"{base_auth_url}info/", data=data3)
        assert response1.status_code == status.HTTP_400_BAD_REQUEST
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        assert response3.status_code == status.HTTP_400_BAD_REQUEST
        user.refresh_from_db()
        assert user.phone_number == init_phone_number

    def test_patch_null_phonenumber_return_200(self, api_client, base_auth_url):
        user = baker.make(User)
        api_client.force_authenticate(user=user)
        data = {"phone_number": ""}
        response = api_client.patch(f"{base_auth_url}info/", data=data)
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestProfileEndpoint:
    def test_post_valid_profileimage_return_200(self, api_client, base_auth_url):
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
        response = api_client.post(f"{base_auth_url}profile/", data=data)
        # This status code seems wrong. Should be changed in future.
        assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
class TestRegisterEndpoint:
    def test_signup_with_valid_data(self, api_client, base_auth_url):
        data = {
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "StrongPassword123!",
            "password2": "StrongPassword123!",
            "phone_number": "+989123456789",
            "code": "12345",
        }

        verification = baker.make(
            SignupEmailVerification,
            email=data["email"],
            code=data["code"],
            is_verified=False,
            expire_at=timezone.now() + timedelta(minutes=10),
        )

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

        verification = baker.make(
            SignupEmailVerification,
            email=data["email"],
            code="12345",
            is_verified=False,
            expire_at=timezone.now() + timedelta(minutes=10),
        )

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

        verification = baker.make(
            SignupEmailVerification,
            email=data["email"],
            code=data["code"],
            is_verified=False,
            expire_at=timezone.now() - timedelta(minutes=10),
        )

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

        verification = baker.make(
            SignupEmailVerification,
            email=data["email"],
            code=data["code"],
            is_verified=False,
            expire_at=timezone.now() + timedelta(minutes=10),
        )

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


@pytest.mark.django_db
class TestLoginEndpoint:
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

    def test_login_with_no_username_email_and_password_get400(
        self, api_client, base_auth_url
    ):
        user = baker.make(User)
        user.set_password("password")
        user.save()
        data = {}

        response = api_client.post(f"{base_auth_url}login/", data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password" in response.data


@pytest.mark.django_db
class TestChangePasswordEndpoint:
    def test_change_password_unauthenticated(self, api_client, base_auth_url):
        data = {
            "old_password": "old_password",
            "new_password": "NewPassword123!",
            "new_password2": "NewPassword123!",
        }

        response = api_client.post(f"{base_auth_url}change_password/", data=data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

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
        user.refresh_from_db()
        api_client.force_authenticate(user=user)

        data = {
            "old_password": "wrong_password",
            "new_password": "NewPassword123!",
            "new_password2": "NewPassword123!",
        }

        response = api_client.post(f"{base_auth_url}change_password/", data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        user.refresh_from_db()
        assert user.check_password("old_password")

    def test_change_password_with_mismatched_new_passwords(
        self, api_client, base_auth_url
    ):
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
        user.refresh_from_db()
        assert user.check_password("old_password")


@pytest.mark.django_db
class TestSignupEmailVerificationEndpoint:
    @patch.object(SignupEmailVerification, "send_verification_email")
    def test_email_username_is_valid_return200(
        self, mock_send_verification_email, api_client, base_auth_url
    ):
        email = "user@example.com"
        username = "username"
        data = {
            "email": email,
            "username": username,
        }
        mock_send_verification_email.return_value = None
        response = api_client.post(
            f"{base_auth_url}signup_email_verification/", data=data
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["message"] == "ایمیل تایید ایمیل کاربر ارسال شد"

    def test_email_already_exist_return_406(self, api_client, base_auth_url):
        user = baker.make(User, email="user@example.com", username="username")
        email = "user@example.com"
        username = "username2"
        data = {
            "email": email,
            "username": username,
        }
        response = api_client.post(
            f"{base_auth_url}signup_email_verification/", data=data
        )
        assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE
        # Just to make sure the post request doesn't make new user object
        assert not User.objects.filter(username=username).exists()

    def test_username_already_exist_return_406(self, api_client, base_auth_url):
        user = baker.make(User, email="user@example.com", username="username")
        email = "user2@example.com"
        username = "username"
        data = {
            "email": email,
            "username": username,
        }

        response = api_client.post(
            f"{base_auth_url}signup_email_verification/", data=data
        )
        assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE
        # Just to make sure post request doesn't make new user object
        assert not User.objects.filter(email=email).exists()

    def test_post_verified_email_validation_notexpired_return_406(
        self, api_client, base_auth_url
    ):
        username = "username"
        email = "user@example.com"
        expiration_date = timezone.now() + timedelta(minutes=10)
        SignupEmailVerification.objects.create(
            email=email, expire_at=expiration_date, is_verified=True
        )
        data = {"email": email, "username": username}
        response = api_client.post(
            f"{base_auth_url}signup_email_verification/", data=data
        )
        assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE
        assert response.data["message"] == "کد تایید قبلا به این ایمیل ارسال شده"

    def test_post_verified_email_verification_expired_return406(
        self, api_client, base_auth_url
    ):
        username = "username"
        email = "user@example.com"
        expiration_date = timezone.now() - timedelta(minutes=10)
        SignupEmailVerification.objects.create(
            email=email, expire_at=expiration_date, is_verified=True
        )
        data = {"email": email, "username": username}
        response = api_client.post(
            f"{base_auth_url}signup_email_verification/", data=data
        )
        assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE
        assert response.data["message"] == "ایمیل ارائه شده قبلاً تأیید شده است"

    def test_post_notverified_email_verification_expired_return200(
        self, api_client, base_auth_url
    ):
        username = "username"
        email = "user@example.com"
        # user = baker.make(User, username=username, email=email)
        expiration_date = timezone.now() - timedelta(minutes=10)
        SignupEmailVerification.objects.create(
            email=email, expire_at=expiration_date, is_verified=False
        )
        data = {"email": email, "username": username}
        response = api_client.post(
            f"{base_auth_url}signup_email_verification/", data=data
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["message"] == "ایمیل تایید ایمیل کاربر ارسال شد"
