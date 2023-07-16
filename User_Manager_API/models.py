import time
from django.db import models
import uuid
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.conf import settings
import os
from typing import *

def user_directory_path(instance, filename: str):
    year, month, day= map(str, time.strftime("%Y %m %d").split())
    ext = filename.split('.').pop()
    filename = '{0}_{1}.{2}'.format(instance.username, time.time() , ext)
    return os.path.join('E-Commerce-DataBase\ProfileIcon_DataBase', year, month, day, instance.username ,filename)

class ShoppingAddress(models.Model):
    is_default = models.BooleanField()
    Phone = models.CharField(max_length=50)
    Address = models.CharField(max_length=100)
    City = models.CharField(max_length=30)
    Country = models.CharField(max_length=50)
    ReceiverName = models.CharField(max_length=50)

class BusinessSubscribe(models.Model):
    Subscribe_End = models.DateTimeField(null=True)
    Subscribe_Date = models.DateTimeField(null=True)
    Subscribe_Plan = models.CharField(max_length=30)

class Client(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=30, unique=True)
    Previous_Refresh_ID = models.UUIDField(null=True)
    Previous_Access_ID = models.UUIDField(null=True)
    Token_is_valided = models.BooleanField(default=False)
    Subscribe = models.ForeignKey(BusinessSubscribe, on_delete=models.SET_NULL, null=True)
    ProfileIcon = models.ImageField(upload_to= user_directory_path, null=True)
    ShoppingAddress = models.ManyToManyField(ShoppingAddress)
    is_OAuth = models.BooleanField()
    Ads_Token = models.UUIDField(default=uuid.uuid4)
    is_superuser = None
    is_staff = None
    first_name = None
    last_name = None

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "password"]

    def RemainProductPublishCount(self):
        try:
            return settings.SUBSCRIPTION_PLAN[self.Subscribe.Subscribe_Plan]['Product'] - self.product_set.count()
        except:
            return 0

    def Is_Subscriber(self):
        try:
            return self.Subscribe.Subscribe_End > timezone.now()
        except:
            return False


