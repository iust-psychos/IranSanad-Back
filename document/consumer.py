import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from y_py import YDoc, apply_update, encode_state_as_update
from asgiref.sync import sync_to_async
from django.core.exceptions import ObjectDoesNotExist
from .models import Document, DocumentUpdate

logger = logging.getLogger(__name__)

class DocumentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Check if the document UUID is valid
        self.doc_uuid = self.scope['url_route']['kwargs'].get('doc_uuid')
        if not self.doc_uuid:
            logger.error("Invalid document UUID.")
            await self.close()
            return
        try:
            self.document = await Document.objects.aget(doc_uuid=self.doc_uuid)
        except Document.DoesNotExist:
            logger.error(f"Document with UUID {self.doc_uuid} does not exist.")
            await self.close()
            return        
        self.doc_uuid = self.scope['url_route']['kwargs']['doc_uuid']
        self.room_group_name = f'document_{self.doc_uuid}'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # send content of document to client
        # log the content of the document
        logger.info(f"Document content: {bytes(self.document.content)}")
        if self.document.content:
            await self.send(bytes_data=bytes(self.document.content))
        logger.info(f"WebSocket connection established for document {self.doc_uuid} from {self.channel_name}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        # check if data is ypy support or not
        if bytes_data is None:
            logger.error("Received non-Yjs update.")
            return  # Ignore non-Yjs updates

        # Broadcast to all clients except sender
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'yjs.update',
                'bytes': bytes_data,
                'sender_channel': self.channel_name,
            }
        )

        # Apply update to DB
        await self.apply_update_to_doc(self.doc_uuid, bytes_data)

    async def yjs_update(self, event):
        if event['sender_channel'] == self.channel_name:
            return  # Ignore updates sent by the sender

        await self.send(bytes_data=event['bytes'])

    @sync_to_async
    def apply_update_to_doc(self, doc_uuid, update_bytes):
        try:
            logger.info(f"Applying update to document {doc_uuid}")
            logger.info(f"Update bytes: {update_bytes}")
            document = Document.objects.get(doc_uuid=doc_uuid)

            ydoc = YDoc()
            if document.content:
                apply_update(ydoc, document.content)
            logger.info(f"Applying update to YDoc: {ydoc}")
            apply_update(ydoc, update_bytes)
            logger.info(f"YDoc after applying update: {ydoc}")
            DocumentUpdate.objects.create(document=document, update_data=update_bytes)
            logger.info(f"Encoded state as update: {encode_state_as_update(ydoc)}")
            document.content = encode_state_as_update(ydoc)
            document.save()
            logger.info(f"Update applied to document {doc_uuid} and saved to DB.")
        except ObjectDoesNotExist:
            logger.error(f"Document with UUID {doc_uuid} does not exist.")
        except Exception as e:
            logger.error(f"Error applying update to document {doc_uuid}: {e}")