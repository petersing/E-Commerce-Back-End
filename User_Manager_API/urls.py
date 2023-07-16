from django.urls import path,re_path
from .views import *

urlpatterns = [
    re_path(r'Register', GeneralAccount.Register_Function),
    re_path(r'Login', GeneralAccount.Login_Function),

    re_path(r"Refresh_Token", TokenManager.Refresh_Token),
    re_path(r"Edit_Token", TokenManager.Edit_Token),
    re_path(r"Ads_Token", TokenManager.GetAdsToken),

    re_path(r'Reset_Password', AccountManager.Reset_Password),
    re_path(r'Update_ProfileIcon', AccountManager.Set_ProfileIcon),
    re_path(r'Subscribe', AccountManager.Subscribe_Business),

    re_path(r'GoogleOAuth2', GoogleAccount.OAuthFunction),
    re_path(r'GoogleRegistry', GoogleAccount.Registry),

]