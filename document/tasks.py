import logging
from datetime import timedelta
from itertools import groupby
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from celery import shared_task
from y_py import YDoc, apply_update, encode_state_as_update, encode_state_vector
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
    logger.info(
        f"Splitting updates into sessions with a time threshold of {time_threshold}."
    )
    session = []
    last_time = None
    for update in updates:
        if not session:
            session.append(update)
        else:
            if (update.created_at - last_time) > time_threshold:
                logger.info(
                    f"* Time gap detected: {update.created_at - last_time} exceeds threshold of {time_threshold}."
                )
                yield session
                session = []
            session.append(update)
        last_time = update.created_at
    if session and session[-1].created_at < timezone.now() - time_threshold:
        logger.info(
            f"~ Last session is old enough: {session[-1].created_at} older than threshold of {time_threshold}. Yielding."
        )
        yield session
    elif session:
        logger.info(
            f"~ Last session is too recent: {session[-1].created_at} within threshold of {time_threshold}. Not yielding.({timezone.now() - time_threshold} < {session[-1].created_at})"
        )
    else:
        logger.info(
            f"~ No updates in the session. Last time: {last_time}, current time: {timezone.now()}"
        )
        

def get_ydoc(document_id):
    """
    Retrieves the YDoc updates and apply them to a new YDoc instance.
    
    Args:
        document_id (int): The ID of the document to retrieve updates for.

    Returns:
        YDoc: A new YDoc instance with the applied updates.
    """
    ydoc = YDoc()
    updates = DocumentUpdate.objects.filter(document_id=document_id, processed=True)
    for update in updates:
        update_bytes = (
            bytes(update.update_data)
            if isinstance(update.update_data, memoryview)
            else update.update_data
        )
        if not isinstance(update_bytes, bytes):
            logger.error(
                f"Invalid update_data type: {type(update_bytes)}, value: {update_bytes}"
            )
            continue
        try:
            apply_update(ydoc, update_bytes)
        except Exception as e: 
            logger.error(f"Error applying update: {e}")
            continue
    return ydoc


def process_session(session):
    """
    Processes a session of updates. This function should contain the logic to handle the updates.

    Args:
        session (List): A list of update objects representing a session.
    """
    if not session:
        return
    logger.info(
        f"! Processing session with {len(session)} updates for document ID: {session[0].document_id}"
    )
    local_doc = get_ydoc(session[0].document_id)
    local_sv = encode_state_vector(local_doc)
    
    remote_doc = get_ydoc(session[0].document_id)
    
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
            apply_update(remote_doc, update_data)
        except Exception as e:
            logger.error(f"Error applying update: {e}")
            continue
    compacted_delta = encode_state_as_update(remote_doc, local_sv)

    with transaction.atomic():
        compacted = DocumentUpdate.objects.create(
            document_id=session[0].document_id,
            update_data=compacted_delta,
            is_compacted=True,
            processed=True,
            # created_at= session[-1].created_at, #TODO: Check if this is needed
        )
        compacted.authors.set(authors)
        compacted.save()
        session_update_ids = [u.id for u in session]
        logger.info(
            f"Compacted {len(session)} updates into session ID: {compacted.id} for document ID: {session[0].document_id}"
        )
        DocumentUpdate.objects.filter(id__in=session_update_ids).update(processed=True)
        DocumentUpdate.objects.filter(id__in=session_update_ids).delete()
        logger.info(
            f"!- Deleted {len(session)} updates after compaction for document ID: {session[0].document_id}"
        )

@shared_task
def compact_document_updates():
    updates = (
        DocumentUpdate.objects
        .filter(processed=False, is_compacted=False)
        .order_by('document_id', 'created_at')
    )
    logger.info(f"[][][] Processing {len(updates)} document updates into sessions.")
    for doc_id, doc_updates in groupby(updates, key=lambda u: u.document_id):
        doc_updates_list = list(doc_updates)
        logger.info(f"Processing document ID: {doc_id} with {len(doc_updates_list)} updates.")
        for session in split_updates_by_time_gap(doc_updates_list):
            process_session(session)