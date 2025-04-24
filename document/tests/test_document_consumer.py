import asyncio
import pytest
from channels.testing import WebsocketCommunicator
from iransanad.asgi import application
from document.models import Document
from y_py import YDoc, encode_state_as_update
import uuid


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
        doc = await Document.objects.acreate()

        communicator = WebsocketCommunicator(application, f"/ws/docs/{doc.doc_uuid}/?Authorization={token}")
        connected, _ = await communicator.connect()
        assert connected
        await communicator.disconnect()

    async def test_invalid_document_uuid(self, user_token_tuple):
        user, token = user_token_tuple
        invalid_uuid = str(uuid.uuid4())
        communicator = WebsocketCommunicator(application, f"/ws/docs/{invalid_uuid}/?Authorization={token}")
        connected, _ = await communicator.connect()
        assert not connected

    async def test_broadcast_update_for_2_clients(self, user_token_tuple):
        user, token = user_token_tuple
        doc = await Document.objects.acreate()

        communicator_1 = WebsocketCommunicator(application, f"/ws/docs/{doc.doc_uuid}/?Authorization={token}")
        connected_1, _ = await communicator_1.connect()
        assert connected_1

        communicator_2 = WebsocketCommunicator(application, f"/ws/docs/{doc.doc_uuid}/?Authorization={token}")
        connected_2, _ = await communicator_2.connect()
        assert connected_2

        yjs_bytes = get_yjs_update_bytes("Broadcast test")
        await communicator_1.send_to(bytes_data=yjs_bytes)

        response = await communicator_2.receive_from()
        assert isinstance(response, bytes)
        assert response == yjs_bytes

        try:
            await communicator_1.receive_from(timeout=0.1)
            pytest.fail("Client 1 should not receive its own update.")
        except asyncio.TimeoutError:
            pass

        await communicator_1.disconnect()
        await communicator_2.disconnect()

    async def test_broadcast_update_for_3_clients(self, user_token_tuple):
        user, token = user_token_tuple
        doc = await Document.objects.acreate()

        communicator_1 = WebsocketCommunicator(application, f"/ws/docs/{doc.doc_uuid}/?Authorization={token}")
        connected_1, _ = await communicator_1.connect()
        assert connected_1

        communicator_2 = WebsocketCommunicator(application, f"/ws/docs/{doc.doc_uuid}/?Authorization={token}")
        connected_2, _ = await communicator_2.connect()
        assert connected_2

        communicator_3 = WebsocketCommunicator(application, f"/ws/docs/{doc.doc_uuid}/?Authorization={token}")
        connected_3, _ = await communicator_3.connect()
        assert connected_3

        yjs_bytes = get_yjs_update_bytes("Broadcast test")
        await communicator_1.send_to(bytes_data=yjs_bytes)

        response = await communicator_2.receive_from()
        assert response == yjs_bytes

        try:
            await communicator_1.receive_from(timeout=0.1)
            pytest.fail("Client 1 should not receive its own update.")
        except asyncio.TimeoutError:
            pass

        response = await communicator_3.receive_from()
        assert response == yjs_bytes

        await communicator_1.disconnect()
        await communicator_2.disconnect()
        await communicator_3.disconnect()

    async def test_document_model_content_saved_after_client_update(self, user_token_tuple):
        user, token = user_token_tuple
        doc = await Document.objects.acreate()
        communicator = WebsocketCommunicator(application, f"/ws/docs/{doc.doc_uuid}/?Authorization={token}")
        connected, _ = await communicator.connect()
        assert connected

        yjs_bytes = get_yjs_update_bytes("Test content")
        await communicator.send_to(bytes_data=yjs_bytes)

        await asyncio.sleep(1)
        document = await Document.objects.aget(doc_uuid=doc.doc_uuid)
        assert bytes(document.content) == yjs_bytes

        await communicator.disconnect()

    async def test_reconnect_and_receive_initial_content(self, user_token_tuple):
        user, token = user_token_tuple
        doc = await Document.objects.acreate()
        communicator_1 = WebsocketCommunicator(application, f"/ws/docs/{doc.doc_uuid}/?Authorization={token}")
        connected, _ = await communicator_1.connect()
        assert connected

        yjs_bytes = get_yjs_update_bytes("Test content")
        await communicator_1.send_to(bytes_data=yjs_bytes)
        await asyncio.sleep(1)
        await communicator_1.disconnect()
        await asyncio.sleep(1)

        communicator_2 = WebsocketCommunicator(application, f"/ws/docs/{doc.doc_uuid}/?Authorization={token}")
        connected, _ = await communicator_2.connect()
        assert connected

        try:
            response = await communicator_2.receive_from()
        except asyncio.TimeoutError:
            pytest.fail("No content received after reconnecting.")
        assert response == yjs_bytes

        await communicator_2.disconnect()

    async def test_send_non_yjs_update(self, user_token_tuple):
        user, token = user_token_tuple
        doc = await Document.objects.acreate()
        communicator = WebsocketCommunicator(application, f"/ws/docs/{doc.doc_uuid}/?Authorization={token}")
        connected, _ = await communicator.connect()
        assert connected

        await communicator.send_to(text_data="Non-Yjs update")

        try:
            await communicator.receive_from(timeout=0.1)
            pytest.fail("Client should not receive a response for non-Yjs update.")
        except asyncio.TimeoutError:
            pass

        await communicator.disconnect()

    async def test_send_empty_update(self, user_token_tuple):
        user, token = user_token_tuple
        doc = await Document.objects.acreate()
        communicator = WebsocketCommunicator(application, f"/ws/docs/{doc.doc_uuid}/?Authorization={token}")
        connected, _ = await communicator.connect()
        assert connected

        try:
            await communicator.send_to(bytes_data=b"")
            pytest.fail("Client should not receive a response for empty update.")
        except (asyncio.TimeoutError, AssertionError):
            pass

        await communicator.disconnect()

    async def test_if_add_data_then_reconnect_broadcast_to_2_clients(self, user_token_tuple):
        user, token = user_token_tuple
        doc = await Document.objects.acreate()
        communicator_1 = WebsocketCommunicator(application, f"/ws/docs/{doc.doc_uuid}/?Authorization={token}")
        connected, _ = await communicator_1.connect()
        assert connected

        yjs_bytes = get_yjs_update_bytes("Test content")
        await communicator_1.send_to(bytes_data=yjs_bytes)
        await communicator_1.disconnect()

        communicator_1 = WebsocketCommunicator(application, f"/ws/docs/{doc.doc_uuid}/?Authorization={token}")
        connected, _ = await communicator_1.connect()
        assert connected

        try:
            response = await communicator_1.receive_from()
            assert response == yjs_bytes
        except asyncio.TimeoutError:
            pytest.fail("No content received after reconnecting.")

        communicator_2 = WebsocketCommunicator(application, f"/ws/docs/{doc.doc_uuid}/?Authorization={token}")
        connected_2, _ = await communicator_2.connect()
        assert connected_2

        try:
            response = await communicator_2.receive_from()
            assert response == yjs_bytes
        except asyncio.TimeoutError:
            pytest.fail("No content received after reconnecting.")

        yjs_bytes = get_yjs_update_bytes("Test content")
        await communicator_1.send_to(bytes_data=yjs_bytes)

        try:
            response = await communicator_2.receive_from()
            assert response == yjs_bytes
        except asyncio.TimeoutError:
            pytest.fail("No content received after reconnecting.")

        try:
            await communicator_1.receive_from()
            pytest.fail("Client 1 should not receive its own update.")
        except asyncio.TimeoutError:
            pass

        await communicator_1.disconnect()
        await communicator_2.disconnect()
