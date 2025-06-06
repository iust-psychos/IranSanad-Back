from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import *
@receiver(post_save, sender=Document)
def handle_new_model_creation(sender, instance, created, **kwargs):
    if created:
        if not instance.link:
            instance.link = link_generator(
                f"{instance.title}{timezone.now().timestamp()}"
            )
            instance.save()
        
        AccessLevel.objects.create(
            user=instance.owner,
            document=instance,
            access_level=AccessLevel.PERMISSION_MAP["Owner"],
        )