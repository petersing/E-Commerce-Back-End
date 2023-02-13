from rest_framework import exceptions
from rest_framework import serializers
from .models import Client, BusinessSubscribe
import bcrypt
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.conf import settings
from typing import *

class Client_Create_Serializers(serializers.ModelSerializer):    
    def create(self, validated_data):
        validated_data['password'] = self.Bcrypt_Encrypt_Function(validated_data['password'])
        New_Client = Client(**validated_data)
        New_Client.save()
        return New_Client

    @staticmethod
    def Bcrypt_Encrypt_Function(Data: str):   ##### Encrpy Any Data to Bcrypt
        return bcrypt.hashpw(Data.encode(), bcrypt.gensalt(rounds=12)).decode("utf-8")

    class Meta:
        model = Client
        fields = ['username', 'email', "password", 'is_OAuth']


##### For Development , It not contain payment in here. in Real case, please add stripe into here.
class Subscribe_Serializers(serializers.ModelSerializer):
    Subscribe_Month = serializers.IntegerField(required=True)
    User = serializers.PrimaryKeyRelatedField(queryset=Client.objects.all())

    def create(self, validated_data: Dict):
        Client_Data: Client = validated_data['User']
        Prev_Record : BusinessSubscribe = Client_Data.Subscribe
        if (validated_data['Subscribe_Plan'] not in settings.SUBSCRIPTION_PLAN): 
            raise exceptions.MethodNotAllowed('This Plan not exist') 
        else: 
            Plan = settings.SUBSCRIPTION_PLAN[validated_data['Subscribe_Plan']]
        if (Prev_Record):
            if (Prev_Record.Subscribe_Plan == validated_data['Subscribe_Plan']):
                Prev_Record.Subscribe_Date = timezone.now()
                Prev_Record.Subscribe_End = Prev_Record.Subscribe_End + relativedelta(months=validated_data['Subscribe_Month'])
                Prev_Record.save()
            else:
                NowTime = timezone.now()
                Prev_Record.Subscribe_Date = NowTime
                Prev_Record.Subscribe_End = NowTime + relativedelta(months=validated_data['Subscribe_Month'])
                Prev_Record.Subscribe_Plan = validated_data['Subscribe_Plan']
                Prev_Record.save()
            return Prev_Record
        else:
            NowTime = timezone.now()
            Record = BusinessSubscribe(Subscribe_End=NowTime+ relativedelta(months=validated_data['Subscribe_Month']), Subscribe_Date=NowTime, Subscribe_Plan = validated_data['Subscribe_Plan'])
            Record.save()
            Client_Data.Subscribe = Record
            Client_Data.save()
            return Record
    
    class Meta:
        model = BusinessSubscribe
        fields = '__all__'
