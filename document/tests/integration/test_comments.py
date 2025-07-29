import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
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


@pytest.mark.django_db
class TestCommentAPI:
    def test_create_comment(self, document, user):
        client = APIClient()
        client.force_authenticate(user=user)
        url = reverse("comment-list", kwargs={"doc_uuid": document.doc_uuid})
        data = {
            "document_uuid": document.doc_uuid,
            "author": user.username,
            "text": "New Comment",
            "range_start": {"type": "text", "index": 10},
            "range_end": {"type": "text", "index": 20},
        }
        assert Comment.objects.count() == 0
        response = client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert Comment.objects.count() == 1
        assert Comment.objects.first().text == "New Comment"
        assert Comment.objects.first().author.id == 1
        assert Comment.objects.first().document.id == document.id

    def test_comment_list(self, document, comment):
        client = APIClient()
        client.force_authenticate(user=document.owner)
        url = reverse("comment-list", kwargs={"doc_uuid": document.doc_uuid})
        response = client.get(url)
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["text"] == comment.text
        assert response.data[0]["author_username"] == document.owner.username
        assert "author" not in response.data[0]

    def test_comment_retrieve(self, comment, user):
        client = APIClient()
        client.force_authenticate(user=user)
        url = reverse(
            "comment-detail",
            kwargs={"doc_uuid": comment.document.doc_uuid, "id": comment.id},
        )
        response = client.get(url)
        assert response.data["text"] == comment.text
        assert response.data["author_username"] == comment.author.username
        assert response.data["range_start"] == comment.range_start
        assert response.data["range_end"] == comment.range_end

    def test_patch_comment(self, comment, user):
        client = APIClient()
        client.force_authenticate(user=user)
        url = reverse(
            "comment-detail",
            kwargs={"doc_uuid": comment.document.doc_uuid, "id": comment.id},
        )
        data = {"text": "Updated Comment", "is_resolved": True}
        response = client.patch(url, data, format="json")
        assert response.status_code == 200
        assert response.data["text"] == "Updated Comment"
        assert response.data["is_resolved"] == True

    def test_delete_comment(self, comment, user):
        client = APIClient()
        client.force_authenticate(user=user)
        url = reverse(
            "comment-detail",
            kwargs={"doc_uuid": comment.document.doc_uuid, "id": comment.id},
        )
        assert Comment.objects.count() == 1
        response = client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Comment.objects.count() == 0
