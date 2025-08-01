import asyncio
import pytest
import uuid
from unittest.mock import Mock
from django.contrib.auth import get_user_model
from iransanad.asgi import application
from asgiref.sync import sync_to_async
from document.models import Document, DocumentUpdate
from rest_framework_simplejwt.tokens import AccessToken
from y_py import YDoc, encode_state_as_update, encode_state_vector, apply_update
from ypy_websocket.yutils import (
    YMessageType,
    process_sync_message,
    read_message,
    YSyncMessageType,
    create_sync_step2_message,
    create_sync_step1_message,
)
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from model_bakery import baker
from logging import getLogger

logger = getLogger()

User = get_user_model()


# @pytest.fixture
# def user():
#     return User.objects.create(username="username")


def get_yjs_update_bytes(initial_text="Hello"):
    ydoc = YDoc()
    with ydoc.begin_transaction() as txn:
        ytext = ydoc.get_text("shared")
        ytext.insert(txn, 0, initial_text)
    return encode_state_as_update(ydoc)


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class TestDocumentConsumer:
    async def test_connect_and_disconnect(self, user_token_tuple):
        user, token = user_token_tuple
        doc = await Document.objects.acreate(owner=user)

        communicator = WebsocketCommunicator(
            application, f"/ws/docs/{doc.doc_uuid}/1/?Authorization={token}"
        )
        connected, _ = await communicator.connect()
        assert connected
        await communicator.disconnect()

    async def test_invalid_document_uuid(self, user_token_tuple):
        user, token = user_token_tuple
        invalid_uuid = str(uuid.uuid4())
        communicator = WebsocketCommunicator(
            application, f"/ws/docs/{invalid_uuid}/1/?Authorization={token}"
        )
        connected, _ = await communicator.connect()
        assert not connected

    async def test_two_users_access(self):
        user1 = await User.objects.acreate(username="user1", email="user1@example.com")
        user2 = await User.objects.acreate(username="user2", email="user2@example.com")
        token1 = str(await database_sync_to_async(AccessToken.for_user)(user1))
        token2 = str(await database_sync_to_async(AccessToken.for_user)(user2))

        doc = await Document.objects.acreate(owner=user1)
        communicator1 = WebsocketCommunicator(
            application, f"/ws/docs/{doc.doc_uuid}/1/?Authorization={token1}"
        )
        # communicator1.scope["user"] = user1
        connected1, _ = await communicator1.connect()
        assert connected1
        communicator2 = WebsocketCommunicator(
            application, f"/ws/docs/{doc.doc_uuid}/1/?Authorization={token2}"
        )
        # communicator2.scope["user"] = user2
        connected2, _ = await communicator2.connect()
        assert connected2
        await communicator1.disconnect()
        await communicator2.disconnect()

    async def test_update_received_when_user_joins(self):
        # Create two users and their tokens
        user = await database_sync_to_async(baker.make)(User)
        token = str(await database_sync_to_async(AccessToken.for_user)(user))

        # Create a document and an update
        doc = await Document.objects.acreate(owner=user)
        update_data = get_yjs_update_bytes("test_update_received_when_user_joins")
        doc_update = await DocumentUpdate.objects.acreate(
            document=doc, page=1, update_data=update_data
        )
        ydoc1 = YDoc()
        apply_update(ydoc1, doc_update.update_data)
        assert isinstance(doc_update.update_data, bytes)

        # Create a communicator and establish connection
        communicator1 = WebsocketCommunicator(
            application, f"/ws/docs/{doc.doc_uuid}/1/?Authorization={token}"
        )
        connected1, _ = await communicator1.connect()
        assert connected1
        asyncio.sleep(2)

        # await communicator1.receive_from()  # Initial SYNC message
        response = await communicator1.receive_from()
        state = encode_state_vector(ydoc1)
        msg = create_sync_step1_message(state)
        assert response == msg

    # async def test_user_document_update_save_successfully(self):
    #     user = await database_sync_to_async(baker.make)(User)
    #     doc = await Document.objects.acreate(owner=user)
    #     token = str(await database_sync_to_async(AccessToken.for_user)(user))
    #     communicator = WebsocketCommunicator(
    #         application, f"/ws/docs/{doc.doc_uuid}/1/?Authorization={token}"
    #     )
    #     communicator.scope["user"] = user
    #     connected, _ = await communicator.connect()
    #     assert connected
    #     yjs_bytes = get_yjs_update_bytes("test_user_document_update_save_successfully")
    #     ydoc1 = YDoc()
    #     apply_update(ydoc1, yjs_bytes)

    #     reply = create_sync_step2_message(yjs_bytes)
    #     await communicator.send_to(bytes_data=reply)
    #     asyncio.sleep(2)

    #     doc_updates = sync_to_async(
    #         lambda: list(
    #             DocumentUpdate.objects.filter(document=doc, page=1)
    #             .order_by("created_at")
    #             .all()
    #         )
    #     )
    #     document_updates = await doc_updates()

    #     ydoc2 = YDoc()
    #     for doc_update in document_updates:
    #         update_data = doc_update.update_data
    #         apply_update(ydoc2, update_data)

    #     assert len(document_updates)
    #     assert encode_state_vector(ydoc1) == encode_state_vector(ydoc2)

    #     await communicator.disconnect()

    async def test_user_receives_comment_updates(self):
        user1, user2 = await database_sync_to_async(baker.make)(User, _quantity=2)
        token1 = str(await database_sync_to_async(AccessToken.for_user)(user1))
        token2 = str(await database_sync_to_async(AccessToken.for_user)(user2))
        doc = await Document.objects.acreate(owner=user1)

        communicator1 = WebsocketCommunicator(
            application, f"/ws/docs/{doc.doc_uuid}/1/?Authorization={token1}"
        )
        communicator2 = WebsocketCommunicator(
            application, f"/ws/docs/{doc.doc_uuid}/1/?Authorization={token2}"
        )
        connected1, _ = await communicator1.connect()
        connected2, _ = await communicator2.connect()
        assert connected1 and connected2

        await communicator1.receive_from()  # Init SYNC message
        await communicator2.receive_from()  # Init SYNC message

        data1 = {"type": "comment_created", "data": "test data"}
        data2 = {"type": "comment_updated", "data": "test data"}
        data3 = {"type": "comment_deleted", "data": "test data"}

        await communicator1.send_json_to(data1)
        response1 = await communicator2.receive_json_from()
        await communicator1.send_json_to(data2)
        response2 = await communicator2.receive_json_from()
        await communicator1.send_json_to(data3)
        response3 = await communicator2.receive_json_from(timeout=20)

        assert response1 == data1
        assert response2 == data2
        assert response3 == data3

        await communicator1.disconnect()
        await communicator2.disconnect()

    async def test_receive_commentreply_updates(self):
        user1, user2 = await database_sync_to_async(baker.make)(User, _quantity=2)
        token1 = str(await database_sync_to_async(AccessToken.for_user)(user1))
        token2 = str(await database_sync_to_async(AccessToken.for_user)(user2))
        doc = await Document.objects.acreate(owner=user1)

        communicator1 = WebsocketCommunicator(
            application, f"/ws/docs/{doc.doc_uuid}/1/?Authorization={token1}"
        )
        communicator2 = WebsocketCommunicator(
            application, f"/ws/docs/{doc.doc_uuid}/1/?Authorization={token2}"
        )

        connected1, _ = await communicator1.connect()
        connected2, _ = await communicator2.connect()

        assert connected1 and connected2
        await communicator1.receive_from()  # Init SYNC message
        await communicator2.receive_from()  # Init SYNC message

        data1 = {"type": "reply_created", "data": "test reply data"}
        data2 = {"type": "reply_updated", "data": "test reply data"}
        data3 = {"type": "reply_deleted", "data": "test reply data"}

        await communicator1.send_json_to(data1)
        response1 = await communicator2.receive_json_from()
        await communicator1.send_json_to(data2)
        response2 = await communicator2.receive_json_from()
        await communicator1.send_json_to(data3)
        response3 = await communicator2.receive_json_from()

        assert response1 == data1
        assert response2 == data2
        assert response3 == data3

        await communicator1.disconnect()
        await communicator2.disconnect()

    # async def test_spell_grammar_check_working(self):
    #     user = await database_sync_to_async(baker.make)(User)
    #     token = await database_sync_to_async(AccessToken.for_user)(user)
    #     doc = await Document.objects.acreate(owner=user)
    #     communicator = WebsocketCommunicator(
    #         application, f"/ws/docs/{doc.doc_uuid}/1/?Authorization={token}"
    #     )
    #     connected, _ = await communicator.connect()
    #     assert connected

    #     data1 = {"type": "SpellCheck"}
    #     data2 = {"type": "GrammarCheck"}

    #     await communicator.receive_from()  # Init SYNC

    #     await communicator.send_json_to(data1)
    #     asyncio.sleep(5)  # Wait for processing
    #     response1 = await communicator.receive_json_from()
    #     await communicator.send_json_to(data2)
    #     asyncio.sleep(5)  # Wait for processing
    #     response2 = await communicator.receive_json_from()

    #     assert "Spell" in response1
    #     assert "Grammar" in response2

    # async def test_broadcast_update_for_two_users(self):
    #     user1 = await User.objects.acreate(username="user1", email="user1@example.com")
    #     user2 = await User.objects.acreate(username="user2", email="user2@example.com")
    #     token1, token2 = str(AccessToken.for_user(user1)), str(
    #         AccessToken.for_user(user2)
    #     )
    #     doc = await Document.objects.acreate(owner=user1)

    #     communicator1 = WebsocketCommunicator(
    #         application, f"/ws/docs/{doc.doc_uuid}/1/?Authorization={token1}"
    #     )
    #     connected1, _ = await communicator1.connect()
    #     response = await communicator1.receive_from()
    #     assert response[0] == YMessageType.SYNC

    #     communicator2 = WebsocketCommunicator(
    #         application, f"/ws/docs/{doc.doc_uuid}/1/?Authorization={token2}"
    #     )
    #     connected2, _ = await communicator2.connect()
    #     response = await communicator2.receive_from()
    #     assert response[0] == YMessageType.SYNC

    #     assert connected1 and connected2

    #     data = {"type": "default", "message": "test data"}

    #     await communicator1.send_json_to(data)
    #     response = await communicator2.receive_json_from(timeout=20)
    #     assert response == data

    #     await communicator1.disconnect()
    #     await communicator2.disconnect()
