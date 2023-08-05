from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view, authentication_classes, permission_classes
import itertools
from rest_framework import exceptions
from .Serializers import Product_Serializers
from e_commerce_server.Public_Function import Convert_Internal_Image_To_Django_Style_File
from rest_framework.permissions import IsAuthenticated
import json
from Authentication.Decorator import JWT_Authentication
from .models import Product
from django.core.cache import cache
from django.conf import settings


#### This API is mainly handled the Product Function
@api_view(["POST"])
@authentication_classes([JWT_Authentication])
@permission_classes([IsAuthenticated])
def Create_Product(request):

    #### Check User are verifyed
    if request.user.Is_Subscriber() == False :
        raise exceptions.AuthenticationFailed("This Account Have not Subscripted, can not Post product", code=401)
    if request.user.RemainProductPublishCount() <= 0:
        raise exceptions.MethodNotAllowed("This account has exceeded the product publish limit, please update your plan!", code=403)

    data = request.POST.dict()
    
    if len(set(data.keys()).intersection(("Description", 'SubItem', 'ProductName', 'ShippingLocation', 'Category'))) != 5:
        raise exceptions.NotAcceptable("Please Input all data information")
    
    data['Images']= list(itertools.chain.from_iterable([request.FILES.getlist(x) for x in request.FILES if 'DescriptionImages' not in x])) ### Since Javascript limit the type of save, in order to save ALL image, we need to use this method
    data['DescriptionImages']= list(itertools.chain.from_iterable([request.FILES.getlist(x) for x in request.FILES if 'DescriptionImages' in x])) ### Since Javascript limit the type of save, in order to save ALL image, we need to use this method
    data['Images'] = [Convert_Internal_Image_To_Django_Style_File(file_path='Default_Item/Image_not_available.png')] if len(data['Images']) == 0 else data['Images']

    data['Seller'] = request.user.id
    data["Description"] = data["Description"].split('\r\n')
    data['SubItemList'] = json.loads(data.pop("SubItem", {}))
    data['DescriptionVideos'] = json.loads(data['DescriptionVideos'])
    data = Product_Serializers(data=data)

    if data.is_valid():
        Result: Product = data.save()
        Response_Dict = {'Product_Name': Result.ProductName, "FirstImage":  settings.IMAGE_SERVER_URL + str(Result.product_image_set.first())}
        return JsonResponse(Response_Dict, status=200, safe=False)
    else:
        return HttpResponse(status=400, content=data.errors)

@api_view(["POST"])
@authentication_classes([JWT_Authentication])
@permission_classes([IsAuthenticated])
def Modify_Product(request):
    data = request.POST.dict()

    Indicate_Product = Product.objects.select_related().get(id = data.get('id', None))
    data['Images']= list(itertools.chain.from_iterable([request.FILES.getlist(x) for x in request.FILES if 'DescriptionImages' not in x]))
    data['DescriptionImages']= list(itertools.chain.from_iterable([request.FILES.getlist(x) for x in request.FILES if 'DescriptionImages' in x]))
    data["Description"] = data["Description"].split('\r\n')
    data['SubItemList'] = json.loads(data.pop("SubItem", []))
    data['RemoveImages'] = json.loads(data['RemoveImages']) if data.get('RemoveImages', None) else []
    data['RemoveDescriptionImages'] = json.loads(data['RemoveDescriptionImages']) if data.get('RemoveDescriptionImages', None) else []
    data['RemoveSubItem'] = json.loads(data['RemoveSubItem']) if data.get('RemoveSubItem', None) else []

    ProductSerializer = Product_Serializers(Indicate_Product, data)
    if (ProductSerializer.is_valid()):
        ProductSerializer.save()
        cache.delete_pattern('Product:{}:*'.format(data.get('id', None)))
    else:
        exceptions.APIException(ProductSerializer.errors, code=403)
    return HttpResponse(status=200)

@api_view(["POST"])
@authentication_classes([JWT_Authentication])
@permission_classes([IsAuthenticated])
def Delete_Product(request):
    data = request.POST.dict()
    try:
        Indicate_Product = Product.objects.get(id = data.get('id', None))
        Indicate_Product.delete()
        return HttpResponse(status=201)
    except:
        return HttpResponse(status=400)

