import logging
from datetime import timedelta
from itertools import groupby
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from celery import shared_task
from y_py import YDoc, apply_update, encode_state_as_update
from .models import DocumentUpdate

logger = logging.getLogger(__name__)

TIME_THRESHOLD = settings.UPDATE_COMPACTING_THRESHOLD

def split_updates_by_time_gap(updates, time_threshold=TIME_THRESHOLD):
    """
    Groups consecutive updates into sessions based on their timestamps.

    Args:
        updates (Iterable): An iterable of update objects, each with a timestamp attribute.
        time_threshold (timedelta, optional): The maximum time difference allowed between consecutive updates in the same session. Defaults to 15 minutes.

    Yields:
        List: Lists of updates that are close together in time, each representing a session.
    """
    session = []
    last_time = None
    for update in updates:
        if not session:
            session.append(update)
        else:
            if (update.created_at - last_time) > time_threshold:
                yield session
                session = [update]
            else:
                session.append(update)
        last_time = update.created_at
    if session and session[-1].created_at < timezone.now() - time_threshold:
        # Only yield the session if the last update is older than the threshold
        yield session
        

def process_session(session):
    """
    Processes a session of updates. This function should contain the logic to handle the updates.

    Args:
        session (List): A list of update objects representing a session.
    """
    ydoc = YDoc()
    authors = set(u.author for u in session if u.author)
    
    for document_update in session:
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
            apply_update(ydoc, update_data)
        except Exception as e:
            logger.error(f"Error applying update: {e}")
            continue
    compacted_data = encode_state_as_update(ydoc)

    with transaction.atomic():
        compacted = DocumentUpdate.objects.create(
            document_id=session[0].document_id,
            update_data=compacted_data,
            is_compacted=True,
            processed=True
        )
        compacted.authors.set(authors)
        compacted.save()
        DocumentUpdate.objects.filter(id__in=[u.id for u in session]).delete()
        


@shared_task
def compact_document_updates():
    updates = (
        DocumentUpdate.objects
        .filter(processed=False, is_compacted=False)
        .order_by('document_id', 'created_at')
    )
    
    for doc_id, doc_updates in groupby(updates, key=lambda u: u.document_id):
        for session in split_updates_by_time_gap(list(doc_updates)):
            process_session(session)
