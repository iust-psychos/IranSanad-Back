from django.urls import path
from .consumer import HelloWorldConsumer

websocket_urlpatterns = [
    path("ws/helloworld/", HelloWorldConsumer.as_asgi()),
]