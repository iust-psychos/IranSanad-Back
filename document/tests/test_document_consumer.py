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
        assert isinstance(response, bytes), "Binary frame payload is not bytes"
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

        
    
    async def test_reconnect_and_receive_initial_content(self):
        doc = await Document.objects.acreate()
        communicator_1 = WebsocketCommunicator(application, f"/ws/docs/{doc.doc_uuid}/")
        connected, _ = await communicator_1.connect()
        self.assertTrue(connected)
        
        yjs_bytes = get_yjs_update_bytes("Test content")
        await communicator_1.send_to(bytes_data=yjs_bytes)

        # Wait for the update to be processed
        await asyncio.sleep(1)

        # Disconnect the first client
        await communicator_1.disconnect()
    
        await asyncio.sleep(1)
        # Reconnect the first client
        communicator_2 = WebsocketCommunicator(application, f"/ws/docs/{doc.doc_uuid}/")
        connected, _ = await communicator_2.connect()
        self.assertTrue(connected)
        
        # Receive initial content
        try:
            response = await communicator_2.receive_from()
        except asyncio.TimeoutError:
            self.fail("No content received after reconnecting.")
        self.assertEqual(response, yjs_bytes)
        
        
    async def test_send_non_yjs_update(self):
        doc = await Document.objects.acreate()
        communicator = WebsocketCommunicator(application, f"/ws/docs/{doc.doc_uuid}/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Send non-Yjs update
        await communicator.send_to(text_data="Non-Yjs update")

        # Receive response
        try:
            response = await communicator.receive_from(timeout=0.1)
            self.fail("Client should not receive a response for non-Yjs update.")
        except asyncio.TimeoutError:
            pass
        
        
    async def test_send_empty_update(self):
        doc = await Document.objects.acreate()
        communicator = WebsocketCommunicator(application, f"/ws/docs/{doc.doc_uuid}/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        try:
            response =  await communicator.send_to(bytes_data=b"")
            self.fail("Client should not receive a response for empty update.")
        except (asyncio.TimeoutError, AssertionError):
            pass
        
        
    async def test_if_add_data_then_reconnect_broadcast_to_2_clients(self):
        doc = await Document.objects.acreate()
        communicator_1 = WebsocketCommunicator(application, f"/ws/docs/{doc.doc_uuid}/")
        connected, _ = await communicator_1.connect()
        self.assertTrue(connected)
        
        yjs_bytes = get_yjs_update_bytes("Test content")
        await communicator_1.send_to(bytes_data=yjs_bytes)

        # Disconnect the first client
        await communicator_1.disconnect()
    
        # Reconnect the first client
        communicator_1 = WebsocketCommunicator(application, f"/ws/docs/{doc.doc_uuid}/")
        connected, _ = await communicator_1.connect()
        self.assertTrue(connected)
        
        # Receive initial content
        try:
            response = await communicator_1.receive_from()
            self.assertEqual(response, yjs_bytes)
        except asyncio.TimeoutError:
            self.fail("No content received after reconnecting.")
        
        # Connect client 2
        communicator_2 = WebsocketCommunicator(application, f"/ws/docs/{doc.doc_uuid}/")
        connected_2, _ = await communicator_2.connect()
        self.assertTrue(connected_2)
        
        # Receive update on client 2
        try:
            response = await communicator_2.receive_from()
            self.assertEqual(response, yjs_bytes)
        except asyncio.TimeoutError:
            self.fail("No content received after reconnecting.")
            
        # client 1 make new update
        yjs_bytes = get_yjs_update_bytes("Test content")
        await communicator_1.send_to(bytes_data=yjs_bytes)
        
        # Receive update on client 2
        try:
            response = await communicator_2.receive_from()
            self.assertEqual(response, yjs_bytes)
        except asyncio.TimeoutError:
            self.fail("No content received after reconnecting.")

        try:
            response = await communicator_1.receive_from()
            self.fail("Client 1 should not receive its own update.")
        except asyncio.TimeoutError:
            pass
        await communicator_1.disconnect()
        await communicator_2.disconnect()
        
