import pytest
from unittest.mock import Mock
from django.db import models
from django.contrib.auth import get_user_model
from model_bakery import baker
from document.models import *

User = get_user_model()


@pytest.fixture
def mock_user():
    user = User()
    user.username = "test"
    user.pk = 1
    return user


@pytest.fixture
def mock_document(mock_user):
    document = Document(id=1, title="new title", owner=mock_user)
    return document


@pytest.fixture
def mock_documentview(mock_document):
    documentview = DocumentView(document=mock_document)
    return documentview


class TestDocument:
    def test_document__str__(self, mock_document):
        assert str(mock_document) == "new title"

    def test_document_title_max_length(self):
        max_length = Document._meta.get_field("title").max_length
        assert max_length == 255

    def test_document_title_default(self):
        default = Document._meta.get_field("title").default
        assert default == "سند بدون عنوان"

    def test_document_link_max_length(self):
        max_length = Document._meta.get_field("link").max_length
        assert max_length == 15

    def test_document_link_unique_blank_true(self):
        assert Document._meta.get_field("link").unique == True
        assert Document._meta.get_field("link").blank == True

    def test_document_owner_null_blank_true(self):
        assert Document._meta.get_field("owner").null is True
        assert Document._meta.get_field("owner").blank is True

    def test_document_owner_on_delete_set_null(self):
        field = Document._meta.get_field("owner")
        assert field.remote_field.on_delete == models.SET_NULL

    def test_document_created_at_auto_now_add_true(self):
        assert Document._meta.get_field("created_at").auto_now_add == True

    def test_document_updated_at_auto_now_true(self):
        assert Document._meta.get_field("updated_at").auto_now == True

    def test_document_uuid_editable_false(self):
        assert Document._meta.get_field("doc_uuid").editable is False

    def test_document_uuid_unique_true(self):
        assert Document._meta.get_field("doc_uuid").unique is True

    def test_document_is_public_default_False(self):
        assert Document._meta.get_field("is_public").default == False

    def test_document_public_permission_access_default_True(self):
        assert Document._meta.get_field("public_premission_access").default == True


class TestDocumentView:
    def test_documentview_on_delete_cascade_true(self):
        field = DocumentView._meta.get_field("document")
        assert field.remote_field.on_delete == models.CASCADE

    def test_documentview_user_on_delete_cascade_true(self):
        field = DocumentView._meta.get_field("user")
        assert field.remote_field.on_delete == models.CASCADE

    def test_documentview_viewd_at_auto_now_add_True(self):
        assert DocumentView._meta.get_field("viewed_at").auto_now_add == True


class TestDocumentUpdate:
    def test_documentupdate_title_max_length_255(self):
        max_length = DocumentUpdate._meta.get_field("title").max_length
        assert max_length == 255

    def test_documentupdate_title_null_blank_true(self):
        assert DocumentUpdate._meta.get_field("title").null is True
        assert DocumentUpdate._meta.get_field("title").blank is True

    def test_documentupdate_document_on_delete_cascade(self):
        field = DocumentUpdate._meta.get_field("document")
        assert field.remote_field.on_delete == models.CASCADE

    def test_documentupdate_author_on_delete_set_null(self):
        field = DocumentUpdate._meta.get_field("author")
        assert field.remote_field.on_delete == models.SET_NULL

    def test_documentupdate_author_null_blank_true(self):
        assert DocumentUpdate._meta.get_field("author").null is True
        assert DocumentUpdate._meta.get_field("author").blank is True

    def test_documentupdate_authors_blank_true(self):
        assert DocumentUpdate._meta.get_field("authors").blank is True

class TestAccessLevel:
    def test_user_on_delete_cascade(self):
        field = AccessLevel._meta.get_field('user')
        assert field.remote_field.on_delete == models.CASCADE

    def test_document_on_delete_cascade(self):
        field = AccessLevel._meta.get_field("document")
        assert field.remote_field.on_delete == models.CASCADE

class TestComment:
    def test_comment_document_on_delete_cascade(self):
        field = Comment._meta.get_field("document")
        assert field.remote_field.on_delete == models.CASCADE

    def test_comment_author_on_delete_set_null(self):
        field = Comment._meta.get_field("author")
        assert field.remote_field.on_delete == models.SET_NULL

    def test_comment_author_null_true(self):
        assert Comment._meta.get_field("author").null == True

    def test_comment_resolved_by_on_delete_set_null(self):
        field = Comment._meta.get_field("resolved_by")
        assert field.remote_field.on_delete == models.SET_NULL

    def test_comment_resolved_by_null_true(self):
        assert Comment._meta.get_field("resolved_by").null == True

    def test_comment_resolved_at_null_blank_true(self):
        assert Comment._meta.get_field("resolved_at").null == True
        assert Comment._meta.get_field("resolved_at").blank == True


class TestCommentReply:
    def test_commentreply_comment_on_delete_cascade(self):
        field = CommentReply._meta.get_field("comment")
        assert field.remote_field.on_delete == models.CASCADE

    def test_commentreply_author_on_delete_set_null(self):
        field = CommentReply._meta.get_field("author")
        assert field.remote_field.on_delete == models.SET_NULL

    def test_commentreply_author_null_true(self):
        assert CommentReply._meta.get_field("author").null == True

    def test_commentreply_created_at_auto_now_add_true(self):
        assert CommentReply._meta.get_field("created_at").auto_now_add == True

    def test_commentreply_updated_at_auto_now_true(self):
        assert CommentReply._meta.get_field("updated_at").auto_now == True
