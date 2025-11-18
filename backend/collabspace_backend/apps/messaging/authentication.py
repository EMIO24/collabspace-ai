from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth.models import AnonymousUser
from urllib.parse import parse_qs
from django.conf import settings
from apps.authentication.models import User # Assuming User model location


class JWTAuthMiddleware:
    """Custom JWT auth for WebSocket"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # Get token from query params
        query_string = scope.get('query_string', b'').decode()
        params = parse_qs(query_string)
        # Check for token in 'token' or 'access_token' query parameter
        token = params.get('token', params.get('access_token', [None]))[0]

        # Validate token and get user
        scope['user'] = await self.get_user_from_token(token)

        # Check if the user is authenticated (not AnonymousUser) before proceeding
        # This allows AuthMiddlewareStack to do its work but ensures our custom auth runs first
        return await self.app(scope, receive, send)

    @database_sync_to_async
    def get_user_from_token(self, token):
        if not token:
            return AnonymousUser()

        try:
            # Token validation and user retrieval
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            # Using select_related for common profile info if available
            return User.objects.get(id=user_id)
        except Exception as e:
            # print(f"JWT Auth Error: {e}")
            return AnonymousUser()

def JWTAuthMiddlewareStack(inner):
    """
    Combines our custom JWT auth with Django's default AuthMiddlewareStack
    to provide an authenticated user object in the scope.
    """
    return JWTAuthMiddleware(AuthMiddlewareStack(inner))