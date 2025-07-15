import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from model_bakery import baker

User = get_user_model()

@pytest.fixture
def mock_user():
    user = User()
    user.username = "test"
    user.pk = 1
    return user

class TestDocumentViewSet:
    # def setUp(self):

    def test_document_view_set(self, mock_user):
        url = reverse("document-list")
        self.client.login(username=mock_user.username, password = mock_user.password)
        response = self.client.get(url)
        assert response.status_code == 200
