from pytest import fixture
from authentication.models import User
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.test import APIClient



@fixture
def user_token_tuple():
    user = User.objects.create_user(username="testuser", password="testpassword")
    token = str(AccessToken.for_user(user))
    return user, token

@fixture
def api_client():
    return APIClient()
