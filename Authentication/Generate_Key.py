from django.contrib.auth import get_user_model
import jwt
from rest_framework import exceptions
from typing import Any, Dict
from datetime import datetime, timedelta, timezone
import uuid
from django.conf import settings
from django.core.cache import cache
from User_Manager_API.models import Client

JWT_ENV_Setting = settings.JWT_ENV_SETTING

class Generate_JWT_Key():
    
    def __init__(self, auth_email) -> None:
        self.client = get_user_model().objects.filter(email = auth_email).first()

    @classmethod
    def Refresh_Token(cls, refresh_key):
        try:
            decode_result = jwt.decode(refresh_key, JWT_ENV_Setting["secret_key"], algorithms=JWT_ENV_Setting["algorithm"], options={"verify_exp": True})
            Token_Record : Client = get_user_model().objects.filter(id=decode_result['user_id']).first()
            if (str(Token_Record.Previous_Refresh_ID) == decode_result['jti'] and Token_Record.Token_is_valided == True): #### Validing The refresh key is latest to prevent TSX attack
                access_key, access_jti = cls.Generate_access_key(decode_result['user_id'])                                ##### Regen
                refresh_key, refresh_jti = cls.Generate_refresh_key(decode_result['user_id'], expired_time=decode_result['exp'])
                Token_Record.Previous_Refresh_ID = refresh_jti #### update the Server Record
                Token_Record.Previous_Access_ID= access_jti
                Token_Record.save()
                cache.set('Client:{}:Main'.format(decode_result['user_id']), Token_Record, 3600)
                return {'refresh' : refresh_key, 'access': access_key}
            else:
                Token_Record.Token_is_valided= False
                Token_Record.save()
                raise      
        except jwt.ExpiredSignatureError:
            raise exceptions.ValidationError("The Token is expired")
        except:
            raise exceptions.NotAcceptable('Refresh Error, please Login again')  

    def Generate_Pair_Key(self, remember) -> Dict:
        try:
            access_key, access_jti = self.Generate_access_key(self.client.id)
            refresh_key, refresh_jti = self.Generate_refresh_key(self.client.id, remember)      
            Token_Record: Client = get_user_model().objects.filter(id=self.client.id).last()
            Token_Record.Previous_Refresh_ID = refresh_jti
            Token_Record.Previous_Access_ID =  access_jti
            Token_Record.Token_is_valided=True
            Token_Record.last_login = datetime.now(tz=timezone.utc)
            Token_Record.save()
            cache.set('Client:{}:Main'.format(self.client.id), Token_Record, 3600)
            return {'access': access_key, 'refresh': refresh_key}
        except:
            raise exceptions.NotFound("User Not Found")
    
    @staticmethod
    def Generate_refresh_key(id, remember=None, expired_time=None) -> Any:
        exp = datetime.fromtimestamp(expired_time) if expired_time else datetime.now(tz=timezone.utc) + (JWT_ENV_Setting['REFRESH_TOKEN_LIFETIME'] if not remember else timedelta(days=99999))
        jti = uuid.uuid4()
        data = {'user_id': str(id), 'exp': exp, "token_type": "refresh", 'jti': str(jti)}
        return {'key': jwt.encode(data, JWT_ENV_Setting['secret_key'], algorithm=JWT_ENV_Setting['algorithm']), 'expired': exp}, jti
    
    @staticmethod
    def Generate_access_key(id) -> Any:
        exp = datetime.now(tz=timezone.utc) + JWT_ENV_Setting['ACCESS_TOKEN_LIFETIME']
        jti = uuid.uuid4()
        data = {'user_id': str(id), 'exp': exp, "token_type": "access", 'jti': str(jti), "iss": JWT_ENV_Setting["issuer"]}
        return {'key' : jwt.encode(data, JWT_ENV_Setting['secret_key'], algorithm=JWT_ENV_Setting['algorithm']), 'expired': exp}, jti

    def Generate_edit_access_key(self) -> Any:
        exp = datetime.now(tz=timezone.utc) + JWT_ENV_Setting['EDIT_TOKEN_LIFETIME']
        jti = uuid.uuid4()
        data = {'user_id': str(self.client.id), 'exp': exp, "token_type": "edit_access", 'jti': str(jti), "iss": JWT_ENV_Setting["issuer"]}
        return {'key' : jwt.encode(data, JWT_ENV_Setting['secret_key'], algorithm=JWT_ENV_Setting['algorithm']), 'expired': exp}


        