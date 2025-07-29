import uuid
import pytest
from django.urls import reverse
from unittest.mock import Mock
from django.contrib.auth import get_user_model
from model_bakery import baker
from django.test import SimpleTestCase
from unittest.mock import patch
from rest_framework import status
from rest_framework.test import APITestCase, APIRequestFactory, APIClient
from document.views import *
from document.models import *

User = get_user_model()


@pytest.fixture
def mock_user():
    user = User()
    user.username = "test"
    user.pk = 1
    return user


# This Test class only tests the performance of viewset class and isolates it from
# Database operations.
class TestDocumentViewSet(SimpleTestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User(username="test_user", password="test_password")
        self.client.force_authenticate(user=self.user)

    # This is a good unit test which tests view set without database actions.
    def test_unauthorized_user_access_denied(self):
        client1 = APIClient()
        response = client1.get(reverse("document-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch.object(DocumentViewSet, "get_queryset")
    def test_authorized_user_access_permitted(self, mock_get_queryset):
        mock_get_queryset.return_value = []
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("document-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch.object(DocumentViewSet, "get_queryset")
    def test_user_get_empty_document_list(self, mock_get_queryset):
        mock_get_queryset.return_value = []
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("document-list"))

        self.assertEqual(len(response.data), 0)

    @patch.object(DocumentViewSet, "get_serializer")
    @patch.object(DocumentViewSet, "get_queryset")
    def test_user_get_document_list(self, mock_get_queryset, mock_get_serializer):
        document1 = Document(id=1, title="test_doc_1", owner=self.user)
        document2 = Document(id=2, title="test_doc_2", owner=self.user)
        mock_get_queryset.return_value = [document1, document2]
        mock_serializer_instance = Mock()
        mock_serializer_instance.data = [
            {"id": 1, "title": "test_doc_1"},
            {"id": 2, "title": "test_doc_2"},
        ]
        mock_get_serializer.return_value = mock_serializer_instance
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("document-list"))
        self.assertEqual(len(response.data), 2)

    @patch.object(DocumentViewSet, "get_serializer")
    def test_create_document(self, mock_get_serializer):
        mock_serializer_instance = Mock()
        mock_serializer_instance.is_valid.return_value = True
        mock_serializer_instance.save.return_value = Document(id=1, owner=self.user)
        mock_serializer_instance.data = {"id": 1, "title": "New Document"}
        mock_get_serializer.return_value = mock_serializer_instance

        response = self.client.post(
            reverse("document-list"), {"title": "New Document"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @patch.object(DocumentViewSet, "get_object")
    @patch.object(DocumentViewSet, "get_serializer")
    def test_document_retrieve(self, mock_get_serializer, mock_get_object):

        mock_get_object.return_value = Document(id=1, title="document title")
        mock_serializer_instance = Mock()
        mock_serializer_instance.data = {"id": 1, "title": "document title"}
        mock_get_serializer.return_value = mock_serializer_instance

        response = self.client.get(
            reverse("document-detail", kwargs={"doc_uuid": uuid.uuid4()})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch.object(DocumentViewSet, "get_object")
    @patch.object(DocumentViewSet, "perform_destroy")
    def test_document_delete(self, mock_perform_destroy, mock_get_object):
        mock_get_object.return_value = Document(id=1, owner=self.user)
        mock_perform_destroy.return_value = None

        response = self.client.delete(
            reverse("document-detail", kwargs={"doc_uuid": uuid.uuid4()})
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @patch.object(DocumentViewSet, "perform_update")
    @patch.object(DocumentViewSet, "get_serializer")
    @patch.object(DocumentViewSet, "get_object")
    def test_document_update(
        self, mock_get_object, mock_get_serializer, mock_perform_update
    ):
        mock_get_object.return_value = Document(owner=self.user)
        mock_serializer_instance = Mock()
        mock_serializer_instance.data = {"id": 1}
        mock_get_serializer.is_valid.return_value = True
        mock_get_serializer.return_value = mock_serializer_instance
        mock_perform_update.return_value = None

        # Need to be fixed.
        response = self.client.patch(
            reverse("document-detail", kwargs={"doc_uuid": uuid.uuid4()}),
            {"title": "new doc"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestCommentViewSet(SimpleTestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User(username="test_user", password="test_password")
        self.client.force_authenticate(user=self.user)

    def test_unauthorized_access_comment_return_401(self):
        client1 = APIClient()
        response = client1.get(
            reverse("comment-list", kwargs={"doc_uuid": uuid.uuid4()})
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch.object(CommentViewSet, "get_queryset")
    def test_get_comment_empty_list(self, mock_get_queryset):
        mock_get_queryset.return_value = []

        response = self.client.get(
            reverse("comment-list", kwargs={"doc_uuid": uuid.uuid4()})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch.object(CommentViewSet, "get_serializer")
    @patch.object(CommentViewSet, "get_queryset")
    def test_get_comment_list_has_two_comments(
        self, mock_get_queryset, mock_get_serializer
    ):
        mock_get_queryset.return_value = [
            Comment(author=self.user, document=Document(id=1, owner=self.user)),
            Comment(author=self.user, document=Document(id=2, owner=self.user)),
        ]
        mock_serializer_instance = Mock()
        mock_serializer_instance.is_valid.return_value = True
        mock_serializer_instance.data = [
            {"id": 1, "author": 1, "document": 1},
            {"id": 2, "author": 1, "document": 2},
        ]
        mock_get_serializer.return_value = mock_serializer_instance

        response = self.client.get(
            reverse("comment-list", kwargs={"doc_uuid": uuid.uuid4()})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    @patch.object(CommentViewSet, "get_serializer")
    @patch.object(CommentViewSet, "get_object")
    def test_get_certain_comment(self, mock_get_object, mock_get_serializer):
        mock_get_object.return_value = [
            Comment(id=1, author=self.user, document=Document(owner=self.user))
        ]
        mock_serializer_instance = Mock()
        mock_serializer_instance.data = [{"id": 1, "author": 1, "document": 1}]
        mock_get_serializer.return_value = mock_serializer_instance

        response = self.client.get(
            reverse("comment-detail", kwargs={"doc_uuid": uuid.uuid4(), "id": 1})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch.object(CommentViewSet, "perform_update")
    @patch.object(CommentViewSet, "get_serializer")
    @patch.object(CommentViewSet, "get_object")
    def test_update_certain_comment(
        self, mock_get_object, mock_get_serializer, mock_perform_update
    ):
        document = Document(owner=self.user)

        mock_get_object.return_value = Comment(author=self.user, document=document)
        mock_serializer_instance = Mock()
        mock_serializer_instance.is_valid.return_value = True
        mock_serializer_instance.data = {"id": 1}
        mock_get_serializer.return_value = mock_serializer_instance
        mock_perform_update.return_value = None

        data = {"id": 1, "text": "test text"}

        response = self.client.patch(
            reverse("comment-detail", kwargs={"doc_uuid": uuid.uuid4(), "id": 1}), data
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch.object(CommentViewSet, "get_serializer")
    def test_create_new_comment(self, mock_get_serializer):
        mock_serializer_instance = Mock()
        mock_serializer_instance.is_valid.return_value = True
        mock_serializer_instance.data = {"id": 1, "author": 1, "document": 2}
        mock_serializer_instance.save.return_value = None
        mock_get_serializer.return_value = mock_serializer_instance

        response = self.client.post(
            reverse("comment-list", kwargs=({"doc_uuid": uuid.uuid4()})),
            {"author": 1, "document": 2},
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @patch.object(CommentViewSet, "perform_destroy")
    @patch.object(CommentViewSet, "get_object")
    def test_delete_certain_comment(self, mock_get_object, mock_perform_destroy):
        mock_get_object.return_value = Comment(
            author=self.user, document=Document(owner=self.user)
        )
        mock_perform_destroy.return_value = None

        response = self.client.delete(
            reverse("comment-detail", kwargs={"doc_uuid": uuid.uuid4(), "id": 1})
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class TestCommentReplyViewSet(SimpleTestCase):
    def setUp(self):
        self.user = User(id=1, username="test user", password="test_password")
        self.document = Document(owner=self.user)
        self.comment = Comment(author=self.user, document=self.document)
        self.comment_reply = CommentReply(author=self.user, comment=self.comment)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_unauthorized_access(self):
        client1 = APIClient()
        reponse = client1.get(reverse("comment-reply-list"))
        self.assertEqual(reponse.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch.object(CommentReplyViewSet, "perform_create")
    @patch.object(CommentReplyViewSet, "get_serializer")
    def test_create_commentreply(self, mock_get_serializer, mock_perform_create):
        mock_serializer_instance = Mock()
        mock_serializer_instance.data = {"id": 1}
        mock_serializer_instance.is_valid.return_value = True
        mock_get_serializer.return_value = mock_serializer_instance

        mock_perform_create.return_value = None

        response = self.client.post(
            reverse("comment-reply-list"),
            {"id": 1},
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @patch.object(CommentReplyViewSet, "get_serializer")
    @patch.object(CommentReplyViewSet, "get_object")
    def test_update_commentreply(self, mock_get_object, mock_get_serializer):
        mock_get_object.return_value = self.comment_reply
        mock_serializer_instance = Mock()
        mock_serializer_instance.data = {"id": 1}
        mock_serializer_instance.is_valid.return_value = True
        mock_serializer_instance.save.return_value = None

        mock_get_serializer.return_value = mock_serializer_instance

        response = self.client.patch(reverse("comment-reply-detail", kwargs={"pk": 1}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch.object(CommentReplyViewSet, "get_object")
    def test_delete_commentreply(self, mock_get_object):
        mock_object = Mock()
        mock_object.delete.return_value = None
        mock_get_object.return_value = mock_object

        response = self.client.delete(reverse("comment-reply-detail", kwargs={"pk": 1}))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_retrieve_commentreply_return_404(self):
        response = self.client.get("comment-reply-detail", kwargs={"id": 1})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_commentreply_return_405(self):
        response = self.client.get(reverse("comment-reply-list"))
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class TestDocumentUpdateViewSet(SimpleTestCase):
    def setUp(self):
        self.user = User(username="test_user", password="test_password")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.document = Document(owner=self.user)
        self.document_update = DocumentUpdate(author=self.user, document=self.document)

    @patch.object(DocumentUpdateViewSet, "get_serializer")
    @patch.object(DocumentUpdateViewSet, "get_object")
    def test_retrieve_documentupdate(self, mock_get_object, mock_get_serializer):
        mock_get_object.return_value = self.document_update
        mock_serializer_instance = Mock()
        mock_serializer_instance.is_valid.return_value = True
        mock_serializer_instance.data = [{"id": 1}]
        mock_get_serializer.return_value = mock_serializer_instance

        response = self.client.get(
            reverse(
                "document-update-detail", kwargs={"doc_uuid": uuid.uuid4(), "pk": 1}
            )
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch.object(DocumentUpdateViewSet, "get_serializer")
    @patch.object(DocumentUpdateViewSet, "get_queryset")
    def test_list_documentupdate(self, mock_get_queryset, mock_get_serializer):
        mock_get_queryset.return_value = [self.document_update, self.document_update]
        mock_serializer_instance = Mock()
        mock_serializer_instance.data = [{"id": 1}, {"id": 2}]
        mock_get_serializer.return_value = mock_serializer_instance

        response = self.client.get(
            reverse("document-update-list", kwargs={"doc_uuid": uuid.uuid4()})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_post_documentupdate_return_405(self):
        response = self.client.post(
            reverse("document-update-list", kwargs={"doc_uuid": uuid.uuid4()})
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_documentupdate_return_405(self):
        response = self.client.delete(
            reverse(
                "document-update-detail", kwargs={"doc_uuid": uuid.uuid4(), "pk": 1}
            )
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    @patch.object(DocumentUpdateViewSet, "get_object")
    @patch.object(DocumentUpdateViewSet, "get_serializer")
    def test_update_documentupdate(self, mock_get_serializer, mock_get_object):
        mock_get_object.return_value = self.document_update
        mock_serializer_instance = Mock()
        mock_serializer_instance.is_valid.return_value = True
        mock_serializer_instance.data = {"id": 1}
        mock_serializer_instance.save.return_value = None
        mock_get_serializer.return_value = mock_serializer_instance

        response = self.client.patch(
            reverse(
                "document-update-detail", kwargs={"doc_uuid": uuid.uuid4(), "pk": 1}
            )
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
