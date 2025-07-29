import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from document.models import Document, Comment, CommentReply


User = get_user_model()


@pytest.fixture
def user():
    return User.objects.create_user(id=1, username="testuser", password="testpass")


@pytest.fixture
def document(user):
    return Document.objects.create(title="Test Doc", owner=user)


@pytest.fixture
def comment(document, user):
    return Comment.objects.create(
        document=document,
        author=user,
        text="Test Comment",
        range_start={"type": "text", "index": 10},
        range_end={"type": "text", "index": 20},
    )


@pytest.fixture
def commentreply(user, comment):
    return CommentReply.objects.create(comment=comment, author=user, text="Test Reply")


@pytest.mark.django_db
class TestCommentReplyEndpoints:
    def test_create_commentreply(self, api_client, user, comment):
        assert CommentReply.objects.count() == 0
        api_client.force_authenticate(user=user)
        url = reverse("comment-reply-list")
        data = {"author": user.username, "comment": comment.id, "text": "Test Reply"}
        response = api_client.post(url, data, format="json")
        assert response.status_code == 201
        assert CommentReply.objects.count() == 1

    def test_patch_commentreply(self, api_client, user, commentreply):
        api_client.force_authenticate(user=user)
        url = reverse("comment-reply-detail", kwargs={"pk": commentreply.id})
        data = {"text": "Updated Reply"}
        assert commentreply.text == "Test Reply"
        response = api_client.patch(url, data, format="json")
        assert response.status_code == 200
        commentreply.refresh_from_db()
        assert commentreply.text == "Updated Reply"

    def test_delete_commentreply(self, api_client, user, commentreply):
        api_client.force_authenticate(user=user)
        url = reverse("comment-reply-detail", kwargs={"pk": commentreply.id})
        assert CommentReply.objects.count() == 1
        response = api_client.delete(url)
        assert response.status_code == 204
        assert CommentReply.objects.count() == 0
