import graphene
from .OrderSchema import AddTransportCode, MakeComment, ReturnProductFunction, RefundReturnRecordItem, RefundPayment, ConfirmOrder, AddReturnTransportCode, OrderQuery
from .UserSchema import UserQuery, CreateOrUpdateAddress, UpdateUserAds, CreateOrUpdateProductCategory, ChangeCategoriesProperties
from .ProductSchema import ProductQuery
from .CartSchema import ModifyCartFunction
from .AnalysisSchema import AnalysisQuery
from .ChatSchema import ChatQuery
from .CartSchema import CartQuery
from .PaymentSchema import PaymentQuery, CancelPayment, RetrievePayment


class Query(PaymentQuery, CartQuery, ChatQuery, UserQuery, OrderQuery, ProductQuery, AnalysisQuery, graphene.ObjectType):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
class Mutations(graphene.ObjectType):
    ###Cart Function
    ModifyCartFunction = ModifyCartFunction.Field()

    ####Order/Payment Function
    ReturnProductFunction = ReturnProductFunction.Field()
    AddTransportCodeFunction = AddTransportCode.Field()
    AddReturnTransportCode = AddReturnTransportCode.Field()
    RefundItem = RefundReturnRecordItem.Field()
    RefundPaymentFunction = RefundPayment.Field()
    ConfirmOrder = ConfirmOrder.Field()
    MakeComment = MakeComment.Field()
    CancelPayment = CancelPayment.Field()
    RetrievePayment = RetrievePayment.Field()
    
    ### User Function
    CreateOrUpdateAddress = CreateOrUpdateAddress.Field()
    UpdateUserAds = UpdateUserAds.Field()
    CreateOrUpdateCategory = CreateOrUpdateProductCategory.Field()
    ChangeCategoriesProperties = ChangeCategoriesProperties.Field()
    

schema = graphene.Schema(query=Query, mutation=Mutations)