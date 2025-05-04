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

        ydoc = YDoc()
        updates = await sync_to_async(list)(
        DocumentUpdate.objects.filter(document=self.document)
                              .order_by("created_at")
                              .values_list("update_data", flat=True)
        )
        for u in updates:
            apply_update(ydoc, u)

        # send the one-time full snapshot to the client
        full_snapshot = encode_state_as_update(ydoc)
        await self.send(bytes_data=full_snapshot)
        
        self.last_seen = await DocumentView.objects.acreate(
            document=self.document,
            user=self.user
        )
        logger.info(f"Document viewed by user: {self.user} for document {self.document.doc_uuid}")

        

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
        if b'"anchorPos"' in bytes_data or b'"awareness"' in bytes_data:
            logger.info("Received awareness or anchor position update.")
        else:
            logger.info("Received Yjs update.")
            document = await Document.objects.aget(doc_uuid=self.doc_uuid)
            await DocumentUpdate.objects.acreate(document=document, update_data=bytes_data)

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
                logger.info(f"Document content: {bytes(document.content)}")
                apply_update(ydoc, bytes(document.content))
            logger.info(f"Encoded state as update before add new update(just perv content): {encode_state_as_update(ydoc)}")
            logger.info(f"Update bytes: {update_bytes}")
            # check if update_bytes is not empty and valid
            if update_bytes and len(update_bytes) > 0:
                logger.info(f"Applying update to YDoc.")
                apply_update(ydoc, update_bytes)
            logger.info(f"Encoded state as update after add new update: {encode_state_as_update(ydoc)}")
            DocumentUpdate.objects.create(document=document, update_data=update_bytes)
            logger.info(f"Encoded state as update: {encode_state_as_update(ydoc)}")
            document.content = encode_state_as_update(ydoc)
            document.save()
            logger.info(f"Update applied to document {doc_uuid} and saved to DB.")
            logger.info(f"Document content after update: {bytes(document.content)}")
        except ObjectDoesNotExist:
            logger.error(f"Document with UUID {doc_uuid} does not exist.")
        except Exception as e:
            logger.error(f"Error applying update to document {doc_uuid}: {e}")