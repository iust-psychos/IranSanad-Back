from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from channels.middleware import BaseMiddleware
from asgiref.sync import sync_to_async
from urllib.parse import parse_qs

User = get_user_model()


class JWTAuthMiddleware(BaseMiddleware):
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode()
        query_params = parse_qs(query_string)
        token = query_params.get("Authorization", [None])[0]

        if not token:
            await self.reject_connection(send, "Missing authorization token")
            return

        try:
            # Token should not have string 'JWT ' in the beginning
            payload = UntypedToken(token)
            user_id = payload["user_id"]
            user = await sync_to_async(User.objects.get)(pk=user_id)
            scope["user"] = user

        except (InvalidToken, TokenError, User.DoesNotExist):
            await self.reject_connection(send, "Invalid authorization token")
            return

        return await super().__call__(scope, receive, send)

    async def reject_connection(self, send, message):
        await send({"type": "websocket.close", "code": 4001, "message": message})
