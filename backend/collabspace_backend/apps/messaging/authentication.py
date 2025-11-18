from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from rest_framework_simplejwt.tokens import AccessToken
from urllib.parse import parse_qs
from django.conf import settings

# Load the custom User model
try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
except Exception:
    # Fallback to a reference if get_user_model fails
    User = settings.AUTH_USER_MODEL 


class JWTAuthMiddleware:
    """
    Custom middleware to authenticate users using a JWT token passed
    in the WebSocket connection's query parameters.
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        # Close old database connections to prevent going stale
        close_old_connections()
        
        # 1. Extract token from query params
        try:
            query_string = scope['query_string'].decode()
            params = parse_qs(query_string)
            token = params.get('token', [None])[0]
        except Exception:
            token = None
        
        # 2. Validate token and set user on the scope
        scope['user'] = await self.get_user_from_token(token)
        
        # 3. Delegate to the next layer
        return await self.app(scope, receive, send)
    
    @database_sync_to_async
    def get_user_from_token(self, token):
        """
        Attempts to authenticate the user based on the provided JWT.
        """
        if not token:
            return AnonymousUser()
            
        try:
            # 1. Decode and validate the token
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            
            # 2. Fetch the user from the database
            return User.objects.get(id=user_id)
            
        except Exception as e:
            # Token invalid, expired, or user not found
            print(f"JWT Authentication failed: {e}")
            return AnonymousUser()