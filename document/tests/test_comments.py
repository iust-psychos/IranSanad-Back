import pytest
import uuid
from django.contrib.auth import get_user_model
from document.models import Document, Comment, CommentReply
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse

User = get_user_model()


@pytest.fixture
def user():
    return User.objects.create_user(username="testuser", password="testpass")


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
class TestCommentModels:
    def test_comment_creation(self, document, user):
        comment = Comment.objects.create(
            id=uuid.uuid4(),
            document=document,
            author=user,
            text="Test Comment",
            range_start={"type": "text", "index": 10},
            range_end={"type": "text", "index": 20},
        )
        assert comment.document == document
        assert comment.author == user
        assert comment.text == "Test Comment"
        assert comment.range_start == {"type": "text", "index": 10}
        assert comment.range_end == {"type": "text", "index": 20}
        assert not comment.is_resolved

    def test_retrieve_comments(self, document, comment):
        comments = Comment.objects.filter(document=document)
        assert comments.count() == 1
        assert comments.first() == comment

    def test_comment_update(self, comment):
        comment.text = "Updated Comment"
        comment.save()
        assert comment.text == "Updated Comment"

    def test_comment_deletion(self, comment):
        comment.delete()
        assert Comment.objects.count() == 0

    def test_commentreply_creation(self, comment, user):
        commentreply = CommentReply.objects.create(
            id=uuid.uuid4(), comment=comment, author=user, text="Test Reply"
        )
        assert commentreply.comment == comment
        assert commentreply.author == user
        assert commentreply.text == "Test Reply"


@pytest.mark.django_db
class TestCommentAPI:
    def test_create_comment(self, document, user):
        client = APIClient()
        client.force_authenticate(user=user)
        url = reverse("comment-list", kwargs={"doc_id": document.id})
        data = {
            "comment_uuid": uuid.uuid4(),
            "document": document.id,
            "author": user.id,
            "text": "New Comment",
            "range_start": {"type": "text", "index": 10},
            "range_end": {"type": "text", "index": 20},
        }
        response = client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert Comment.objects.count() == 1
        assert Comment.objects.first().text == "New Comment"

    def test_comment_list(self, document, comment):
        client = APIClient()
        client.force_authenticate(user=document.owner)
        url = reverse("comment-list", kwargs={"doc_id": document.id})
        response = client.get(url)
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["text"] == comment.text

    def test_comment_retrieve(self, comment, user):
        client = APIClient()
        client.force_authenticate(user=user)
        url = reverse(
            "comment-detail", kwargs={"doc_id": comment.document.id, "pk": comment.id}
        )
        response = client.get(url)
        assert response.data["text"] == comment.text
        assert response.data["author"] == comment.author.id
        assert response.data["range_start"] == comment.range_start
        assert response.data["range_end"] == comment.range_end

    def test_patch_comment(self, comment, user):
        client = APIClient()
        client.force_authenticate(user=user)
        url = reverse(
            "comment-detail",
            kwargs={"doc_id": comment.document.id, "pk": comment.id},
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
            "comment-detail", kwargs={"doc_id": comment.document.id, "pk": comment.id}
        )
        response = client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
