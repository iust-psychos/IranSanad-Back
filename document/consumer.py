import json
import logging
import django
django.setup()
from django.utils import timezone
from channels.generic.websocket import AsyncWebsocketConsumer
from y_py import YDoc, apply_update, encode_state_as_update
from asgiref.sync import sync_to_async
from django.core.exceptions import ObjectDoesNotExist
from .models import Document, DocumentUpdate, DocumentView

logger = logging.getLogger(__name__)

class DocumentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Check if the document UUID is valid
        self.doc_uuid = self.scope['url_route']['kwargs'].get('doc_uuid')
        self.user = self.scope['user']
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
        self.room_group_name = f'document_{self.doc_uuid}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        
        self.last_seen = await DocumentView.objects.acreate(
            document=self.document,
            user=self.user
        )
        logger.info(f"Document viewed by user: {self.user} for document {self.document.doc_uuid}")
        
        self.ydoc = YDoc() 
        if self.document.content:
            apply_update(self.ydoc, bytes(self.document.content))

        

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        # update the last seen time for the user by self.last_seen
        if self.last_seen:
            self.last_seen.created_at = timezone.now()
            await sync_to_async(self.last_seen.save)()
        else:
            logger.error(f"DocumentView object not found for user {self.user} and document {self.document.doc_uuid}")
            await DocumentView.objects.acreate(
                document=self.document,
                user=self.user
            )
        self.document.content = await sync_to_async(encode_state_as_update)(self.ydoc)
        await self.document.asave(update_fields=['content'])

        

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

        if b'"anchorPos"' in bytes_data or b'"awareness"' in bytes_data or b'"awarenessStates"' in bytes_data:
            logger.info("Received awareness or anchor position update.")
        else:
            logger.info("Received Yjs update.")
            await self.apply_update_to_doc(bytes_data)


    async def yjs_update(self, event):
        if event['sender_channel'] == self.channel_name:
            return  # Ignore updates sent by the sender

        await self.send(bytes_data=event['bytes'])

    def apply_update_to_doc(self, update_bytes):
        logger.info(f"Update bytes: {update_bytes}")
        apply_update(self.ydoc, update_bytes)
        
            
            