from django.urls import path,re_path
from .views import *

urlpatterns = [
    re_path(r'File', Handle_Send_File),
    re_path(r'DeleteMessage', Delete_Message)
]