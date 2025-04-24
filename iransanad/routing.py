from django.urls import path
from .consumer import HelloWorldConsumer
from document.consumer import DocumentConsumer

websocket_urlpatterns = [
    path("ws/helloworld/", HelloWorldConsumer.as_asgi()),
    path('ws/docs/<uuid:doc_uuid>/', DocumentConsumer.as_asgi()),
]