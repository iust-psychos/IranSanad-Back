from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from iransanad.consumer import HelloWorldConsumer

application = ProtocolTypeRouter({
    "websocket": URLRouter([
        path("ws/helloworld/", HelloWorldConsumer.as_asgi()),
    ])
})