from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register('transcriptions', AudioTranscriptionViewSet, basename='audio-transcriptions')


urlpatterns = [

] + router.urls