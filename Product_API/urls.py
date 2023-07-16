from django.urls import path,re_path
from .views import *

urlpatterns = [
    re_path(r'Create_Product', Create_Product),
    re_path(r'Modify_Product', Modify_Product),
    re_path(r'Delete_Product', Delete_Product),
]