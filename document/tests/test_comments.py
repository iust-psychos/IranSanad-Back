import pytest
import uuid
from django.contrib.auth import get_user_model
from document.models import Document, Comment, CommentReply

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

    def test_commentreply_creation(self, comment, user):
        commentreply = CommentReply.objects.create(
            id=uuid.uuid4(), comment=comment, author=user, text="Test Reply"
        )
        assert commentreply.comment == comment
        assert commentreply.author == user
        assert commentreply.text == "Test Reply"
