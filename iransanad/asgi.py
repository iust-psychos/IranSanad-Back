import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from iransanad.routing import websocket_urlpatterns

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "iransanad.settings")
app = get_asgi_application()
from .middlewares.JWTAuthMiddleware import JWTAuthMiddleware

application = ProtocolTypeRouter(
    {
        "http": app,
        "websocket": AuthMiddlewareStack(
            JWTAuthMiddleware(URLRouter(websocket_urlpatterns))
        ),
    }
)
