import pytest
from rest_framework import status
from model_bakery import baker
from document.models import Document, AccessLevel, Comment
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def base_docs_url():
    return f"/api/v1/docs/"

@pytest.mark.django_db
class TestDocumentEndpoints:
    def test_create_document(self, api_client, base_docs_url):
        user = baker.make(User)
        api_client.force_authenticate(user=user)
        data = {
            "title": "Test Document",
            "content": b"Sample content",
        }

        response = api_client.post(base_docs_url, data=data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == data["title"]
        assert response.data["owner"] == user.id
        
    def test_create_document_without_name(self, api_client, base_docs_url):
        # it should be create document with default name
        user = baker.make(User)
        api_client.force_authenticate(user=user)
        data = {
            
        }
        response = api_client.post(base_docs_url, data=data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == "سند بدون عنوان"
        assert response.data["owner"] == user.id

    def test_list_documents(self, api_client, base_docs_url):
        user = baker.make(User)
        api_client.force_authenticate(user=user)
        baker.make(Document, owner=user, _quantity=3)

        response = api_client.get(base_docs_url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3

    def test_retrieve_document(self, api_client, base_docs_url):
        user = baker.make(User)
        api_client.force_authenticate(user=user)
        document = baker.make(Document, owner=user)

        response = api_client.get(f"{base_docs_url}{document.doc_uuid}/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == document.id

    def test_update_document(self, api_client, base_docs_url):
        user = baker.make(User)
        api_client.force_authenticate(user=user)
        document = baker.make(Document, owner=user)
        data = {"title": "Updated Title"}

        response = api_client.patch(f"{base_docs_url}{document.doc_uuid}/", data=data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == data["title"]

    def test_delete_document(self, api_client, base_docs_url):
        user = baker.make(User)
        api_client.force_authenticate(user=user)
        document = baker.make(Document, owner=user)

        response = api_client.delete(f"{base_docs_url}{document.doc_uuid}/")

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Document.objects.filter(id=document.id).exists()

    def test_permission_denied_for_unauthenticated_user(self, api_client, base_docs_url):
        response = api_client.get(base_docs_url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

