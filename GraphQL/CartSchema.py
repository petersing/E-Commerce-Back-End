import graphene
from django.core.cache import cache
from Authentication.Decorator import Check_JWT_Valid_GraphQL
from Product_API.models import Product
import json
from Cache_Function.Caches import Resolve_Cache_Model_Field
from typing import List

"""
    ALL Cache Function and record will be saved in Redis cache only
    There Are Two reason why i choose that.
    1. Shopping cart records are frequently accessed items, and redis can provide the fastest access time.
    2. Keeping cart records in Postgresql or Mysql does not provide the most cost-effective processing time.
"""
class ModifyCartFunction(graphene.Mutation):
    class Arguments:
        ProductID = graphene.Int(required=False)
        SubItemKey = graphene.Int(required=False)
        Change = graphene.Int(required=False)
        Clear = graphene.Boolean(required=False)
        Response = graphene.Boolean(required=False)
        ToOther = graphene.Int(required= False)

    ResponseCart = graphene.String()

    @Check_JWT_Valid_GraphQL
    def mutate(self, info, **kwargs):
        CartID = 'Cart:{}'.format(kwargs.get('user').id)
        CacheData = cache.get(CartID, {})
        if (kwargs.get('Clear', None)):
            cache.set(CartID, {}, None)
        elif(kwargs.get('ProductID', None) and kwargs.get("SubItemKey", None) and kwargs.get("Change", None)):
            PreviousRecord = CacheData.get(kwargs['ProductID'], {})
            count = PreviousRecord.get(kwargs['SubItemKey'], 0) + kwargs["Change"]

            ### Check count is positive value
            if count > 0 :
                PreviousRecord[kwargs["SubItemKey"]] = count       
            else: 
                PreviousRecord.pop(kwargs["SubItemKey"], None)
            #### Check Product Exist subItem
            if len(PreviousRecord):
                CacheData[kwargs["ProductID"]] = PreviousRecord         
            else:
                CacheData.pop(kwargs['ProductID'], None)

            cache.set(CartID, CacheData, None)
        elif (kwargs.get('ToOther', None) and kwargs.get("ProductID", None) and kwargs.get("SubItemKey", None)):
            PreviousRecord = CacheData.get(kwargs['ProductID'], {})
            PreviousRecord[kwargs["ToOther"]] = PreviousRecord.get(kwargs['SubItemKey'], 0) 
            PreviousRecord.pop(kwargs['SubItemKey'], None)
            cache.set(CartID, CacheData, None)

        if (kwargs.get("Response", None)):
            Out = []
            CacheData = cache.get(CartID, {})
            CacheKeys = list(CacheData.keys())
            ProductList = Resolve_Cache_Model_Field.Resolve_Model(Field=Product, Item_IDs=CacheKeys)
            for n, i in enumerate(CacheKeys):
                Out.append(ProductList[n].Get_Cart_Response(CacheData[i]))
            return ModifyCartFunction(ResponseCart = json.dumps(Out))
        else:
            return None

class CartQuery(graphene.ObjectType):
    CartDetail = graphene.String()

    @Check_JWT_Valid_GraphQL
    def resolve_CartDetail(self, info, **kwargs):
        CartID = 'Cart:{}'.format(kwargs.get('user').id)
        Out = []
        CacheData = cache.get(CartID)
        CacheKeys = list(CacheData.keys())
        ProductList: List[Product] = Resolve_Cache_Model_Field.Resolve_Model(Field=Product, Item_IDs=CacheKeys)
        for n, i in enumerate(CacheKeys):
            Out.append(ProductList[n].Get_Cart_Response(CacheData[i]))
        return json.dumps(Out)