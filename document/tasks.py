from celery import shared_task


@shared_task
def add(x, y):
    """Add two numbers."""
    return x + y