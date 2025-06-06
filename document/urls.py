from rest_framework.routers import DefaultRouter
from .views import *

UUID_REGEX = r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}"

router = DefaultRouter()
router.register(
    r"commentreply",
    CommentReplyViewSet,
    basename="comment-reply",
)
router.register("", DocumentViewSet, "document")
router.register("permission", DocumentPermissionViewSet, "permission")
router.register(
    fr"document/(?P<doc_uuid>{UUID_REGEX})/comment",
    CommentViewSet,
    basename="comment",
)
router.register(
    fr"document/(?P<doc_uuid>{UUID_REGEX})/updates",
    DocumentUpdateViewSet,
    basename="document-update",
)

urlpatterns = [] + router.urls
