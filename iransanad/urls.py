from django.contrib import admin
from django.urls import path,include
from django.conf.urls.static import static
from django.conf import settings
from .swagger import schema_view

VERSION = settings.VERSION
BASE_URL = settings.BASE_URL


urlpatterns = [
    path(f'{BASE_URL}/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path(f'{BASE_URL}/nbt-admin', admin.site.urls),
    path(f'{BASE_URL}/auth/',include('authentication.urls')),
    path(f'{BASE_URL}/',include('core.urls')),
]\
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)\
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)