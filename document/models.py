from django.db import models
import uuid
from .utility import link_generator
from django.utils import timezone


class Document(models.Model):
    ACCESS_LEVELS = {
        4: "Owner",
        3: "Admin",
        2: "Writer",
        1: "Read_Only",
        0: "Deny",
    }
    title = models.CharField(max_length=255, default="سند بدون عنوان")
    link = models.CharField(max_length=15, unique=True, blank=True)
    owner = models.ForeignKey(
        "authentication.User", on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    doc_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    is_public = models.BooleanField(default=False)
    public_premission_access = models.BooleanField(default=True)   #can Writers or ReadOnly change permissions
    default_access_level = models.PositiveSmallIntegerField(
        choices=ACCESS_LEVELS, default=2
    )

    def __str__(self):
        return self.title

    def get_last_seen_by_user(self, user):
        try:
            return DocumentView.objects.filter(document=self, user=user).latest(
                "viewed_at"
            )
        except DocumentView.DoesNotExist:
            return None

class DocumentView(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    user = models.ForeignKey("authentication.User", on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} viewed {self.document.title} on {self.viewed_at}"


class DocumentUpdate(models.Model):
    title = models.CharField(max_length=255, null=True, blank=True)
    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name="updates"
    )
    # for raw updates
    author = models.ForeignKey(
        "authentication.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="document_updates",
    )
    # for processed updates
    authors = models.ManyToManyField(
        "authentication.User",
        blank=True,
        related_name="compacted_document_updates",
    )
    processed = models.BooleanField(default=False)
    is_compacted = models.BooleanField(default=False)
    
    
    update_data = models.BinaryField()  # Stores the Yjs update as binary data
    created_at = models.DateTimeField(
        auto_now_add=True
    )  # Timestamp for when the update was created

    def __str__(self):
        if self.title:
            return self.title
        else:
            return f"Unknown - {self.created_at}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_compacted and not self.title:
            self.title = f"{self.created_at.strftime('%d %B %Y, %H:%M')}"


class AccessLevel(models.Model):
    ACCESS_LEVELS = {
        4: "Owner",
        3: "Admin",
        2: "Writer",
        1: "ReadOnly",
        0: "Deny",
    }
    PERMISSION_MAP = {
        "Owner": 4,
        "Admin": 3,
        "Writer": 2,
        "ReadOnly": 1,
        "Deny": 0,
    }

    user = models.ForeignKey("authentication.User", on_delete=models.CASCADE)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    access_level = models.PositiveSmallIntegerField(choices=ACCESS_LEVELS, default=2)

    class Meta:
        unique_together = ("user", "document")

    def __str__(self):
        return f"{self.user} has {self.ACCESS_LEVELS[self.access_level]} access to {self.document}"


class Comment(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    author = models.ForeignKey(
        "authentication.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="comments",
    )
    text = models.TextField()
    range_start = models.JSONField(null=True, blank=True)
    range_end = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="resolved_comments",
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["document", "created_at"]),
            models.Index(fields=["is_resolved"]),
        ]

    def __str__(self):
        return f"{self.author} commented on {self.document.title} at {self.created_at}"


class CommentReply(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    author = models.ForeignKey(
        "authentication.User", on_delete=models.SET_NULL, null=True
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Reply by {self.author} at {self.created_at}"
