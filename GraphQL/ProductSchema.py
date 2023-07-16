from collections import Counter

from graphql import GraphQLError

from Cache_Function.Caches import Resolve_Cache_Model_Field
import graphene
import json
from Product_API.models import Product
from statistics import mean
import operator
from functools import reduce
from django.db.models import Min, Count, Q, Avg
from Order_API.models import ProductComment, OrderRecord
from Authentication.Decorator import Check_JWT_Valid_GraphQL
from typing import List, Dict
from django.db.models import F
from django.core.cache import cache
import numpy as np
from django.conf import settings
from .UserSchema import PublicUserType
from Advertising_API.UserSearchType import User_Product_Preference, User_Searching_Preference
from graphql.type.definition import GraphQLResolveInfo
from graphene_django import DjangoObjectType

class CommentType(DjangoObjectType):
    CreateDate = graphene.String()
    User = graphene.Field(PublicUserType)
    id = graphene.Int()
    
    class Meta:
        model = ProductComment

    def resolve_CreateDate(self : Meta.model, info):
        return self.Date.strftime('%Y-%m-%d')

class FullProductType(DjangoObjectType):

    class Meta:
        model = Product
        exclude = ['Seller']

    ### Model
    SubItem = graphene.String()
    Author = graphene.String() 
    AuthorIcon = graphene.String()
    id = graphene.Int()

    ### For Detail
    Images = graphene.String()
    DescriptionImages = graphene.String()
    SimilarProduct = graphene.String()
    Comment = graphene.List(CommentType, Start= graphene.Int(), End= graphene.Int())
    Score = graphene.String()
    DateCreate = graphene.String()
    SellingRecord = graphene.Int()
    DescriptionVideos = graphene.String()
    

    
    ### For Search
    FirstImage = graphene.String()
    MinPrice = graphene.Int()

    def resolve_DescriptionVideos(self:Meta.model, info):
        CacheName = 'Product:{}:DescriptionVideos'.format(self.pk)
        CacheData =  cache.get(CacheName)
        if CacheData:
            return CacheData
        else:
            Data = json.dumps(self.DescriptionVideos)
            cache.set(CacheName, Data, 3600)
            return Data

    def resolve_AuthorIcon(self:Meta.model, info):
        CacheName = 'Product:{}:AuthorIcon'.format(self.pk)
        CacheData = cache.get(CacheName)
        if CacheData:
            return CacheData
        else:
            Data = settings.IMAGE_SERVER_URL + str(self.Seller.ProfileIcon)
            cache.set(CacheName, Data, 3600)
            return Data

    #### I will split the SubItem into keys and values, since if i response Full dict item to frontend, it is very hard to handle !!!!!
    #### For example, I need to handle multi subItem, if i choose 1 then i can easy to change subitem into that, but if i response dict, it is diffcult to handle
    def resolve_SellingRecord(self:Meta.model, info):
        CacheName = "Product:{}:SellingRecord".format(self.id)
        CacheData = cache.get(CacheName)
        if CacheData != None:
            return CacheData
        else:
            Data = self.orderitem_set.count()
            cache.set(CacheName, Data, 3600)
            return Data

    def resolve_DateCreate(self: Meta.model, info):
        return self.date_created.strftime('%Y-%m-%d')


    def resolve_Score(self: Meta.model, info, **kwargs):
        CacheName = 'Product:{}:Score'.format(self.id)
        CacheData = cache.get(CacheName)
        if CacheData != None:
            return CacheData
        else:
            Return_Data = {}
            Score =  self.productcomment_set.values_list('Score', flat=True)
            Return_Data['TotalScore'] = round(mean(Score),1) if len(Score) > 0 else 0
            Distribution = dict(Counter(Score))
            for i in range(5):
                if i +1 not in Distribution:
                    Distribution[i+1] = 0
                else:
                    Distribution[i+1] = round(Distribution[i+1]*100/len(Score), 1)
            Return_Data['Distribution'] = Distribution
            Return_Data['TotalComment'] = len(Score)
            Data = json.dumps(Return_Data)
            cache.set(CacheName, Data, 3600)
            return Data

    def resolve_Comment(self: Meta.model, info, **kwargs):
        try:
            CacheName = 'Product:{}:Comment_set'.format(self.id)
            data = cache.get(CacheName)
            if data != None:
                return Resolve_Cache_Model_Field.Resolve_Model(ProductComment, data[kwargs['Start']: kwargs['End']], select_related=['User'])
            else:
                data = self.productcomment_set.order_by('-pk')
                cachedata = list(data.values_list('pk', flat=True)[:200])
                cache.set(CacheName, cachedata, 3600)
                return data[kwargs['Start']: kwargs['End']]
        except:
            return None

    def resolve_SubItem(self: Meta.model, info):
        CacheName = 'Product:{}:SubItem'.format(self.pk)
        CacheData = cache.get(CacheName)
        if CacheData:
            return CacheData
        else:
            Data = json.dumps(list(self.SubItem.values('Name', 'Price', 'Quantity', 'Properties', 'id', 'Sell')))
            cache.set(CacheName, Data, 3600)
            return Data

    def resolve_Author(self: Meta.model, info):
        CacheName = 'Product:{}:Author'.format(self.pk)
        CacheData = cache.get(CacheName)
        if CacheData:
            return CacheData
        else:
            Data = self.Seller.username
            cache.set(CacheName, Data, 3600)
            return Data

    def resolve_FirstImage(self : Meta.model, info, *args, **kwargs):
        CacheName = 'Product:{}:FirstImage'.format(self.pk)
        CacheData = cache.get(CacheName)
        if CacheData:
            return CacheData
        else:
            data = settings.IMAGE_SERVER_URL + str(self.product_image_set.all()[0])
            cache.set(CacheName, data, 3600)
            return data

    def resolve_SimilarProduct(self: Meta.model , info):
        CacheName = 'Product:{}:SimilarProduct'.format(self.pk)
        CacheData = cache.get(CacheName)
        if CacheData != None:
            SimilarProduct: List[Product] = Resolve_Cache_Model_Field.Resolve_Model(Product, np.random.choice(CacheData, 3))
            Data = [x.BasicInformation() for x in SimilarProduct]
            return json.dumps(Data)
        else:
            Filter = reduce(operator.or_, (Q(ProductName__contains = item) for item in self.ProductName.split(' ')))
            Data = list(Product.objects.filter(Filter).values_list('pk', flat=True)[:200])
            cache.set(CacheName, Data, 3600)
            SimilarProduct: List[Product] = Resolve_Cache_Model_Field.Resolve_Model(Product, np.random.choice(Data, 3))
            Data = [x.BasicInformation() for x in SimilarProduct]
            return json.dumps(Data)

    def resolve_Images(self : Meta.model, info):
        CacheName = 'Product:{}:Images'.format(self.pk)
        CacheData = cache.get(CacheName)
        if CacheData:
            return CacheData
        else:
            data = json.dumps([settings.IMAGE_SERVER_URL + str(x) for x in self.product_image_set.all()])
            cache.set(CacheName, data, 3600)
            return data

    def resolve_DescriptionImages(self : Meta.model, info):
        CacheName = 'Product:{}:DescriptionImages'.format(self.pk)
        CacheData = cache.get(CacheName)
        if CacheData:
            return CacheData
        else:
            data = json.dumps([settings.IMAGE_SERVER_URL + str(x) for x in self.product_description_images_set.all()])
            cache.set(CacheName, data, 3600)
            return data
    
    def resolve_MinPrice(self : Meta.model, info):
        CacheName = 'Product:{}:MinPrice'.format(self.pk)
        CacheData = cache.get(CacheName)
        if CacheData:
            return CacheData
        else:
            Data = self.Get_Lower_Price()
            cache.set(CacheName, Data, 3600)
            return Data
    
class CombineProductAndCount(graphene.ObjectType):
    Product = graphene.List(FullProductType)
    Count = graphene.Int()
    

    def resolve_Product(self, info, **kwargs):
        return self['Product']
    
    def resolve_Count(self, info, **kwargs):
        return self['Count']

class ProductQuery(graphene.ObjectType):
    ProductDetail = graphene.Field(FullProductType, id=graphene.Int(required=True), adsToken = graphene.String(required=False))
    PublicProduct =graphene.Field(CombineProductAndCount, Start=graphene.Int(required=True), End=graphene.Int(required=True), Category=graphene.String(required=False), 
                                                  Search=graphene.String(required=False), User=graphene.String(required=False), StockType= graphene.String(required=False),
                                                  PriceStart=graphene.Float(required=False), PriceEnd=graphene.Float(required=False), QueueMethod = graphene.String(required=False),
                                                  adsToken = graphene.String(required=False))

    PersonalProduct = graphene.Field(CombineProductAndCount, User=graphene.String(required=True), Start=graphene.Int(required=True), End=graphene.Int(required=True), StockType= graphene.String(required=False))

    SuggestionProduct = graphene.List(FullProductType, CategoryType = graphene.String(required=True), Count = graphene.Int(required=True))

    AllSuggestionProduct = graphene.String()

    PersonalSuggestionProduct = graphene.List(FullProductType, Count= graphene.Int(required=True))

    PopularSuggestionProduct = graphene.List(FullProductType, Count= graphene.Int(required=True))

    BuyAgainProduct = graphene.List(FullProductType, Count= graphene.Int(required=True))

    @Check_JWT_Valid_GraphQL
    def resolve_BuyAgainProduct(self, info, **kwargs):
        CacheName = 'Client:{}:BuyAgainProduct:Main'.format(kwargs['user'].id)
        data = cache.get(CacheName)

        if data:
            return Resolve_Cache_Model_Field.Resolve_Model(Product, np.random.choice(data, kwargs.get('Count')))
        else:
            OrderFilter= set(OrderRecord.objects.filter(Buyer = kwargs['user']).values_list('OrderList__ProductID', flat=True).order_by('-id')[:200])
            OrderFilter = list(OrderFilter)
            cache.set(CacheName, OrderFilter, 3600)
            return Product.objects.filter(pk__in = OrderFilter)[:kwargs.get('Count')]

    def resolve_PopularSuggestionProduct(self, info: GraphQLResolveInfo, **kwargs):
        CacheName = 'PopularProduct:Main'
        data = cache.get(CacheName)
        if data:
            return Resolve_Cache_Model_Field.Resolve_Model(Product, np.random.choice(data, kwargs.get('Count')))
        else:
            data = Product.objects.annotate(Sell = Count('orderitem__id')).order_by('-Sell').all()
            cachedata = list(data.values_list('pk', flat=True)[:200])
            cache.set(CacheName, cachedata, 3600)
            return data[:kwargs.get('Count')]

    @Check_JWT_Valid_GraphQL
    def resolve_PersonalSuggestionProduct(self, info, **kwargs):
        CacheName = 'Client:{}:SuggestionProduct:Main'.format(kwargs['user'].id)
        data: List[int] = cache.get(CacheName)
        if data:
            return Resolve_Cache_Model_Field.Resolve_Model(Product, np.random.choice(data, kwargs.get('Count')))
        else:
            """
                Filter : List[str] = list(OrderRecord.objects.filter(Buyer = kwargs['user']).values_list('OrderList__ProductTitle', flat=True).order_by('-id')[:30])
                Filter = itertools.chain.from_iterable(map(lambda x: x.split(' ') if isinstance(x, str) else '', Filter))
                Filter = [Q(ProductName__contains = item) for item in Filter]
                The Above Code is for user who already buy this
            """
            Filter = Q(ProductName__contains = '')
            CacheData: Dict[str, Dict] = cache.get('Ads:{}:Main'.format(kwargs['user'].Ads_Token), {"KeyWords": {}, 'Searching': {}})
            UserPreferenceData: Dict[str, int] = CacheData["KeyWords"]
            UserPreferenceData.update(CacheData["Searching"])

            for x, _ in sorted(UserPreferenceData.items(), key=lambda x: x[1], reverse=True)[:5]:
                Filter = operator.or_(Filter, Q(ProductName__contains = x))
                Filter = operator.or_(Filter, Q(Category__contains = x))
            data = Product.objects.filter(Filter).all()
            cachedata = list(data.values_list('pk', flat=True)[:100])
            cache.set(CacheName, cachedata, 3600)
            return data[:kwargs.get('Count')]

    def resolve_SuggestionProduct(self, info, **kwargs):
        CacheName = 'SuggestionCategoryProduct:{}'.format(kwargs.get('CategoryType'))
        data = cache.get(CacheName)
        if data:
            return Resolve_Cache_Model_Field.Resolve_Model(Product, np.random.choice(data, kwargs.get('Count')))
        else:
            data = Product.objects.filter(Q(is_public = True), Q(Category__contains = kwargs.get('CategoryType')))
            cachedata = list(data.values_list('pk', flat=True)[:200])
            cache.set(CacheName, cachedata, 3600)
            return data[:kwargs.get('Count')]

    def resolve_PersonalProduct(self, info, **kwargs):
        CacheName = 'PersonalProduct:User_{}'.format(kwargs.get('User'))
        CacheName = CacheName + '_StockType_{}'.format(kwargs.get('StockType')) if kwargs.get('StockType', False) else CacheName
        data = cache.get(CacheName)
        if data:      
            Cachedata = Resolve_Cache_Model_Field.Resolve_Model(Product, data[int(kwargs.get('Start')): int(kwargs.get('End'))])
            return {'Product': Cachedata, 'Count': len(data)}
        else:
            FilterList = []
            FilterList.append(Q(Seller__username = kwargs.get('User')))
            FilterList.append(Q(is_public = True))
            FilterList.append(Q(Stock__contains = kwargs.get('StockType', ''))) if kwargs.get('StockType', None) != 'All' else None
            data =  Product.objects.filter(*FilterList)
            cachedata = list(data.values_list('pk', flat=True))
            cache.set(CacheName, cachedata, 1200)
            return {'Product': data[int(kwargs.get('Start')): int(kwargs.get('End'))], 'Count': len(cachedata)}

    def resolve_ProductDetail(self, info, **kwargs):
        User_Product_Preference(model=Product, adsToken=kwargs.get('adsToken'), id=kwargs['id'])
        return Resolve_Cache_Model_Field.Resolve_Model(Product, kwargs.get('id'))


    def resolve_PublicProduct(self, info, **kwargs):
        filter_Properties = []

        ### Filter Categories
        CategoryList: List[str] = kwargs.get("Category", '').split('/')
        filter_Properties.append(reduce(operator.and_, (Q(Category__contains = item) for item in CategoryList)))

        #### Filter search
        NameList: List[str] = kwargs.get('Search', '').split(' ')
        filter_Properties.append(reduce(operator.or_, (Q(ProductName__contains = item) for item in NameList)))
        

        #### User Ads Record (Notice that, some country are limited to collect user informations)
        User_Searching_Preference(SearchItem=CategoryList+NameList, adsToken=kwargs.get('adsToken'))
        
        ### Check item not disable
        filter_Properties.append(Q(is_public = True))
        #### queue Method
        data = Product.objects.filter(*filter_Properties).annotate(MinPrice = Min('SubItem__Price'), AverageScore = Avg('productcomment__Score'), CommentCount = Count('productcomment__pk'))

        PriceFilter = []

        #### Filter Price
        PriceFilter.append(Q(MinPrice__lte = kwargs.get('PriceEnd'))) if kwargs.get('PriceEnd') else None
        PriceFilter.append(Q(MinPrice__gte = kwargs.get('PriceStart'))) if kwargs.get('PriceStart') else None

        if kwargs.get('QueueMethod') == 'PHL':
            data = data.filter(*PriceFilter).order_by('-MinPrice', '-id')
        elif kwargs.get('QueueMethod') == 'PLH':
            data = data.filter(*PriceFilter).order_by('MinPrice', '-id') 
        elif kwargs.get('QueueMethod') == 'SLH':
            data = data.order_by(F('AverageScore').asc(nulls_last=True), F('CommentCount').desc(nulls_last=True)) 
        elif kwargs.get('QueueMethod') == 'SHL':
            data = data.order_by(F('AverageScore').desc(nulls_last=True), F('CommentCount').desc(nulls_last=True))
        else:
            data = data.filter(*PriceFilter).order_by('-id') 


        return {'Product': data[int(kwargs.get('Start')): int(kwargs.get('End'))], 'Count': data.count()}
        
        

