from Cache_Function.Caches import Query_Cache_Function, Resolve_Cache_Model_Field
from User_Manager_API.models import Client, Product_Categories, Advertisement, ShoppingAddress,  ShoppingAddress as ShoppingAddressModel, BusinessSubscribe
from Product_API.models import Product
import graphene
from Authentication.Decorator import Check_JWT_Valid_GraphQL
from Order_API.models import PaymentRecord
from django.core.cache import cache
from Chat_API.models import Chat_Channel_Record
import json
from django.db.models import Q, Sum
from django.conf import settings
from typing import Dict, List
from graphene_django import DjangoObjectType

class BusinessSubscribeType(graphene.ObjectType):
    SubscribeEnd = graphene.String()
    SubscribeDate = graphene.String()
    SubscribePlan = graphene.String()

    class Meta:
        model = BusinessSubscribe

    def resolve_SubscribeEnd(self: BusinessSubscribe, info):
        return self.Subscribe_End.strftime('%Y-%m-%d')


    def resolve_SubscribeDate(self: BusinessSubscribe, info):
        return self.Subscribe_Date.strftime('%Y-%m-%d')

    def resolve_SubscribePlan(self: BusinessSubscribe, info):
        return self.Subscribe_Plan

class ShoppingAddressType(DjangoObjectType):
    class Meta:
        model = ShoppingAddressModel
        exclude = ['client_set']
    
    id = graphene.Int()

class UserAds(DjangoObjectType):
    class Meta:
        model = Advertisement
        exclude = ["client_set"]

class FullUserType(DjangoObjectType):
    class Meta:
        model = Client
        exclude = ['Token_is_valided', "paymentrecord_set", "returnrecord_Buyer", "returnrecord_Seller", 'Previous_Access_ID', 'Previous_Refresh_ID', 'password', "product_set", "productcomment_set", "orderrecord_Buyer", "orderrecord_Seller"]

    dateJoined = graphene.String()
    isSubscriber = graphene.Boolean()
    RemainPublish = graphene.Int()
    ShoppingAddress = graphene.List(ShoppingAddressType)
    ProfileIcon = graphene.String()
    Subscribe = graphene.Field(BusinessSubscribeType)
    Preference = graphene.List(graphene.String)

    def resolve_Preference(self: Meta.model, info):
        UserAdsData: Dict[str: int] = cache.get('Ads:{}:Main'.format(self.Ads.id), {"KeyWords": {}, "Searching": {}}) #### if you need to identify the word catelogy, maybe you need to train the ai model.
        return set(UserAdsData['KeyWords'].keys()).union(set(UserAdsData['Searching'].keys()))

    def resolve_ProfileIcon(self: Meta.model, info):
        return settings.IMAGE_SERVER_URL + str(self.ProfileIcon)

    def resolve_ShoppingAddress(self: Meta.model, info):
        CacheName = 'Client:{}:ShoppingAddress'.format(self.id)
        data = cache.get(CacheName)
        if data != None:
            return Resolve_Cache_Model_Field.Resolve_Model(ShoppingAddressModel, data)
        else:
            data = list(self.ShoppingAddress.order_by('-is_default').values_list('pk', flat=True).all())
            cache.set(CacheName, data, 7200)
            data : List[ShoppingAddressModel] = Resolve_Cache_Model_Field.Resolve_Model(ShoppingAddressModel, data)
            return data

    def resolve_RemainPublish(self: Meta.model, info):
        return self.RemainProductPublishCount()

    def resolve_isSubscriber(self: Meta.model, info):
        CacheName = 'Client:{}:isSubscriber'.format(self.id)
        data = cache.get(CacheName)
        if data:
            return data
        else:
            data = self.Is_Subscriber()
            cache.set(CacheName, data, 120)
            return data

    def resolve_dateJoined(self: Meta.model, info):
        return self.date_joined.strftime('%Y-%m-%d')

class PublicUserType(DjangoObjectType):
    class Meta:
        model = Client
        fields = ['ProfileIcon', 'username']

    DateJoin = graphene.String()
    isSubscriber = graphene.Boolean()
    ProfileIcon = graphene.String()

    def resolve_ProfileIcon(self: Meta.model, info):
        return settings.IMAGE_SERVER_URL + str(self.ProfileIcon)

    def resolve_isSubscriber(self: Meta.model, info):
        CacheName = 'Client:{}:isSubscriber'.format(self.id)
        data = cache.get(CacheName)
        if data:
            return data
        else:
            data = self.Is_Subscriber()
            cache.set(CacheName, data, 120)
            return data

    def resolve_DateJoined(self: Meta.model, info):
        return self.date_joined.strftime('%Y-%m-%d')

class SimpleCategoriesProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ["id", "ProductName", "ProductStatus"]

    FirstImage = graphene.String()

    def resolve_FirstImage(self : Meta.model, info, *args, **kwargs):
        CacheName = 'Product:{}:FirstImage'.format(self.pk)
        CacheData = cache.get(CacheName)
        if CacheData:
            return CacheData
        else:
            data = settings.IMAGE_SERVER_URL + str(self.product_image_set.all()[0])
            cache.set(CacheName, data, 3600)
            return data
        
    def resolve_id(self: Meta.model, info):
        return "Item{}".format(self.id)

class CategoriesType(graphene.ObjectType):
    Category = graphene.String()
    Product = graphene.List(SimpleCategoriesProductType)
    TotalSell = graphene.Int()
    Status = graphene.Boolean()
    id = graphene.Int()

    def resolve_id(self, info):
        return int(self.id)

    def resolve_Product(self, info):
        return self.Product.all()

    def resolve_TotalSell(self, info):
        return self.sum

class UserQuery(graphene.ObjectType):
    DataCount = graphene.String()
    PrivateUserData = graphene.Field(FullUserType)
    PublicUserData = graphene.Field(PublicUserType, username=graphene.String(required=True))
    CheckIsUser = graphene.Boolean(username = graphene.String(required=True))
    Categories = graphene.List(CategoriesType)

    @Check_JWT_Valid_GraphQL
    def resolve_Categories(self, info, **kwargs):
        return Product_Categories.objects.filter(User = kwargs['user']).prefetch_related('Product').annotate(sum=Sum('Product__orderitem')).all()

    @Check_JWT_Valid_GraphQL
    def resolve_DataCount(self, info, **kwargs):
        OrderCount = PaymentRecord.objects.filter(Q(Buyer = kwargs['user']), Q(PaymentStatus__in = ['paid', 'unpaid']), Q(Order__is_complete = False)).distinct().count()
        CartCount = 0
        CartID = 'Cart:{}'.format(kwargs.get('user').id)
        CacheData = cache.get_or_set(CartID, {}, None)
        CartCount = sum([len(CacheData[x]) for x in CacheData])

        ChatCount = Chat_Channel_Record.objects.filter(Q(User= kwargs['user']), Q(Record__is_read = False), ~Q(Record__Sender = kwargs['user'])).count()
        return json.dumps({'Order': OrderCount, 'Cart' : CartCount, 'Chat' : ChatCount})


    @Check_JWT_Valid_GraphQL
    def resolve_PrivateUserData(self, info, *args, **kwargs):
        return kwargs['user']

    @Check_JWT_Valid_GraphQL
    def resolve_CheckIsUser(self, info, **kwargs):
        return kwargs.get('user').username == kwargs.get('username')

    def resolve_PublicUserData(self, info, **kwargs):
        CacheName = 'PublicUserData:username_{}'.format(kwargs['username'])
        data = cache.get(CacheName)
        if data:
            return data
        else:
            try:
                data = Client.objects.filter(username=kwargs['username']).only('date_joined', 'ProfileIcon', 'username').last()
                cache.set(CacheName, data, 3600)
                return data
            except:
                return None
            
class UpdateUserAds(graphene.Mutation):
    class Arguments:
        Agreement = graphene.Boolean(required=True)
        ConsentGlobalAds = graphene.Boolean(required=True)
        ConsentThirdPartyAds = graphene.Boolean(required=True)

    status = graphene.Boolean()

    @Check_JWT_Valid_GraphQL
    def mutate(self, info, **kwargs):
        user: Client = kwargs.pop('user')
        Adv: Advertisement = user.Ads
        Adv.Agreement = kwargs['Agreement']
        Adv.ConsentGlobalAds = kwargs['ConsentGlobalAds']
        Adv.ConsentThirdPartyAds = kwargs['ConsentThirdPartyAds']
        Adv.save()
        return UpdateUserAds(status=True)

class CreateOrUpdateAddress(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=False)
        ReceiverName = graphene.String(required=False)
        Address = graphene.String(required=False)
        Phone = graphene.String(required=False)
        City = graphene.String(required=False)
        Country = graphene.String(required=False)
        Delete = graphene.Boolean(required=False)
        Default = graphene.Boolean(required=False)

    status = graphene.Boolean()

    @Check_JWT_Valid_GraphQL
    def mutate(self, info, **kwargs):
        user: Client = kwargs.pop('user')
        if not (kwargs.get('id', False)):
            if (kwargs.pop('Default', False)): 
                user.ShoppingAddress.filter(is_default = True).update(is_default = False)
                NewAddress = ShoppingAddress(**kwargs, is_default = True)
                NewAddress.save()
            else:
                NewAddress = ShoppingAddress(**kwargs, is_default = False)
                NewAddress.save()
            user.ShoppingAddress.add(NewAddress)

        elif (kwargs.pop('Delete', False)):
            user.ShoppingAddress.filter(id = kwargs.get('id', False)).delete()
        elif (kwargs.pop('Default', False)):
            user.ShoppingAddress.filter(is_default=True).update(is_default=False)
            user.ShoppingAddress.filter(id = kwargs.pop('id')).update(is_default=True, **kwargs)
        else:
            user.ShoppingAddress.filter(id = kwargs.get('id', False)).update(is_default=True, **kwargs)
        cache.delete('Client:{}:ShoppingAddress'.format(user.pk))
        return CreateOrUpdateAddress(status = True)
    
class CreateOrUpdateProductCategory(graphene.Mutation):

    class Arguments:
        CategoryName = graphene.String(required=True)
        ProductList = graphene.List(graphene.Int, required=True)
        PreID = graphene.Int(required=False)
    
    status = graphene.Boolean()

    @Check_JWT_Valid_GraphQL
    def mutate(self, info, **kwargs):
        user: Client = kwargs.pop('user')
        if kwargs.get('PreID', False):
            Target = Product_Categories.objects.filter(id = kwargs['PreID'], User=user).first()
            Target.Category = kwargs['CategoryName']
            Target.Product.set(kwargs['ProductList'])
            Target.save()
            CacheName = 'Categories:User_{}_{}'.format(user.id, kwargs['PreID'])
            cache.delete(CacheName)
            cache.delete_many(['Product:{}:Item'.format(x) for x in kwargs['ProductList']])

            PreDisable_Key: set = cache.get(('ChangeProduct'), set())
            if Target.Status == False:
                PreDisable_Key.update(kwargs['ProductList'])
                cache.set('ChangeProduct', PreDisable_Key, None)
            else:
                PreDisable_Key.difference_update(kwargs['ProductList'])
                cache.set('ChangeProduct', PreDisable_Key, None)
            

            Target.Product.update(ProductStatus = Target.Status)

            return CreateOrUpdateProductCategory(status = True)
        else:
            New_Category = Product_Categories(Category = kwargs['CategoryName'], User = user)
            New_Category.save()
            New_Category.Product.set(kwargs['ProductList'])
            return CreateOrUpdateProductCategory(status = True)
        
class ChangeCategoriesProperties(graphene.Mutation):
    class Arguments:
        ID = graphene.Int(required=True)
        Status = graphene.Boolean(required=True)
    
    status = graphene.Boolean()
    
    @Check_JWT_Valid_GraphQL
    def mutate(self, info, **kwargs):
        user: Client = kwargs.pop('user')
        if kwargs.get('ID', False):
            Target = Product_Categories.objects.filter(id=kwargs['ID'], User=user).first()
            if Target:
                # Update the status directly in the database
                Product_Categories.objects.filter(id=kwargs['ID'], User=user).update(Status=kwargs['Status'])
                # Update the product status directly in the database
                Target.Product.update(ProductStatus=kwargs['Status'])
                # Delete cache in one operation
                Delete_CacheKey = []
                Create_ChangeKey = []
                PreDisable_Key: set = cache.get(('ChangeProduct'), set())
                for i in Target.Product.all():
                    Create_ChangeKey.append(i.pk)
                    Delete_CacheKey.append('Product:{}:Item'.format(i.pk))
                if not kwargs['Status']:
                    PreDisable_Key.update(Create_ChangeKey)
                else:
                    PreDisable_Key.difference_update(Create_ChangeKey)
                cache.delete_many(Delete_CacheKey)
                cache.set('ChangeProduct', PreDisable_Key, None)
                return ChangeCategoriesProperties(status=True)
        return ChangeCategoriesProperties(status=False)