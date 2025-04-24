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
        self.doc_uuid = self.scope['url_route']['kwargs']['doc_uuid']
        self.room_group_name = f'document_{self.doc_uuid}'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        logger.info(f"WebSocket connection established for document {self.doc_uuid} from {self.channel_name}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if not bytes_data:
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
            document = Document.objects.get(doc_uuid=doc_uuid)

            ydoc = YDoc()
            if document.content:
                apply_update(ydoc, document.content)

            apply_update(ydoc, update_bytes)

            DocumentUpdate.objects.create(document=document, update_data=update_bytes)

            document.content = encode_state_as_update(ydoc)
            document.save()
        except ObjectDoesNotExist:
            logger.error(f"Document with UUID {doc_uuid} does not exist.")
        except Exception as e:
            logger.error(f"Error applying update to document {doc_uuid}: {e}")