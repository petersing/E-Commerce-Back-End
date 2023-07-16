import graphene
from Authentication.Decorator import Check_JWT_Valid_GraphQL
from Order_API.models import PaymentRecord


class PaymentQuery(graphene.ObjectType):
    CheckPaymentStatus = graphene.String(access=graphene.String(required=True), StripeID=graphene.String(required=True))

    @Check_JWT_Valid_GraphQL
    def resolve_CheckPaymentStatus(self, info, **kwargs):
        Payment = PaymentRecord.objects.filter(Stripe_ID=kwargs.get('StripeID', None))
        if Payment.exists():
            return Payment.all()[0].CheckStripeServerStatus()

class RetrievePayment(graphene.Mutation):
    class Arguments:
        PaymentID=graphene.Int(required=True)
    
    StripeCode = graphene.String()

    @Check_JWT_Valid_GraphQL
    def mutate(self, info, **kwargs):
        Payment = PaymentRecord.objects.filter(id= kwargs.get("PaymentID", None)).last()
        if Payment:
            Previous_Record = Payment.Retrieve_Payment()
            return RetrievePayment(StripeCode=Previous_Record)

class CancelPayment(graphene.Mutation):
    class Arguments:
        PaymentID = graphene.Int(required=True)
    
    status = graphene.Boolean()

    @Check_JWT_Valid_GraphQL
    def mutate(self, info, **kwargs):
        Payment = PaymentRecord.objects.prefetch_related('Order').filter(id= kwargs.get("PaymentID", None)).last()
        if (Payment):
            Payment.Order.update(Status= 'cancel')
            return CancelPayment(status = Payment.Cancel_Payment())
        else:
            return CancelPayment(status = False)