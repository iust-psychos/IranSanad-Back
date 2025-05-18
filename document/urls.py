from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register("", DocumentViewSet, "document")
router.register("permission", DocumentPermissionViewSet, "permission")
router.register(
    r"document/(?P<doc_uuid>[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})/comment",
    CommentViewSet,
    basename="comment",
)

urlpatterns = [] + router.urls
