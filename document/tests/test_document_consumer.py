import asyncio
import pytest
from channels.testing import WebsocketCommunicator
from asgiref.sync import sync_to_async
from django.test import TransactionTestCase
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


class TestDocumentConsumer(TransactionTestCase):
    async def test_connect_and_disconnect(self):
        # Create a document
        doc = await Document.objects.acreate()
        # Connect client
        communicator = WebsocketCommunicator(application, f"/ws/docs/{doc.doc_uuid}/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Disconnect client
        await communicator.disconnect()

    async def test_invalid_document_uuid(self):
        invalid_uuid = str(uuid.uuid4())  
        communicator = WebsocketCommunicator(application, f"/ws/docs/{invalid_uuid}/")
        connected, _ = await communicator.connect()
        self.assertFalse(connected)

    async def test_broadcast_update_for_2_clients(self):
        doc = await Document.objects.acreate()
        # Connect client 1
        communicator_1 = WebsocketCommunicator(application, f"/ws/docs/{doc.doc_uuid}/")
        connected_1, _ = await communicator_1.connect()
        self.assertTrue(connected_1)

        # Connect client 2
        communicator_2 = WebsocketCommunicator(application, f"/ws/docs/{doc.doc_uuid}/")
        connected_2, _ = await communicator_2.connect()
        self.assertTrue(connected_2)

        # Generate binary Yjs update
        yjs_bytes = get_yjs_update_bytes("Broadcast test")

        # Send update from client 1
        await communicator_1.send_to(bytes_data=yjs_bytes)

        # Receive update on client 2
        response = await communicator_2.receive_from()
        self.assertEqual(response, yjs_bytes)
        
        # Confirm client 1 does not receive its own update
        try:
            response = await communicator_1.receive_from(timeout=0.1)
            self.fail("Client 1 should not receive its own update.")
        except asyncio.TimeoutError:
            pass
        

    async def test_broadcast_update_for_3_clients(self):
        doc = await Document.objects.acreate()
        # Connect client 1
        communicator_1 = WebsocketCommunicator(application, f"/ws/docs/{doc.doc_uuid}/")
        connected_1, _ = await communicator_1.connect()
        self.assertTrue(connected_1)

        # Connect client 2
        communicator_2 = WebsocketCommunicator(application, f"/ws/docs/{doc.doc_uuid}/")
        connected_2, _ = await communicator_2.connect()
        self.assertTrue(connected_2)

        # Connect client 3
        communicator_3 = WebsocketCommunicator(application, f"/ws/docs/{doc.doc_uuid}/")
        connected_3, _ = await communicator_3.connect()
        self.assertTrue(connected_3)

        # Generate binary Yjs update
        yjs_bytes = get_yjs_update_bytes("Broadcast test")

        # Send update from client 1
        await communicator_1.send_to(bytes_data=yjs_bytes)

        # Receive update on client 2
        response = await communicator_2.receive_from()
        self.assertEqual(response, yjs_bytes)
        
        # Confirm client 1 does not receive its own update
        try:
            response = await communicator_1.receive_from(timeout=0.1)
            self.fail("Client 1 should not receive its own update.")
        except asyncio.TimeoutError:
            pass

        # Receive update on client 3
        response = await communicator_3.receive_from()
        self.assertEqual(response, yjs_bytes)


    async def test_document_model_content_saved_after_client_update(self):
        doc = await Document.objects.acreate()
        communicator = WebsocketCommunicator(application, f"/ws/docs/{doc.doc_uuid}/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        yjs_bytes = get_yjs_update_bytes("Test content")
        await communicator.send_to(bytes_data=yjs_bytes)

        # Wait for the update to be processed
        await asyncio.sleep(1)
        
        document = await Document.objects.aget(doc_uuid=doc.doc_uuid)
        
        self.assertEqual(bytes(document.content), yjs_bytes)
        
    
        
