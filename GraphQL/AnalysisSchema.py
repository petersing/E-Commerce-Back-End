
from collections import defaultdict
from datetime import date, datetime, timedelta
import json
import re
import graphene
from django.db.models import CharField
from django.db.models.functions import Cast
import pandas
from Product_API.models import Product
from Authentication.Decorator import Check_JWT_Valid_GraphQL
from Order_API.models import OrderRecord
from django.db.models.functions import TruncDate
from django.db.models import Count, Sum, F
from django.conf import settings
from django.core.cache import cache
from User_Manager_API.models import Client


class ProductAnalysisType(graphene.ObjectType):
    Series = graphene.String(Start = graphene.String(required=False), End = graphene.String(required=False))

    def resolve_Series(self, info, **kwargs):
        Start = datetime.strptime(kwargs['Start'],"%Y-%m-%d")
        End = datetime.strptime(kwargs['End'],"%Y-%m-%d") + timedelta(days=1)
        Now = datetime.now() +timedelta(days=1)
        End = End if Now >= End else Now
        Start = End - timedelta(days=30) if (End - Start) > timedelta(days=30) else Start

        Data = self.orderitem_set.select_related().filter(date_created__gte=Start, date_created__lte=End).values('SubItem__Name', 'ProductTitle', 'SubItem__Count', date = Cast('date_created__date', output_field=CharField()))
        Out = {}
        try:
            Date_All = pandas.date_range(Start,End-timedelta(days=1),freq='d')
            Date_All = Date_All.strftime('%Y-%m-%d').tolist()
            Date_All.append(End.strftime('%Y-%m-%d'))
        except:
            Date_All = []
        
        if Data.count() != 0:
            for i in Data:### O(n) maybe it is a good method or not
                Title = Out.setdefault(i['ProductTitle'], {})
                Title.setdefault(i['SubItem__Name'], {x: 0 for x in Date_All})
                Out[i['ProductTitle']][i['SubItem__Name']][i['date']] += i['SubItem__Count']
        else:
            Out = {self.ProductName: {x.Name: {datetime.now().strftime('%Y-%m-%d'): 0} for x in self.SubItem.all()}}
        return json.dumps(Out)


class OrderAnalysisType(graphene.ObjectType):
    day = graphene.String()
    count = graphene.Int()

    def resolve_day(self, info, **kwargs):
        return self['day']

    def resolve_count(self, info, **kwargs):
        return self['count']
    
class PopularProductType(graphene.ObjectType):
    ProductName = graphene.String()
    Count = graphene.Int()
    FirstImage = graphene.String()
    Stock = graphene.String()

    def resolve_Stock(self, info, **kwargs):
        return self['OrderList__ProductID__Stock']

    def resolve_FirstImage(self, info, **kwargs):
        CacheName = 'Product:{}:FirstImage'.format(self["OrderList__ProductID"])
        CacheData = cache.get(CacheName)
        if CacheData:
            return CacheData
        else:
            Target = Product.objects.get(pk=self["OrderList__ProductID"])
            data = settings.IMAGE_SERVER_URL + str(Target.product_image_set.all()[0])
            cache.set(CacheName, data, 3600)
            return data

    def resolve_ProductName(self, info, **kwargs):
        return self['OrderList__ProductID__ProductName']

    def resolve_Count(self, info, **kwargs):
        return self['Count']
    
class IntegratedAnalysisType(graphene.ObjectType):
    Sell = graphene.Int()
    Return = graphene.Int()
    Profit = graphene.Int()
    Order = graphene.Int()
    Cancel = graphene.Int()

    def resolve_Order(self, info, **kwargs):
        return self['Order']

    def resolve_Sell(self, info, **kwargs):
        return self['Sell']
    
    def resolve_Return(self, info, **kwargs):
        return self['Return']
    
    def resolve_Profit(self, info, **kwargs):
        return self['Profit']
    
    def resolve_Cancel(self, info, **kwargs):
        return self['Cancel']

class AnalysisQuery(graphene.ObjectType):
    AnalysisProduct = graphene.List(ProductAnalysisType, Start=graphene.Int(required=True), End=graphene.Int(required=True))
    ProductCountUser = graphene.Int()
    SellCountByDate= graphene.List(OrderAnalysisType, start_date=graphene.String(required=True), end_date=graphene.String(required=True))
    PopularProduct = graphene.List(PopularProductType)
    IntegratedAnalysis = graphene.Field(IntegratedAnalysisType)

    #### Analysis

    @Check_JWT_Valid_GraphQL
    def resolve_IntegratedAnalysis(self, info, **kwargs):
        User: Client = kwargs['user']
        ORecord = User.orderrecord_Seller
        RRecord = User.returnrecord_Seller
        CRecord = User.orderrecord_Seller
        Cancel = CRecord.filter(Status='cancel').annotate(total_price=Sum(F('OrderList__SubItem__Count') * F('OrderList__SubItem__Price'))).values('total_price')
        Return = RRecord.annotate(total_price=Sum(F('SubItem__Count') * F('SubItem__Price'))).values('total_price')
        Sell = ORecord.annotate(total_price=Sum(F('OrderList__SubItem__Count') * F('OrderList__SubItem__Price'))).values('total_price')
        total_sell_price = Sell.aggregate(total_sell_price=Sum('total_price'))['total_sell_price']
        total_return_price = Return.aggregate(total_return_price=Sum('total_price'))['total_return_price']
        total_cancel_price = Cancel.aggregate(total_cancel_price=Sum('total_price'))['total_cancel_price']
        total_sell_price = 0 if total_sell_price == None else total_sell_price
        total_return_price = 0 if total_return_price == None else total_return_price
        total_cancel_price = 0 if total_cancel_price == None else total_cancel_price
        return {"Cancel": total_cancel_price, "Order": ORecord.count(), 'Sell': total_sell_price + total_return_price, 'Return': total_return_price, 'Profit': total_sell_price - total_return_price - total_cancel_price}

    @Check_JWT_Valid_GraphQL
    def resolve_PopularProduct(self, info, **kwargs):
        return OrderRecord.objects.filter(Seller=kwargs['user']).values("OrderList__ProductID", "OrderList__ProductID__ProductName", "OrderList__ProductID__Stock").annotate(Count=Count('OrderList__ProductID__ProductName')).order_by('-Count')[:5]
    
    @Check_JWT_Valid_GraphQL
    def resolve_SellCountByDate(self, info, start_date, end_date, **kwargs):
        if re.match(r"^\d{4}-\d{2}-\d{2}$", start_date) == None or re.match(r"^\d{4}-\d{2}-\d{2}$", end_date) == None:
            raise Exception('Date format error')
        Order = OrderRecord.objects.filter(Seller=kwargs['user'], date_created__gte=start_date, date_created__lte=end_date)
        sales_by_day = Order.annotate(day=TruncDate('date_created')).values('day').annotate(count=Count('id')).order_by('day')
        Range = [x.strftime('%Y-%m-%d') for x in pandas.date_range(start_date,end_date,freq='d')]
        Res = []
        Reference = {x['day'].strftime('%Y-%m-%d'): x['count'] for x in sales_by_day}
        for i in Range:
            Res.append({'day': i, 'count': Reference.get(i, 0)})
        return Res
    

    @Check_JWT_Valid_GraphQL
    def resolve_AnalysisProduct(self, info, **kwargs):
        return Product.objects.filter(Seller = kwargs['user'])[int(kwargs.get('Start')):int(kwargs.get('End'))].prefetch_related('orderitem_set', 'orderitem_set__SubItem')

    @Check_JWT_Valid_GraphQL
    def resolve_ProductCountUser(self, info, **kwargs):
        return Product.objects.filter(Seller = kwargs['user']).count()