from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register('', DocumentViewSet, 'document')
router.register('permission', DocumentPermissionViewSet, 'permission')


urlpatterns = [

] + router.urls