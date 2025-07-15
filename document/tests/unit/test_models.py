import pytest
from unittest.mock import Mock
from django.test import SimpleTestCase
from django.db import models
from django.contrib.auth import get_user_model
from model_bakery import baker
from document.models import *

User = get_user_model()


class TestDocumentDefinition(SimpleTestCase):
    # def test_document__str__(self):
    #     user = User()
    #     document = Document(title="new title", owner=user)
    #     self.assertEqual(str(document), "new title")

    def test_document_title_max_length(self):
        max_length = Document._meta.get_field("title").max_length
        self.assertEqual(max_length, 255)

    def test_document_title_default(self):
        default = Document._meta.get_field("title").default
        self.assertEqual(default, "سند بدون عنوان")

    def test_document_link_max_length(self):
        max_length = Document._meta.get_field("link").max_length
        self.assertEqual(max_length, 15)

    def test_document_link_unique_blank_true(self):
        self.assertTrue(Document._meta.get_field("link").unique)
        self.assertTrue(Document._meta.get_field("link").blank)

    def test_document_owner_null_blank_true(self):
        self.assertTrue(Document._meta.get_field("owner").null)
        self.assertTrue(Document._meta.get_field("owner").blank)

    def test_document_owner_on_delete_set_null(self):
        field = Document._meta.get_field("owner")
        self.assertEqual(field.remote_field.on_delete, models.SET_NULL)

    def test_document_created_at_auto_now_add_true(self):
        self.assertTrue(Document._meta.get_field("created_at").auto_now_add)

    def test_document_updated_at_auto_now_true(self):
        self.assertTrue(Document._meta.get_field("updated_at").auto_now)

    def test_document_uuid_editable_false(self):
        self.assertFalse(Document._meta.get_field("doc_uuid").editable)

    def test_document_uuid_unique_true(self):
        self.assertTrue(Document._meta.get_field("doc_uuid").unique)

    def test_document_is_public_default_False(self):
        self.assertFalse(Document._meta.get_field("is_public").default)

    def test_document_public_permission_access_default_True(self):
        self.assertTrue(Document._meta.get_field("public_premission_access").default)


class TestDocumentViewDefinition(SimpleTestCase):
    def test_documentview_on_delete_cascade_true(self):
        field = DocumentView._meta.get_field("document")
        self.assertEqual(field.remote_field.on_delete, models.CASCADE)

    def test_documentview_user_on_delete_cascade_true(self):
        field = DocumentView._meta.get_field("user")
        self.assertEqual(field.remote_field.on_delete, models.CASCADE)

    def test_documentview_viewd_at_auto_now_add_True(self):
        self.assertTrue(DocumentView._meta.get_field("viewed_at").auto_now_add)


class TestDocumentUpdateDefinition(SimpleTestCase):
    def test_documentupdate_title_max_length_255(self):
        max_length = DocumentUpdate._meta.get_field("title").max_length
        self.assertEqual(max_length, 255)

    def test_documentupdate_title_null_blank_true(self):
        self.assertTrue(DocumentUpdate._meta.get_field("title").null)
        self.assertTrue(DocumentUpdate._meta.get_field("title").blank)

    def test_documentupdate_document_on_delete_cascade(self):
        field = DocumentUpdate._meta.get_field("document")
        self.assertEqual(field.remote_field.on_delete, models.CASCADE)

    def test_documentupdate_author_on_delete_set_null(self):
        field = DocumentUpdate._meta.get_field("author")
        self.assertEqual(field.remote_field.on_delete, models.SET_NULL)

    def test_documentupdate_author_null_blank_true(self):
        self.assertTrue(DocumentUpdate._meta.get_field("author").null)
        self.assertTrue(DocumentUpdate._meta.get_field("author").blank)

    def test_documentupdate_authors_blank_true(self):
        self.assertTrue(DocumentUpdate._meta.get_field("authors").blank)


class TestAccessLevelDefinition(SimpleTestCase):
    def test_user_on_delete_cascade(self):
        field = AccessLevel._meta.get_field("user")
        self.assertEqual(field.remote_field.on_delete, models.CASCADE)

    def test_document_on_delete_cascade(self):
        field = AccessLevel._meta.get_field("document")
        self.assertEqual(field.remote_field.on_delete, models.CASCADE)


class TestCommentDefinition(SimpleTestCase):
    def test_comment_document_on_delete_cascade(self):
        field = Comment._meta.get_field("document")
        self.assertEqual(field.remote_field.on_delete, models.CASCADE)

    def test_comment_author_on_delete_set_null(self):
        field = Comment._meta.get_field("author")
        self.assertEqual(field.remote_field.on_delete, models.SET_NULL)

    def test_comment_author_null_true(self):
        self.assertTrue(Comment._meta.get_field("author").null)

    def test_comment_resolved_by_on_delete_set_null(self):
        field = Comment._meta.get_field("resolved_by")
        self.assertEqual(field.remote_field.on_delete, models.SET_NULL)

    def test_comment_resolved_by_null_true(self):
        self.assertTrue(Comment._meta.get_field("resolved_by").null)

    def test_comment_resolved_at_null_blank_true(self):
        self.assertTrue(Comment._meta.get_field("resolved_at").null)
        self.assertTrue(Comment._meta.get_field("resolved_at").blank)


class TestCommentReplyDefinition(SimpleTestCase):
    def test_commentreply_comment_on_delete_cascade(self):
        field = CommentReply._meta.get_field("comment")
        self.assertEqual(field.remote_field.on_delete, models.CASCADE)

    def test_commentreply_author_on_delete_set_null(self):
        field = CommentReply._meta.get_field("author")
        self.assertEqual(field.remote_field.on_delete, models.SET_NULL)

    def test_commentreply_author_null_true(self):
        self.assertTrue(CommentReply._meta.get_field("author").null)

    def test_commentreply_created_at_auto_now_add_true(self):
        self.assertTrue(CommentReply._meta.get_field("created_at").auto_now_add)

    def test_commentreply_updated_at_auto_now_true(self):
        self.assertTrue(CommentReply._meta.get_field("updated_at").auto_now)
