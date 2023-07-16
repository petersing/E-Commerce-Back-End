import bcrypt
from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework import exceptions
from .Serializers import Client_Create_Serializers, Subscribe_Serializers
from Authentication.Generate_Key import Generate_JWT_Key
from Authentication.Decorator import CheckAccountValided, CheckGoogleOAuth2Valided
from rest_framework.permissions import IsAuthenticated
from Authentication.Decorator import Edit_JWT_Authentication, JWT_Authentication
from .models import Client
from django.core.cache import cache
from datetime import datetime, timedelta, timezone
from django.conf import settings


class GoogleAccount():
    @api_view(["POST"])
    @CheckGoogleOAuth2Valided
    def OAuthFunction(request):
        RequestData = request.POST.dict()
        User = Client.objects.filter(email = request.userdata['email'])
        if (User.exists()):
            Key_API = Generate_JWT_Key(request.userdata['email'])
            return JsonResponse({**Key_API.Generate_Pair_Key(RequestData.get('remember')), 'Status': True}, status=200)
        else:
            return JsonResponse({'Status': False, "Platform": 'Google', "Email": request.userdata['email']}, status=200)

    @api_view(["POST"])
    @CheckGoogleOAuth2Valided
    def Registry(request):
        RequestData = request.POST.dict()
        New_Client = Client_Create_Serializers(data={'email': request.userdata['email'], 'username': RequestData['username'], 'is_OAuth': True, 'password': RequestData['password']})
        if (New_Client.is_valid()):
            New_Client.save()
            Key_API = Generate_JWT_Key(request.userdata['email'])
            return JsonResponse({**Key_API.Generate_Pair_Key(RequestData.get('remember')), 'Status': True}, status=200)
        else:
            raise exceptions.NotAcceptable('username have already used')

class GeneralAccount():
    @api_view(["POST"])
    def Register_Function(request):
        request_data = request.POST.dict()
        New_Client = Client_Create_Serializers(data={**request_data, 'is_OAuth': False})
        if New_Client.is_valid():
            New_Client.save()  
            return HttpResponse(status=200)
        else:
            raise exceptions.NotAcceptable('EmailOrUsernameRepeat')

    @api_view(["POST"])
    @CheckAccountValided
    def Login_Function(request):
        request_data = request.POST.dict()
        Key_API = Generate_JWT_Key(request_data.get('email'))
        Key_Pair = Key_API.Generate_Pair_Key(request_data.get('remember'))
        Response = HttpResponse(status=200)
        Response.set_cookie('refresh', Key_Pair['refresh']["key"], expires=Key_Pair['refresh']["expired"], path="/")
        Response.set_cookie('access', Key_Pair['access']["key"], expires=Key_Pair['access']["expired"], path="/")
        return Response

class AccountManager():

    @api_view(["POST"])
    @authentication_classes([JWT_Authentication])
    @permission_classes([IsAuthenticated])
    def Subscribe_Business(request):
        
        if settings.DEBUG != True:
            return

        request_data = request.POST.dict()
        request_data['User'] = request.user.id
        New_Subscribe = Subscribe_Serializers(data=request_data)
        if New_Subscribe.is_valid():
            New_Subscribe.save()  
            cache.delete_pattern('Client:{}:*'.format(request.user.id))
            return HttpResponse(status=201)
        else:
            raise exceptions.NotAcceptable('Email or username have used')

    @api_view(["POST"])
    @authentication_classes([Edit_JWT_Authentication])
    @permission_classes([IsAuthenticated])
    def Reset_Password(request):
        try:
            request_data = request.POST.dict()
            Check = bcrypt.checkpw(request_data['prev_password'].encode(), request.user.password.encode())
            if (Check):
                request.user.password = bcrypt.hashpw(request_data['new_password'].encode(), bcrypt.gensalt(rounds=12)).decode("utf-8")
                request.user.save()
                return HttpResponse(status=200)
            else:
                return HttpResponse(status=400)
        except:
            return HttpResponse(status=400)

    @api_view(["POST"])
    @authentication_classes([JWT_Authentication])
    @permission_classes([IsAuthenticated])
    def Set_ProfileIcon(request):
        try:
            Icon = request.FILES.getlist('Icon')[0]
            request.user.ProfileIcon = Icon
            request.user.save()
            cache.delete_pattern('Client:{}:*'.format(request.user.id))
            cache.delete_pattern('PublicUserData:username_{}'.format(request.user.username))
            return HttpResponse(status=200)
        except:
            return HttpResponse(status=400)
    
class TokenManager():
    @api_view(["POST"])
    def Refresh_Token(request):
        request_data = request.POST.dict()
        Key_Pair = Generate_JWT_Key.Refresh_Token(request_data.get('refresh'))
        Response = HttpResponse(status=200)
        Response.set_cookie('refresh', Key_Pair['refresh']["key"], expires=Key_Pair['refresh']["expired"], path="/")
        Response.set_cookie('access', Key_Pair['access']["key"], expires=Key_Pair['access']["expired"], path="/")
        return Response

        #return JsonResponse(Key_Pair, status=200)

    @api_view(["POST"])
    @CheckAccountValided
    def Edit_Token(request):
        request_data = request.POST.dict()
        Key = Generate_JWT_Key(request_data.get('email')).Generate_edit_access_key()
        Response = HttpResponse(status=200)
        Response.set_cookie('Edit_Access', Key["key"], expires=Key["expired"], path="/AccountSetting")
        return Response

    @api_view(["POST"])
    @authentication_classes([JWT_Authentication])
    @permission_classes([IsAuthenticated])
    def GetAdsToken(request):
        Response = HttpResponse(status=200)
        Response.set_cookie('ads', request.user.Ads_Token, expires=datetime.now(tz=timezone.utc) + timedelta(weeks=999), path="/")
        return Response

