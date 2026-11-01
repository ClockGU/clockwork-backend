from api.security import auth_clerk_from_token
from api.websockets.managers.base_manager import WebsocketConnectionManager

ClerkConnectionManager = WebsocketConnectionManager(auth_clerk_from_token)


def get_clerk_connection_manager():
    return ClerkConnectionManager
