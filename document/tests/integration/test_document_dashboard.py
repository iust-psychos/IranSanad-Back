import pytest

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from model_bakery import baker
from document.models import *

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
        }

        response = api_client.post(base_docs_url, data=data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == data["title"]
        assert response.data["owner"] == user.id

    def test_create_document_without_name(self, api_client, base_docs_url):
        # it should be create document with default name
        user = baker.make(User)
        api_client.force_authenticate(user=user)
        data = {}
        response = api_client.post(base_docs_url, data=data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == "سند بدون عنوان"
        assert response.data["owner"] == user.id

    def test_list_documents_excluding_shared_documents(self, api_client, base_docs_url):
        user1 = baker.make(User)
        api_client.force_authenticate(user=user1)

        titles = ["Test Document 1", "Test Document 2", "Test Document 3"]

        api_client.post(base_docs_url, {"title": titles[0]})
        api_client.post(base_docs_url, {"title": titles[1]})
        api_client.post(base_docs_url, {"title": titles[2]})

        response = api_client.get(base_docs_url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3
        assert response.data[0]["title"] == titles[0]
        assert response.data[1]["title"] == titles[1]
        assert response.data[2]["title"] == titles[2]

    def test_document_list_including_shared_documents(self, api_client, base_docs_url):
        user1 = baker.make(User)
        user2 = baker.make(User)

        api_client.force_authenticate(user=user1)
        response = api_client.post(base_docs_url, {"title": "User1 Document"})
        document_id = response.data["id"]

        url = base_docs_url + "permission/set_permission/"
        data = {
            "document": document_id,
            "permissions": [{"user": user2.id, "permission": "ReadOnly"}],
            "send_email": False,
            "email_message": "You are invited to view this document.",
        }
        api_client.post(url, data=data, format="json")
        api_client.logout()
        api_client.force_authenticate(user=user2)
        api_client.post(base_docs_url, data={"title": "User2 Document"})
        response = api_client.get(base_docs_url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

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

    def test_permission_denied_for_unauthenticated_user(
        self, api_client, base_docs_url
    ):
        response = api_client.get(base_docs_url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
