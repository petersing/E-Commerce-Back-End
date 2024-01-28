from Product_API.models import Product
from Cache_Function.Caches import Resolve_Cache_Model_Field
from Cache_Function.Caches import Query_Cache_Function
import graphene
import json
from Order_API.models import OrderRecord, OrderItem, OrderSubItem
from Authentication.Decorator import Check_JWT_Valid_GraphQL
from django.db.models import Q
from Order_API.models import ReturnRecord, PaymentRecord, ProductComment
from django.db.models import Prefetch
from .ProductSchema import FullProductType
from django.core.cache import cache
from django.conf import settings
from User_Manager_API.models import Client
from graphene_django import DjangoObjectType
from django.db.models import Count

#### Query
class SubOrderType(DjangoObjectType):
    class Meta:
        model = OrderSubItem
        exclude = ['returnrecord_set']

    Comment = graphene.Boolean()
    id = graphene.Int()

    def resolve_Comment(self: Meta.model, info):
        CacheName = 'OrderSubItem:{}:Comment'.format(self.pk)
        CacheData = cache.get(CacheName)
        if CacheData != None:
            return CacheData
        else:
            Data = bool(self.Comment)
            cache.set(CacheName, Data, 120)
            return Data

class OrderItemsType(DjangoObjectType):
    class Meta:
        model = OrderItem
        exclude = ['returnrecord_set']

    DateCreate= graphene.String()
    Product = graphene.Field(FullProductType)
    ProductKey = graphene.Int()
    id = graphene.Int()

    def resolve_OrderImage(self: Meta.model, info):
        CacheName = 'OrderItem:{}:OrderImage'.format(self.pk)
        CacheData = cache.get(CacheName)
        if CacheData != None:
            return CacheData
        else:
            Data = settings.IMAGE_SERVER_URL + str(self.OrderImage)
            cache.set(CacheName, Data, 120)
            return Data

    def resolve_ProductKey(self: Meta.model, info):
        CacheName = 'OrderItem:{}:ProductKey'.format(self.pk)
        CacheData = cache.get(CacheName)
        if CacheData != None:
            return CacheData
        else:
            Data = self.ProductID.pk
            cache.set(CacheName, Data, 3600)
            return Data

    def resolve_Product(self: Meta.model, info):
        CacheName = 'OrderItem:{}:ProductKey'.format(self.pk)
        CacheData = cache.get(CacheName)
        if CacheData != None:
            return Resolve_Cache_Model_Field.Resolve_Model(Product, CacheData)
        else:
            Data = self.ProductID.pk
            cache.set(CacheName, Data, 3600)
            return Resolve_Cache_Model_Field.Resolve_Model(Product, Data)

    def resolve_DateCreate(self: Meta.model, info):
        CacheName = 'OrderItem:{}:DateCreate'.format(self.pk)
        CacheData = cache.get(CacheName)
        if CacheData != None:
            return CacheData
        else:
            Data = self.date_created.strftime('%Y-%m-%d %H:%M:%S')
            cache.set(CacheName, Data, 3600)
            return Data

class OrderType(DjangoObjectType):
    class Meta:
        model = OrderRecord
        exclude = ['Buyer', 'Seller', 'paymentrecord_set']

    id = graphene.Int()
    SellerName = graphene.String()
    SellerID = graphene.String()
    OrderProcess = graphene.Int()
    DateCreate= graphene.String()
    BuyerName = graphene.String()
    PaymentStatus = graphene.String()

    def resolve_PaymentStatus(self: Meta.model, info):
        CacheName = 'OrderRecord:{}:PaymentRecord'.format(self.pk)
        CacheData = cache.get(CacheName)
        if CacheData != None:
            Data :PaymentRecord = Resolve_Cache_Model_Field.Resolve_Model(PaymentRecord, CacheData)
            return Data.CheckStripeServerStatus()
        else:
            try:
                Data :PaymentRecord = self.paymentrecord_set.all()[0]
                cache.set(CacheName, Data.id, 120)
                return Data.CheckStripeServerStatus()
            except:
                return 'Error'

    def resolve_BuyerName(self : Meta.model, info):
        CacheName = 'OrderRecord:{}:Buyer'.format(self.pk)
        CacheData = cache.get(CacheName)
        if CacheData != None:
            Data : Client =  cache.get('Client:{}:Main'.format(CacheData))
            if Data:
                return Data.username
            else:
                Data = cache.get_or_set('Client:{}:Main'.format(CacheData), self.Seller, 3600)
                return Data.username
        else:
            Data = self.Seller
            cache.set(CacheName, Data.pk, 120)
            cache.get_or_set('Client:{}:Main'.format(Data.pk), Data, 3600)
            return Data.username

    def resolve_DateCreate(self : Meta.model, info):
        CacheName = 'OrderRecord:{}:DateCreate'.format(self.pk)
        CacheData = cache.get(CacheName)
        if CacheData != None:
            return CacheData
        else:
            Data = self.date_created.strftime('%Y-%m-%d %H:%M:%S')
            cache.set(CacheName, Data, 120)
            return Data
 
    def resolve_SellerName(self: Meta.model , info):
        CacheName = 'OrderRecord:{}:Seller'.format(self.pk)
        CacheData = cache.get(CacheName)
        if CacheData != None:
            Data : Client =  cache.get('Client:{}:Main'.format(CacheData))
            if Data:
                return Data.username
            else:
                Data = cache.get_or_set('Client:{}:Main'.format(CacheData), self.Seller, 3600)
                return Data.username
        else:
            Data = self.Seller
            cache.set(CacheName, Data.pk, 120)
            cache.get_or_set('Client:{}:Main'.format(Data.pk), Data, 3600)
            return Data.username

    def resolve_SellerID(self : Meta.model, info):
        CacheName = 'OrderRecord:{}:Seller'.format(self.pk)
        CacheData = cache.get(CacheName)
        if CacheData != None:
            return CacheData
        else:
            Data = self.Seller.pk
            cache.set(CacheName, Data, 120)
            return Data

    def resolve_OrderProcess(self : Meta.model, info):
        try:
            CacheName = 'OrderRecord:{}:PaymentRecord'.format(self.pk)
            CacheData = cache.get(CacheName)
            if CacheData:
                PaymentStatus :PaymentRecord = Resolve_Cache_Model_Field.Resolve_Model(PaymentRecord, CacheData)
            else:
                PaymentStatus :PaymentRecord = self.paymentrecord_set.all()[0]
                cache.set(CacheName, PaymentStatus.pk, 120)
            PaymentStatus = 'unpaid' if not PaymentStatus else PaymentStatus.CheckStripeServerStatus()
        except:
            PaymentStatus = 'Error'

        if self.is_complete:
            return 4
        elif self.TransportCode != None:
            return 3
        elif PaymentStatus == 'paid':
            return 2
        else: 
            return 1

class PaymentRecordType(DjangoObjectType):
    class Meta:
        model = PaymentRecord
        exclude = ['Stripe_ID', 'payment_intent', 'Buyer']

    PaymentStatus = graphene.String()
    PaymentID = graphene.Int()
    id = graphene.Int()

    
    def resolve_PaymentStatus(self: Meta.model, info):
        try:
            return self.CheckStripeServerStatus()
        except:
            return 'Error'
        
    def resolve_PaymentID(self, info):
        CacheName = 'PaymentRecord:{}:PaymentID'.format(self.pk)
        CacheData = cache.get(CacheName)
        if CacheData != None:
            return CacheData
        else:
            Data = self.id
            cache.set(CacheName, Data, 120)
            return Data

class ReturnProductType(DjangoObjectType):
    class Meta:
        model = ReturnRecord
        exclude = ['Seller', 'Buyer']

    SellerName = graphene.String()
    BuyerName = graphene.String()
    ReturnStatusState = graphene.String()
    id = graphene.Int()

    def resolve_ReturnStatusState(self: Meta.model, info):
        CacheName = 'ReturnRecord:{}:OrderRecordTransportCode'.format(self.pk)
        TransportCode = cache.get_or_set(CacheName, self.Order.orderrecord_set.all()[0].TransportCode, 120)

        if (self.is_complete):
            return 'Finish'
        elif(self.ReturnStatus == 'cancel'):
            return 'Cancel'
        elif(self.ReturnTransportCode):
            return 'Returning'
        elif(self.ReturnTransportCode == None and TransportCode):
            return 'Wait for Return'
        else:
            return 'Wait for Process'

    def resolve_SellerName(self: Meta.model, info):
        CacheName = 'ReturnRecord:{}:Seller'.format(self.pk)
        CacheData = cache.get(CacheName)
        if CacheData != None:
            Data : Client =  cache.get('Client:{}:Main'.format(CacheData))
            if Data:
                return Data.username
            else:
                Data = cache.get_or_set('Client:{}:Main'.format(CacheData), self.Seller, 3600)
                return Data.username
        else:
            Data = self.Seller
            cache.set(CacheName, Data.pk, 120)
            cache.get_or_set('Client:{}:Main'.format(Data.pk), Data, 3600)
            return Data.username

    def resolve_BuyerName(self: Meta.model, info):
        CacheName = 'ReturnRecord:{}:Buyer'.format(self.pk)
        CacheData = cache.get(CacheName)
        if CacheData != None:
            Data : Client =  cache.get('Client:{}:Main'.format(CacheData))
            if Data:
                return Data.username
            else:
                Data = cache.get_or_set('Client:{}:Main'.format(CacheData), self.Seller, 3600)
                return Data.username
        else:
            Data = self.Seller
            cache.set(CacheName, Data.pk, 120)
            cache.get_or_set('Client:{}:Main'.format(Data.pk), Data, 3600)
            return Data.username

class CombinePaymentAndCount(graphene.ObjectType):
    Payments = graphene.List(PaymentRecordType)
    Count = graphene.Int()

    def resolve_Payments(self, info, **kwargs):
        return self['Payments']
    
    def resolve_Count(self, info, **kwargs):
        return self['Count']

class CombineOrderAndCount(graphene.ObjectType):
    Orders = graphene.List(OrderType)
    Count = graphene.Int()

    def resolve_Payments(self, info, **kwargs):
        return self['Orders']
    
    def resolve_Count(self, info, **kwargs):
        return self['Count']

class CombineReturnProductAndCount(graphene.ObjectType):
    ReturnProduct = graphene.List(ReturnProductType)
    Count = graphene.Int()

    def resolve_ReturnProduct(self, info, **kwargs):
        return self['ReturnProduct']
    
    def resolve_Count(self, info, **kwargs):
        return self['Count']

class OrderQuery(graphene.ObjectType):
    PaymentList = graphene.Field(CombinePaymentAndCount, Start=graphene.Int(required=True), End=graphene.Int(required=True), Filter=graphene.String(required=False))
    OrderDetail = graphene.Field(OrderType, id=graphene.Int(required=True))
    OrderListSeller = graphene.Field(CombineOrderAndCount, Start=graphene.Int(required=True), End=graphene.Int(required=True), 
                                                           Status=graphene.String(required=False), TransportStatus=graphene.String(required=False), 
                                                           OrderStatus=graphene.String(required=False))
    ReturnProduct = graphene.Field(CombineReturnProductAndCount,Start=graphene.Int(required=True), End=graphene.Int(required=True), Filter=graphene.String(required=False), Identity=graphene.String(required=True))
    
    @Check_JWT_Valid_GraphQL
    def resolve_OrderListSeller(self, info, **kwargs):
        CacheName = 'Client:{}:OrderListSeller:Status_{}_TransportStatus_{}_OrderStatus_{}'.format(kwargs['user'].pk, kwargs.get("Status"), kwargs.get("TransportStatus"), kwargs.get("OrderStatus"))
        data = cache.get(CacheName)
        if data:
            cachedata = Resolve_Cache_Model_Field.Resolve_Model( prefetch_related=['paymentrecord_set'], Field=OrderRecord, Item_IDs=data[int(kwargs.get('Start')): int(kwargs.get('End'))])
            return {'Orders': cachedata, 'Count': len(data)}
        else:
            FilterList = []
            FilterList.append(Q(Seller = kwargs['user']))

            if kwargs.get("Status") == 'normal':
                FilterList.append(Q(Status = 'normal'))
            elif kwargs.get("Status") == 'cancel':
                FilterList.append(Q(Status = 'cancel'))

            if kwargs.get("TransportStatus") == 'waiting':
                FilterList.append(Q(TransportCode__isnull=True))
            elif kwargs.get("TransportStatus") == 'transport':
                FilterList.append(Q(TransportCode__isnull=False))

            if kwargs.get("OrderStatus") == 'finish':
                FilterList.append(Q(is_complete = True))
            elif kwargs.get("OrderStatus") == 'process':
                FilterList.append(Q(is_complete = False))

            data = OrderRecord.objects.filter(*FilterList).order_by('-id')
            cachedata = list(data.values_list('pk', flat=True))
            cache.set(CacheName, cachedata, 1200)
            return {'Orders': data[int(kwargs.get('Start')): int(kwargs.get('End'))], 'Count': len(cachedata)}

    @Check_JWT_Valid_GraphQL
    def resolve_ReturnProduct(self, info, **kwargs):
        CacheName = 'Client:{}:ReturnProduct:Identity_{}_Filter_{}'.format(kwargs['user'].pk, kwargs.get('Identity'), kwargs.get('Filter'))
        data = cache.get(CacheName)
        if data:
            cachedata = Resolve_Cache_Model_Field.Resolve_Model(prefetch_related=['Order__orderrecord_set'], Field=ReturnRecord, Item_IDs=data[int(kwargs.get('Start')): int(kwargs.get('End'))])
            return {'ReturnProduct': cachedata, 'Count': len(data)}
        else:
            FilterList = []
            FilterList.append(Q(Buyer = kwargs['user'])) if kwargs.get('Identity') == 'Buyer' else None
            FilterList.append(Q(Seller = kwargs['user'])) if kwargs.get('Identity') == 'Seller' else None
            FilterList.append(Q(ReturnTransportCode = '')) if kwargs.get('Filter') == 'WFR' else None
            FilterList.append(Q(is_complete = False)) if kwargs.get('Filter') == 'WFC' else None
            FilterList.append(Q(is_complete = True)) if kwargs.get('Filter') == 'Finish' else None
            FilterList.append(Q(ReturnStatus = 'cancel')) if kwargs.get('Filter') == 'Cancel' else None
            data = ReturnRecord.objects.filter(*FilterList).order_by('-id')
            cachedata = list(data.values_list('pk', flat=True))
            cache.set(CacheName, cachedata, 1200)
            return {'ReturnProduct': data[int(kwargs.get('Start')): int(kwargs.get('End'))], 'Count': len(cachedata)}

    @Check_JWT_Valid_GraphQL
    def resolve_OrderDetail(self, info, **kwargs):
        return Resolve_Cache_Model_Field.Resolve_Model(OrderRecord, kwargs.get('id'), prefetch_related=('paymentrecord_set', 'Seller', 'Buyer'))

    @Check_JWT_Valid_GraphQL
    def resolve_PaymentList(self, info, **kwargs):
        CacheName = 'Client:{}:PaymentList:Filter_{}'.format(kwargs['user'].pk, kwargs.get('Filter'))
        data = cache.get(CacheName)
        if data:
            cachedata = Resolve_Cache_Model_Field.Resolve_Model(prefetch_related=['Order', 'Order__OrderList'], Field=PaymentRecord, Item_IDs=data[int(kwargs.get('Start')): int(kwargs.get('End'))])
            return {'Payments': cachedata, 'Count': len(data)}
        else:
            FilterList = []
            FilterList.append(Q(Buyer = kwargs['user']))
            FilterList.append(Q(PaymentStatus = 'cancel')) if kwargs.get('Filter') == 'Cancel' else None
            FilterList.append(Q(PaymentStatus = 'unpaid')) if kwargs.get('Filter') == 'WFP' else None
            FilterList.append(Q(PaymentStatus = 'paid')) if kwargs.get('Filter') == 'Paid' else None
            data = PaymentRecord.objects.filter(*FilterList).order_by('-id')
            cachedata = list(data.values_list('pk', flat=True))
            cache.set(CacheName, cachedata, 1200)
            return {'Payments': data[int(kwargs.get('Start')): int(kwargs.get('End'))], 'Count': len(data)}

#### Mutation
class AddTransportCode(graphene.Mutation):
    class Arguments:
        OrderID = graphene.Int(required=True)
        TransportCode = graphene.String(required=True)

    status = graphene.Boolean()

    @Check_JWT_Valid_GraphQL
    def mutate(self, info, **kwargs):
        Order = OrderRecord.objects.filter(id=int(kwargs['OrderID']), Seller=kwargs['user']).prefetch_related('paymentrecord_set')
        if (Order.exists):
            Order = Order.first()
            Order.TransportCode = kwargs['TransportCode']
            Order.save()
            cache.delete_pattern('OrderRecord:{}*'.format(Order.pk))
            cache.delete_pattern('PaymentRecord:{}*'.format(Order.paymentrecord_set.all()[0].pk))    
            cache.delete('Client:{}:OrderDetail:id_{}'.format(kwargs['user'].pk,Order.pk))
            return AddTransportCode(status = True)
        else:
            return AddTransportCode(status = False)

class RefundReturnRecordItem(graphene.Mutation):
    class Arguments:
        ReturnID = graphene.Int(required=True)

    Result = graphene.String()

    @Check_JWT_Valid_GraphQL
    def mutate(self, info, **kwargs):
        try:
            ReturnData = ReturnRecord.objects.prefetch_related('Order', 'Order__orderrecord_set', 'Order__orderrecord_set__paymentrecord_set').\
                                              get(pk = kwargs['ReturnID'], is_complete=False, Seller=kwargs['user'])
            Result = ReturnData.Refund()
            return RefundReturnRecordItem(Result = json.dumps({'amount': Result['amount'], 'status': Result['status']}))
        except:
            return None

class RefundPayment(graphene.Mutation):
    class Arguments:
        OrderID = graphene.Int(required=True)
        OrderSubID = graphene.Int(required=True)
        OrderSubItemID = graphene.Int(required=True)
    
    status = graphene.Boolean()

    @Check_JWT_Valid_GraphQL
    def mutate(self, info, **kwargs):
        #try:
            ReturnData = OrderRecord.objects.prefetch_related('paymentrecord_set', 
                         Prefetch('OrderList', queryset=OrderItem.objects.filter(pk = kwargs['OrderSubID'])),
                         Prefetch("OrderList__SubItem", queryset=OrderSubItem.objects.filter(pk = kwargs['OrderSubItemID']))).\
                         annotate(RemainOrder = Count("OrderList__SubItem", filter=Q(OrderList__SubItem__Status='normal'))).\
                         get(pk = kwargs['OrderID'], Seller=kwargs['user'])
            
            Paymentrecord : PaymentRecord = ReturnData.paymentrecord_set.all()[0]
            TargetSub : OrderItem = ReturnData.OrderList.all()[0]
            TargetSubItem: OrderSubItem = TargetSub.SubItem.all()[0]
            TargetSubItem.Status = 'cancel'
            TargetSubItem.save()
            
            if ReturnData.RemainOrder == 1:
                ReturnData.is_complete = True
                ReturnData.Status = 'cancel'
                ReturnData.save()

            Paymentrecord.RefundFunction(Amount = TargetSubItem.Price * TargetSubItem.Count)
            cache.delete_pattern('OrderRecord:{}*'.format(ReturnData.pk))
            cache.delete_pattern('PaymentRecord:{}*'.format(ReturnData.paymentrecord_set.all()[0].pk))
            cache.delete('Client:{}:OrderDetail:id_{}'.format(kwargs['user'].pk, ReturnData.pk))
            return RefundPayment(status = True)
      #  except:
       #     return None

class ConfirmOrder(graphene.Mutation):

    status = graphene.Boolean()

    class Arguments:
        OrderSubItemKey = graphene.Int(required=False)
        OrderRecordKey = graphene.Int(required=False)

    @Check_JWT_Valid_GraphQL
    def mutate(self, info, **kwargs):

        def CheckOrderAlreadyFinish(Record):
            Remain_Record = Record.OrderList.filter(SubItem__Status = 'normal')
            if Remain_Record.exists():
                return False
            return True

        Record = OrderRecord.objects.filter(Q(Buyer = kwargs['user']), Q(OrderList__SubItem__pk = kwargs.get('OrderSubItemKey'))| Q(id = kwargs.get('OrderRecordKey'))).distinct().prefetch_related('paymentrecord_set').last()
        #### system should design payment to seller
        if (kwargs.get('OrderSubItemKey') and Record):
            SubItem = OrderSubItem.objects.get(pk=kwargs.get('OrderSubItemKey'))
            SubItem.Status = 'finish'
            SubItem.save()
            if CheckOrderAlreadyFinish(Record=Record):
                Record.is_complete=True
                Record.save()
            ##### Pay System Record
        elif(kwargs.get('OrderRecordKey') and Record):
            for x in Record.OrderList.filter(SubItem__Status = 'normal'):
                x.SubItem.update(Status = 'finish')
            Record.is_complete=True
            Record.save()
        else:
            return ConfirmOrder(status = False)
        cache.delete_pattern('OrderRecord:{}*'.format(Record.pk))
        cache.delete_pattern('PaymentRecord:{}*'.format(Record.paymentrecord_set.all()[0].pk))  
        cache.delete('Client:{}:OrderDetail:id_{}'.format(kwargs['user'].pk, Record.pk))
        return ConfirmOrder(status = True)

class AddReturnTransportCode(graphene.Mutation):
    class Arguments:
        ReturnID = graphene.Int(required=True)
        TransportCode = graphene.String(required=True)

    status = graphene.Boolean()

    @Check_JWT_Valid_GraphQL
    def mutate(self, info, **kwargs):
        Return = ReturnRecord.objects.filter(id=int(kwargs['ReturnID']), Buyer=kwargs['user'])
        if (Return.exists):
            Return = Return.first()
            Return.ReturnTransportCode = kwargs['TransportCode']
            Return.save()
            Return.Clearup_Cache()
            return AddReturnTransportCode(status = True)
        else:
            return AddReturnTransportCode(status = False)

class ReturnProductFunction(graphene.Mutation):
    class Arguments:
        SubProduct = graphene.Int(required=True)
        SubProductItem = graphene.Int(required=True)
        ErrorMessage = graphene.String(required=False)
    
    status = graphene.Boolean()

    @Check_JWT_Valid_GraphQL
    def mutate(self, info, **kwargs):
        Order = OrderItem.objects.filter(pk = kwargs.get('SubProduct'))
        if (Order.exists()):
            OrderData = Order.first()
            SubItem = OrderData.SubItem.filter(pk = int(kwargs.get('SubProductItem', None))).first()
            ReturnData = ReturnRecord(Buyer = kwargs.get('user', None), Seller = OrderData.orderrecord_set.first().Seller, Order=OrderData, 
                                      SubItem = SubItem, ErrorReason=kwargs.get('ErrorMessage', ''))
            SubItem.Status = 'return'
            ReturnData.save()
            SubItem.save()
            ReturnData.Clearup_Cache()
            return ReturnProductFunction(status = True)
        else:
            return None

class MakeComment(graphene.Mutation):
    class Arguments:
        OrderID = graphene.Int(required=True)
        OrderItemID = graphene.Int(required=True)
        SubItemID = graphene.Int(required=True)
        Score = graphene.Int(required=True)
        CommentTitle = graphene.String(required=True)
        CommentContent = graphene.String(required=True)

    status = graphene.Boolean()
    
    @Check_JWT_Valid_GraphQL
    def mutate(self, info, **kwargs):
        TargetOrder = OrderRecord.objects.filter(Buyer = kwargs['user'], id= int(kwargs['OrderID'])).select_related().\
                        prefetch_related(Prefetch('OrderList', queryset=OrderItem.objects.filter(id = int(kwargs['OrderItemID'])))).\
                        prefetch_related(Prefetch('OrderList__SubItem', queryset=OrderSubItem.objects.filter(id = int(kwargs['SubItemID'])))).\
                        first()
        TargetProduct = TargetOrder.OrderList.all()[0]
        TargetSubitem = TargetProduct.SubItem.all()[0]

        if (TargetSubitem.Comment):
            raise

        NewComment = ProductComment(User = kwargs['user'], CommentTitle = kwargs['CommentTitle'], CommentContent = kwargs['CommentContent'], 
                                    Score = kwargs['Score'], Product = TargetProduct.ProductID, CommentProductName = TargetSubitem.Name)
        NewComment.save()
        TargetSubitem.Comment = NewComment
        TargetSubitem.save()
        cache.delete_pattern('OrderSubItem:{}*'.format(TargetSubitem.pk))
        cache.delete('Product:{}:ProductDetail_Comment'.format(TargetProduct.ProductID.pk))
        return MakeComment(status = True)