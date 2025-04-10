from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register('', AuthenticationViewSet, 'auth')
router.register("verification",VerificationViewSet,basename="verification")





urlpatterns = [
    
] + router.urls