"""e_commerce_server URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import re_path, include, path
from django.views.decorators.csrf import csrf_exempt
import User_Manager_API.urls
import Product_API.urls
import Order_API.urls
import Chat_API.urls
import Media_API.urls
from graphene_django.views import GraphQLView

urlpatterns = [
    re_path(r'^api/Account', include(User_Manager_API.urls)),
    re_path(r'^api/Product', include(Product_API.urls)),
    re_path(r'^graphql', csrf_exempt(GraphQLView.as_view())),
    re_path(r'^api/Order', include(Order_API.urls)),
    re_path(r'^api/Message', include(Chat_API.urls)),
    re_path(r"^api/Media", include(Media_API.urls))
]

