import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from document.models import Document, DocumentUpdate


User = get_user_model()


@pytest.fixture
def user():
    return User.objects.create_user(id=1, username="testuser", password="testpass")


@pytest.fixture
def document(user):
    return Document.objects.create(title="Test Doc", owner=user)


@pytest.fixture
def documentupdate(user, document):
    return DocumentUpdate.objects.create(
        title="Test Update",
        document=document,
        page=1,
        author=user,
        update_data=b"testdata",
        is_compacted=True,
    )


@pytest.mark.django_db
class TestDocumentUpdateEndpoints:
    def test_retrieve_documentupdate(self, api_client, user, documentupdate):
        api_client.force_authenticate(user=user)
        url = reverse(
            "document-update-detail",
            kwargs={
                "doc_uuid": str(documentupdate.document.doc_uuid),
                "pk": documentupdate.id,
            },
        )
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.data["title"] == documentupdate.title
        assert response.data["document"] == documentupdate.document.id
        assert response.data["page"] == documentupdate.page

    def test_create_documentupdate(self, api_client, user, document):
        assert DocumentUpdate.objects.count() == 0
        api_client.force_authenticate(user=user)
        url = reverse("document-update-list", kwargs={"doc_uuid": document.doc_uuid})
        data = {
            "title": "Test Update",
            "document": document.id,
            "page": 1,
            "author": user.id,
            "update_data": b"testdata",
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == 405
        assert DocumentUpdate.objects.count() == 0

    def test_patch_documentupdate(self, api_client, user, documentupdate):
        api_client.force_authenticate(user=user)
        url = reverse(
            "document-update-detail",
            kwargs={
                "doc_uuid": str(documentupdate.document.doc_uuid),
                "pk": documentupdate.id,
            },
        )
        data = {"title": "Updated Title"}
        assert documentupdate.title == "Test Update"
        response = api_client.patch(url, data, format="json")
        assert response.status_code == 200
        documentupdate.refresh_from_db()
        assert documentupdate.title == "Updated Title"

    def test_delete_documentupdate(self, api_client, user, documentupdate):
        api_client.force_authenticate(user=user)
        url = reverse(
            "document-update-detail",
            kwargs={
                "doc_uuid": str(documentupdate.document.doc_uuid),
                "pk": documentupdate.id,
            },
        )
        assert DocumentUpdate.objects.count() == 1
        response = api_client.delete(url)
        assert response.status_code == 405
        assert DocumentUpdate.objects.count() == 1
