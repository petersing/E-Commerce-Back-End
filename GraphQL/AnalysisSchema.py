
from datetime import date, datetime, timedelta
import json
import graphene
from django.db.models import CharField
from django.db.models.functions import Cast
import pandas
from Product_API.models import Product
from Authentication.Decorator import Check_JWT_Valid_GraphQL

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

class AnalysisQuery(graphene.ObjectType):
    AnalysisProduct = graphene.List(ProductAnalysisType, Start=graphene.Int(required=True), End=graphene.Int(required=True))
    ProductCountUser = graphene.Int()


    #### Analysis
    @Check_JWT_Valid_GraphQL
    def resolve_AnalysisProduct(self, info, **kwargs):
        return Product.objects.filter(Seller = kwargs['user'])[int(kwargs.get('Start')):int(kwargs.get('End'))].prefetch_related('orderitem_set', 'orderitem_set__SubItem')

    @Check_JWT_Valid_GraphQL
    def resolve_ProductCountUser(self, info, **kwargs):
        return Product.objects.filter(Seller = kwargs['user']).count()