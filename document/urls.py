from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register("", DocumentViewSet, "document")
router.register("permission", DocumentPermissionViewSet, "permission")
router.register(
    r"document/(?P<doc_id>\d+)/comment",
    CommentViewSet,
    basename="comment",
)

urlpatterns = [] + router.urls
