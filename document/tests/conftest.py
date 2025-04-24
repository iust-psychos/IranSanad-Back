from pytest import fixture
from authentication.models import User
from rest_framework_simplejwt.tokens import AccessToken



@fixture
def user_token_tuple():
    user = User.objects.create_user(username="testuser", password="testpassword")
    token = str(AccessToken.for_user(user))
    return user, token

