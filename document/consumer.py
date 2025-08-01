import json
import logging
import django

django.setup()
from django.utils import timezone
from django.conf import settings
from channels.generic.websocket import AsyncWebsocketConsumer
from y_py import YDoc, apply_update, encode_state_as_update, encode_state_vector
from asgiref.sync import sync_to_async
from django.core.exceptions import ObjectDoesNotExist
from .models import Document, DocumentUpdate, DocumentView
from ypy_websocket.yutils import (
    create_sync_step1_message,
    create_sync_step2_message,
    YMessageType,
    YSyncMessageType,
    read_message,
)
from document.spell_grammar_checker.spell_grammar_checker import SpellGrammarChecker

logger = logging.getLogger(__name__)

GROQ_API_KEY = settings.GROQ_API_KEY


class DocumentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Check if the document UUID is valid
        self.doc_uuid = self.scope["url_route"]["kwargs"].get("doc_uuid")
        self.page = self.scope["url_route"]["kwargs"].get("page", 1)
        self.user = self.scope["user"]
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
        self.room_group_name = f"document_{self.doc_uuid}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        self.last_seen = await DocumentView.objects.acreate(
            document=self.document, user=self.user
        )
        logger.info(
            f"Document viewed by user: {self.user} for document {self.document.doc_uuid}"
        )

        self.ydoc = YDoc()

        document_updates = sync_to_async(
            lambda: list(
                DocumentUpdate.objects.filter(document=self.document, page=self.page)
                .order_by("created_at")
                .all()
            )
        )
        document_updates = await document_updates()
        for document_update in document_updates:
            update_data = (
                bytes(document_update.update_data)
                if isinstance(document_update.update_data, memoryview)
                else document_update.update_data
            )
            if not isinstance(update_data, bytes):
                logger.error(
                    f"Invalid update_data type: {type(update_data)}, value: {update_data}"
                )
                continue
            try:
                apply_update(self.ydoc, update_data)
            except Exception as e:
                logger.error(f"Error applying update: {e}")

        state = encode_state_vector(self.ydoc)
        msg = create_sync_step1_message(state)
        await self.send(bytes_data=msg)
        AI_MODEL = "llama-3.3-70b-versatile"
        self.spellgrammarcheck = SpellGrammarChecker(GROQ_API_KEY, AI_MODEL)

    async def send_message(self, type: str, text_data=None, bytes_data=None):
        if text_data:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": type,
                    "text_data": text_data,
                    "sender_channel": self.channel_name,
                },
            )

        if bytes_data:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": type,
                    "bytes": bytes_data,
                    "sender_channel": self.channel_name,
                },
            )

    async def spell_check(self, event):

        await self.send(text_data=event["text_data"])

    async def comment_commentreply_sync(self, event):
        if event["sender_channel"] == self.channel_name:
            return  # Ignore updates sent by the sender

        await self.send(text_data=event["text_data"])

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        # update the last seen time for the user by self.last_seen
        if self.last_seen:
            self.last_seen.created_at = timezone.now()
            await sync_to_async(self.last_seen.save)()
        else:
            logger.error(
                f"DocumentView object not found for user {self.user} and document {self.document.doc_uuid}"
            )
            await DocumentView.objects.acreate(document=self.document, user=self.user)

    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            if eval(text_data)["type"] in ["SpellCheck", "GrammarCheck"]:
                ydoc_text = " ".join(self.ydoc.get_array("root"))
                logger.info(ydoc_text)
                spell_checked_data = self.spellgrammarcheck.spell_check(ydoc_text)
                grammar_checked_data = self.spellgrammarcheck.grammar_check(ydoc_text)
                merged_data = (
                    "{"
                    + f'"Spell":{await spell_checked_data},'
                    + f'"Grammar":{await grammar_checked_data}'
                    + "}"
                )
                await self.send_message(type="spell_check", text_data=merged_data)
            elif eval(text_data)["type"] in [
                "comment_created",
                "comment_updated",
                "comment_deleted",
                "reply_created",
                "reply_updated",
                "reply_deleted",
            ]:
                await self.send_message(
                    type="comment_commentreply_sync", text_data=text_data
                )
            else:
                await self.send_message(type="default_send", text_data=text_data)

        if bytes_data:
            await self.send_message(type="default_send", bytes_data=bytes_data)
            update = await self.process_message(bytes_data, self.ydoc)
            # Save update to Database
            if update:
                document_update = await DocumentUpdate.objects.acreate(
                    document=self.document,
                    update_data=update,
                    author=self.user,
                    page=self.page,
                )
                await sync_to_async(document_update.save)()

    async def process_message(self, message: bytes, ydoc: YDoc):
        if message[0] == YMessageType.SYNC:
            message_type = message[1]
            msg = message[2:]
            if message_type == YSyncMessageType.SYNC_STEP1:
                state = read_message(msg)
                update = encode_state_as_update(ydoc, state)
                reply = create_sync_step2_message(update)
                await self.send_message(type="yjs_update", bytes_data=reply)
            elif message_type in (
                YSyncMessageType.SYNC_STEP2,
                YSyncMessageType.SYNC_UPDATE,
            ):
                update = read_message(msg)
                apply_update(ydoc, update)
                return update

    async def yjs_update(self, event):
        # if event["sender_channel"] == self.channel_name:
        #     return  # Ignore updates sent by the sender

        await self.send(bytes_data=event["bytes"])

    async def default_send(self, event):
        if event["text_data"] is not None:
            await self.send(text_data=event["text_data"])
        elif event["bytes"] is not None:
            await self.send(bytes_data=event["bytes"])
