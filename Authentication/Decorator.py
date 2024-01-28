import bcrypt
from User_Manager_API.models import Client
from rest_framework import exceptions
import jwt
from rest_framework import authentication
from django.contrib.auth.models import AnonymousUser
from channels.db import database_sync_to_async
from logging import getLogger
from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from graphql.type.definition import GraphQLResolveInfo
from rest_framework.request import Request
from django.db import transaction
import time

logger = getLogger(__file__)

JWT_ENV_Setting = settings.JWT_ENV_SETTING

def CheckAccountValided(fn):
    def Checking(*args, **kwargs):
        try:
            user_data = args[0].POST.dict()
            user = Client.objects.get(email=user_data['email'], is_OAuth=False)
            hashed_pw = user.password
            if not hashed_pw:
                raise exceptions.AuthenticationFailed("Email not exist")
            elif bcrypt.checkpw(user_data['password'].encode(), hashed_pw.encode()):
                with transaction.atomic():
                    user.last_login = timezone.now()
                    user.save()
                    return fn(*args, **kwargs)
            else:
                raise exceptions.AuthenticationFailed("Password is not correct")
        except (exceptions.AuthenticationFailed, Client.DoesNotExist):
            raise exceptions.AuthenticationFailed("Data Not Correct")
        except:
            raise exceptions.MethodNotAllowed('Data not correct')
    return Checking

def CheckGoogleOAuth2Valided(fn):
    def Checking(*args, **kwargs):
        try:
            Auth_Data = args[0].POST.dict()
            idinfo = id_token.verify_oauth2_token(Auth_Data['credential'], requests.Request(), settings.GOOGLE_CLIENT_ID)
            args[0].userdata = idinfo
            return (fn(*args, **kwargs))
        except exceptions.NotAcceptable:
            raise exceptions.NotAcceptable('username have already used')
        except:
            raise exceptions.MethodNotAllowed('Valide Failure')
    return Checking

def Check_JWT_Valid_GraphQL(function):
    def Checking(self, info: GraphQLResolveInfo, **kwargs):
        try:
            Token = info.context.META.get('HTTP_AUTHORIZATION').split(' ')
            if Token[0] != "Bearer":
                return None
            
            decode_result = jwt.decode(Token[1], JWT_ENV_Setting['secret_key'], issuer=JWT_ENV_Setting["issuer"], algorithms=JWT_ENV_Setting['algorithm'], options={"verify_exp": True})
            user = cache.get_or_set('Client:{}:Main'.format(decode_result['user_id']), Client.objects.filter(id=decode_result['user_id']).select_related().first())
            if decode_result and user:
                kwargs['user'] = user
                return function(self, info, **kwargs)
        except Exception as e:
            e.args += (401,)
            return e
    return Checking   

class JWT_Authentication(authentication.BaseAuthentication):
    def authenticate(self, request: Request):
        try:
            Token = request.META.get('HTTP_AUTHORIZATION').split(' ')
            if Token[0] != "Bearer":
                raise exceptions.ValidationError("Token Header Not Correct")

            decode_result = jwt.decode(Token[1], JWT_ENV_Setting["secret_key"], issuer=JWT_ENV_Setting["issuer"], algorithms=JWT_ENV_Setting["algorithm"], options={"verify_exp": True})
            user: Client = cache.get_or_set('Client:{}:Main'.format(decode_result['user_id']), Client.objects.filter(id=decode_result['user_id']).first(), 3600)
            if Token[0] == 'Bearer' and decode_result['jti'] == str(user.Previous_Access_ID):
                return (user, None)
            else:
                raise exceptions.NotFound("Token Not Match, Please Login Again")

        except jwt.ExpiredSignatureError:
            raise exceptions.ValidationError("The Token is expired, please refresh or regenerate")
        except:
            raise exceptions.ValidationError("Validate failure")

class Edit_JWT_Authentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        try:
            Token = request.META.get('HTTP_AUTHORIZATION').split(' ')
            decode_result = jwt.decode(Token[1], JWT_ENV_Setting["secret_key"], issuer=JWT_ENV_Setting["issuer"], algorithms=JWT_ENV_Setting["algorithm"], options={"verify_exp": True})
            user = Client.objects.filter(id=decode_result['user_id']).last()
            if user and Token[0] == 'Bearer' and decode_result['token_type'] == 'edit_access':
                return (user, None)
            else:
                raise exceptions.NotFound("User NotFound")
        except jwt.ExpiredSignatureError:
            raise exceptions.ValidationError("The Token is expired, please refresh or regenerate")
        except:
            raise exceptions.ValidationError("Validate failure")

@database_sync_to_async
def get_user(self_id =None):
    try:
        Data = cache.get('Client:{}:Main'.format(self_id))
        if not Data:
            Data = Client.objects.filter(id = self_id).last()
            if Data: cache.set('Client:{}:Main'.format(self_id))
            else: raise
        return Data               
    except:
        return AnonymousUser()

class JWTAuthMiddleware:

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        try:
            
            StringData = dict((x.split('=') for x in scope['query_string'].decode().split("&")))
            token = StringData.get('Authorization', '')
            decode_result = jwt.decode(token, JWT_ENV_Setting['secret_key'], issuer=JWT_ENV_Setting["issuer"], algorithms=JWT_ENV_Setting['algorithm'], options={"verify_exp": True})
            scope['user'] = get_user(self_id = decode_result['user_id'])
            scope['jti_code'] = decode_result['jti']
            return await self.app(scope, receive, send)
        except:
            scope['user'] = AnonymousUser()
            return await self.app(scope, receive, send)


class RouteNotFoundMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        try:
            return await self.app(scope, receive, send)
        except ValueError as e:
            if (
                "No route found for path" in str(e)
                and scope["type"] == "websocket"
            ):
                await send({"type": "websocket.close"})
                logger.warning(e)
            else:
                raise e