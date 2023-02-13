"""
ASGI config for e_commerce_server project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'e_commerce_server.settings')
django.setup()

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from Chat_API.wurls import websocket_urlpatterns
from channels.security.websocket import AllowedHostsOriginValidator
from Authentication.Decorator import JWTAuthMiddleware, RouteNotFoundMiddleware

application = ProtocolTypeRouter({
   "http": get_asgi_application(),
   
   "websocket":  AllowedHostsOriginValidator(   
     RouteNotFoundMiddleware(
          JWTAuthMiddleware(
               URLRouter(
                    websocket_urlpatterns
               )
          )
     )
     ,)
 })



