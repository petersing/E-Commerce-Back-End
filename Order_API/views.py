from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from Authentication.Decorator import JWT_Authentication
from rest_framework.permissions import IsAuthenticated
import json
from .Serializers import Make_Order_Serializers
from rest_framework import exceptions
from django.core import cache

### since the order need to redirect to other page, in order to prevent the bug case, it will use REST API to do so!!
@api_view(["POST"])
@authentication_classes([JWT_Authentication])
@permission_classes([IsAuthenticated])
def Create_Order(request):
    data = request.POST.dict()
    AllOrder = Make_Order_Serializers(data={'ClientInformation': json.loads(data['ClientInformation']), 'OrderData': json.loads(data['OrderDetail']), 'ClientID': request.user.id})
    if AllOrder.is_valid():
        result = AllOrder.save() 
        return JsonResponse(result,status=200, safe=False)
    else:
        raise exceptions.NotAcceptable("Please Input All Data")