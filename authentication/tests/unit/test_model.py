from django.contrib.auth import get_user_model
from django.test import SimpleTestCase
from django.db import models
from authentication.models import (
    ProfileImage,
    EmailVerification,
    ForgetPasswordVerification,
    SignupEmailVerification,
)
from datetime import datetime
from django.utils import timezone

User = get_user_model()


class TestUserModelDefinition(SimpleTestCase):
    def test_user_email(self):
        self.assertTrue(User._meta.get_field("email").unique)

    def test_phone_number_max_length20(self):
        self.assertEqual(User._meta.get_field("phone_number").max_length, 20)

    def test_phone_number_blank_True(self):
        self.assertTrue(User._meta.get_field("phone_number").blank)

    def test_phone_number_unique_True(self):
        self.assertTrue(User._meta.get_field("phone_number").unique)

    def test_phone_number_null_True(self):
        self.assertTrue(User._meta.get_field("phone_number").null)

    def test_birth_date_blank_True(self):
        self.assertTrue(User._meta.get_field("birth_date").blank)

    def test_birth_date_null_True(self):
        self.assertTrue(User._meta.get_field("birth_date").null)

    def test_user_model_str_func(self):
        user = User(username="test user", password="test password")
        self.assertEqual(str(user), "test user")


class TestProfileImageModelDefinition(SimpleTestCase):
    def test_user_foreignkey_ondelete_cascade(self):
        field = ProfileImage._meta.get_field("user")
        self.assertEqual(field.remote_field.on_delete, models.CASCADE)

    def test_image_blank_true(self):
        self.assertTrue(ProfileImage._meta.get_field("image").blank)

    def test_image_null_true(self):
        self.assertTrue(ProfileImage._meta.get_field("image").null)


class TestEmailVerificationModelDefinition(SimpleTestCase):
    def test_user_ondelete_cascade(self):
        field = EmailVerification._meta.get_field("user")
        self.assertEqual(field.remote_field.on_delete, models.CASCADE)

    def test_code_max_length5(self):
        self.assertEqual(EmailVerification._meta.get_field("code").max_length, 5)

    def test_code_null_True(self):
        self.assertTrue(EmailVerification._meta.get_field("code").null)

    def test_code_blank_True(self):
        self.assertTrue(EmailVerification._meta.get_field("code").blank)

    def test_is_expired(self):
        user = User(username="test user", password="test password")
        expired_date = datetime(2000, 1, 1, 1, 1, 1, 1, timezone.get_default_timezone())
        non_expired_date = datetime(
            3000, 1, 1, 1, 1, 1, 1, timezone.get_default_timezone()
        )
        expired_email = EmailVerification(user=user, expire_at=expired_date)
        non_expired_email = EmailVerification(user=user, expire_at=non_expired_date)
        self.assertTrue(expired_email.is_expired())
        self.assertFalse(non_expired_email.is_expired())

    def test_is_valid_function(self):
        user = User(username="test user", password="test password")
        code = "90856"
        expiration_date_1 = datetime(
            2000, 1, 1, 1, 1, 1, 1, timezone.get_default_timezone()
        )
        expiration_date_2 = datetime(
            3000, 1, 1, 1, 1, 1, 1, timezone.get_default_timezone()
        )
        expired_email_ver = EmailVerification(
            user=user, code=code, expire_at=expiration_date_1
        )
        non_expired_email_ver = EmailVerification(
            user=user, code=code, expire_at=expiration_date_2
        )

        self.assertTrue(non_expired_email_ver.is_valid(code))
        self.assertFalse(non_expired_email_ver.is_valid("00000"))
        self.assertFalse(expired_email_ver.is_valid(code))
        self.assertFalse(expired_email_ver.is_valid("00000"))


class TestForgetPasswordVerificationModelDefinition(SimpleTestCase):
    def test_user_on_delete_cascade(self):
        field = ForgetPasswordVerification._meta.get_field("user")
        self.assertEqual(field.remote_field.on_delete, models.CASCADE)

    def test_code_max_length5(self):
        field = ForgetPasswordVerification._meta.get_field("code")
        self.assertEqual(field.max_length, 5)

    def test_code_null_True(self):
        field = ForgetPasswordVerification._meta.get_field("code")
        self.assertTrue(field.null)

    def test_code_blank_True(self):
        field = ForgetPasswordVerification._meta.get_field("code")
        self.assertTrue(field.blank)

    def test_is_expired_function(self):
        user = User(username="test user", password="test password")
        expired_date = datetime(2000, 1, 1, 1, 1, 1, 1, timezone.get_default_timezone())
        non_expired_date = datetime(
            3000, 1, 1, 1, 1, 1, 1, timezone.get_default_timezone()
        )
        expired_fp = ForgetPasswordVerification(user=user, expire_at=expired_date)
        non_expired_fp = ForgetPasswordVerification(
            user=user, expire_at=non_expired_date
        )

        self.assertTrue(expired_fp.is_expired())
        self.assertFalse(non_expired_fp.is_expired())

    def test_is_valid_function(self):
        user = User(username="test user", password="test password")
        expired_date = datetime(2000, 1, 1, 1, 1, 1, 1, timezone.get_default_timezone())
        non_expired_date = datetime(
            3000, 1, 1, 1, 1, 1, 1, timezone.get_default_timezone()
        )
        code = "81818"
        expired_fp = ForgetPasswordVerification(
            user=user, code=code, expire_at=expired_date
        )
        non_expired_fp = ForgetPasswordVerification(
            user=user, code=code, expire_at=non_expired_date
        )
        self.assertTrue(non_expired_fp.is_valid("81818"))
        self.assertFalse(non_expired_fp.is_valid("12345"))
        self.assertFalse(expired_fp.is_valid("81818"))
        self.assertFalse(expired_fp.is_valid("12345"))


class TestSignUpEmailVerificationModelDefinition(SimpleTestCase):
    def test_email_unique_True(self):
        field = SignupEmailVerification._meta.get_field("email")
        self.assertTrue(field.unique)

    def test_code_max_length5(self):
        field = SignupEmailVerification._meta.get_field("code")
        self.assertEqual(field.max_length, 5)

    def test_code_null_True(self):
        field = SignupEmailVerification._meta.get_field("code")
        self.assertTrue(field.null)

    def test_code_blank_True(self):
        field = SignupEmailVerification._meta.get_field("code")
        self.assertTrue(field.blank)

    def test_is_expired_function(self):
        email = "test_email@example.com"
        expired_date = datetime(2000, 1, 1, 1, 1, 1, 1, timezone.get_default_timezone())
        non_expired_date = datetime(
            3000, 1, 1, 1, 1, 1, 1, timezone.get_default_timezone()
        )
        expired_email = SignupEmailVerification(email=email, expire_at=expired_date)
        non_expired_email = SignupEmailVerification(
            email=email, expire_at=non_expired_date
        )

        self.assertTrue(expired_email.is_expired())
        self.assertFalse(non_expired_email.is_expired())

    def test_is_valid_function(self):
        email = "test_email@example.com"
        expired_date = datetime(2000, 1, 1, 1, 1, 1, 1, timezone.get_default_timezone())
        non_expired_date = datetime(
            3000, 1, 1, 1, 1, 1, 1, timezone.get_default_timezone()
        )
        code = "99999"
        expired_email = SignupEmailVerification(
            email=email, code=code, expire_at=expired_date
        )
        non_expired_email = SignupEmailVerification(
            email=email, code=code, expire_at=non_expired_date
        )
        self.assertTrue(non_expired_email.is_valid("99999"))
        self.assertFalse(non_expired_email.is_valid("12312"))
        self.assertFalse(expired_email.is_valid("99999"))
        self.assertFalse(expired_email.is_valid("12222"))
