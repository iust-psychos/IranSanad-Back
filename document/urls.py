from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register('', DocumentViewSet, 'document')



urlpatterns = [

] + router.urls