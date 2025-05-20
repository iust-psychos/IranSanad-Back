import pytest
from rest_framework import status
from model_bakery import baker
from document.models import Document, AccessLevel
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def base_permission_url():
    return "/api/v1/docs/permission/"

@pytest.fixture
def test_users():
    owner = baker.make(User, username='owner')
    admin = baker.make(User, username='admin')
    writer = baker.make(User, username='writer')
    reader = baker.make(User, username='reader')
    other = baker.make(User, username='other')
    return {
        'owner': owner,
        'admin': admin,
        'writer': writer,
        'reader': reader,
        'other': other
    }

@pytest.fixture
def test_document(test_users):
    doc = baker.make(Document, owner=test_users['owner'], public_premission_access=False)
    # Set up initial permissions
    baker.make(AccessLevel, user=test_users['admin'], document=doc, access_level=AccessLevel.PERMISSION_MAP['Admin'])
    baker.make(AccessLevel, user=test_users['writer'], document=doc, access_level=AccessLevel.PERMISSION_MAP['Writer'])
    baker.make(AccessLevel, user=test_users['reader'], document=doc, access_level=AccessLevel.PERMISSION_MAP['ReadOnly'])
    return doc

@pytest.mark.django_db
class TestDocumentPermissionEndpoints:
w    def test_set_permission_by_owner(self, api_client, base_permission_url, test_users, test_document):
        api_client.force_authenticate(user=test_users['owner'])
        data = {
            'document': test_document.id,
            'permissions': [
                {'user': test_users['other'].id, 'permission': 'Writer'},
                {'user': test_users['reader'].id, 'permission': 'Admin'}
            ],
            'send_email': False
        }
        
        response = api_client.post(f"{base_permission_url}set_permission/", data=data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert AccessLevel.objects.get(user=test_users['other'], document=test_document).access_level == AccessLevel.PERMISSION_MAP['Writer']
        assert AccessLevel.objects.get(user=test_users['reader'], document=test_document).access_level == AccessLevel.PERMISSION_MAP['Admin']

    def test_set_permission_by_admin(self, api_client, base_permission_url, test_users, test_document):
        api_client.force_authenticate(user=test_users['admin'])
        data = {
            'document': test_document.id,
            'permissions': [
                {'user': test_users['other'].id, 'permission': 'ReadOnly'}
            ],
            'send_email': False
        }
        
        response = api_client.post(f"{base_permission_url}set_permission/", data=data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert AccessLevel.objects.get(user=test_users['other'], document=test_document).access_level == AccessLevel.PERMISSION_MAP['ReadOnly']

    def test_set_permission_denied_by_writer(self, api_client, base_permission_url, test_users, test_document):
        api_client.force_authenticate(user=test_users['writer'])
        data = {
            'document': test_document.id,
            'permissions': [
                {'user': test_users['other'].id, 'permission': 'ReadOnly'}
            ],
            'send_email': False
        }
        
        response = api_client.post(f"{base_permission_url}set_permission/", data=data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_permission_list_by_owner(self, api_client, base_permission_url, test_users, test_document):
        api_client.force_authenticate(user=test_users['owner'])
        
        response = api_client.get(f"{base_permission_url}get_permission_list/{test_document.id}/")
        
        assert response.status_code == status.HTTP_200_OK
        print(response.data)
        assert len(response.data) == 4  # owner + admin + writer + reader

    def test_get_user_permission_for_reader(self, api_client, base_permission_url, test_users, test_document):
        api_client.force_authenticate(user=test_users['reader'])
        
        response = api_client.get(f"{base_permission_url}get_user_permission/{test_document.id}/")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['access_level'] == 'ReadOnly'
        assert response.data['can_write'] is False

    def test_get_user_permission_default(self, api_client, base_permission_url, test_users, test_document):
        api_client.force_authenticate(user=test_users['other'])
        
        response = api_client.get(f"{base_permission_url}get_user_permission/{test_document.id}/")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['access_level'] == 'Writer'  # Default access level
        assert response.data['can_write'] is True