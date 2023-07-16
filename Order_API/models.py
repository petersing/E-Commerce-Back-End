from django.db import models
import time
import os

from User_Manager_API.models import Client
from Product_API.models import Product, ProductSubItem
import datetime
from django.utils import timezone
import stripe
from django.core.cache import cache

class ProductComment(models.Model):
    User = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True)
    CommentTitle = models.CharField(max_length=200)
    CommentContent = models.CharField(max_length=1000)
    Date = models.DateTimeField(auto_now_add=True, blank=True)
    Score = models.IntegerField()
    Product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    CommentProductName = models.CharField(max_length=200)

class OrderSubItem(models.Model):
    Name =  models.CharField(max_length=100)
    Count = models.IntegerField()
    Price = models.IntegerField()
    Status = models.CharField(max_length=100)
    Comment = models.ForeignKey(ProductComment, on_delete=models.SET_NULL, null=True)

class OrderItem(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    ProductTitle = models.CharField(max_length=100)
    SubItem = models.ManyToManyField(OrderSubItem, blank=True)
    ProductID = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    OrderImage = models.ImageField()

class OrderRecord(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    Buyer = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, related_name='%(class)s_Buyer')
    Seller = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, related_name='%(class)s_Seller')
    OrderList = models.ManyToManyField(OrderItem, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    PaymentMethod = models.CharField(max_length=20)
    DeliveryMethod = models.CharField(max_length=20)
    TransportCode = models.CharField(max_length=200, null=True)
    is_complete = models.BooleanField(default=False)
    Phone = models.CharField(max_length=20)
    Address = models.CharField(max_length=200)
    Status = models.CharField(max_length=20, default='normal')

    def Clearup_Cache(self):
        cache.delete_pattern('Client:{}:Order*'.format(self.Seller.pk))

class PaymentRecord(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    Stripe_ID = models.CharField(max_length=200)
    payment_intent = models.CharField(max_length=200)
    PaymentStatus = models.CharField(default='unpaid', max_length=20)
    Order = models.ManyToManyField(OrderRecord, blank=True)
    date_created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    Buyer = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True)

    def Clearup_Cache(self):
        cache.delete_pattern('Client:{}:Payment*'.format(self.Buyer.pk))

    def RefundFunction(self, Amount):
        if (self.payment_intent == ''):
           StripeData = stripe.checkout.Session.retrieve(self.Stripe_ID)
           RefundResult = stripe.Refund.create(payment_intent=StripeData['payment_intent'] , amount=Amount)
           self.payment_intent = StripeData['payment_intent']
           self.save()
        else:
            RefundResult = stripe.Refund.create(payment_intent=self.payment_intent , amount=Amount)
        return RefundResult

    def CheckStripeServerStatus(self):
        if (self.PaymentStatus == 'paid' or self.PaymentStatus == 'cancel'):
            return self.PaymentStatus
        elif((datetime.datetime.now(tz=timezone.utc).timestamp() - self.date_created.timestamp())> 3600):
            Result =stripe.checkout.Session.expire(self.Stripe_ID)
            self.PaymentStatus = 'cancel'
            self.save()
            return self.PaymentStatus
        else:
            status = stripe.checkout.Session.retrieve(self.Stripe_ID)['payment_status']
            self.PaymentStatus = status
            self.save()
            return self.PaymentStatus
    def Cancel_Payment(self):
        try:
            Result = stripe.checkout.Session.expire(self.Stripe_ID)
            self.PaymentStatus = 'cancel'
            self.save()
            return True
        except:
            return False

    def Retrieve_Payment(self):
        StripeData = stripe.checkout.Session.retrieve(self.Stripe_ID)
        return StripeData['url']

class ReturnRecord(models.Model):
    Buyer = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, related_name='%(class)s_Buyer')
    Seller = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, related_name='%(class)s_Seller')
    Order = models.ForeignKey(OrderItem, on_delete=models.SET_NULL, null=True)
    SubItem = models.ForeignKey(OrderSubItem, on_delete=models.SET_NULL, null=True)
    ReturnTransportCode = models.CharField(max_length=100, null = True)
    ErrorReason = models.CharField(max_length=200, default='')
    ReturnStatus = models.CharField(max_length=20, default='normal')
    is_complete = models.BooleanField(default=False)

    def Clearup_Cache(self):
        cache.delete_pattern('Client:{}:Return*'.format(self.Buyer.pk))
        cache.delete_pattern('Client:{}:Return*'.format(self.Seller.pk))
        cache.delete_pattern('ReturnRecord:{}*'.format(self.pk))

    def Refund(self):
        Price = self.SubItem.Count * self.SubItem.Price
        OrderPaymentRecord : PaymentRecord= self.Order.orderrecord_set.all()[0].paymentrecord_set.all()[0]
        RefundResult = OrderPaymentRecord.RefundFunction(Amount=Price)
        self.is_complete = True
        self.save()
        self.Clearup_Cache()
        return RefundResult

class ProductSnapShot(models.Model):
    id = models.AutoField(primary_key=True, editable=False);
    Description = models.JSONField(default=list)
    ProductName = models.CharField(default='', max_length=30)
    ShippingLocation = models.CharField(default='', max_length=50)
    date_created = models.DateTimeField(auto_now_add=True, blank=True)
    Seller = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True)
    OrderItemRecord = models.ForeignKey(OrderItem, on_delete=models.CASCADE, null=True)

class ProductSnapShot_Image(models.Model):
    Product = models.ForeignKey(ProductSnapShot, on_delete=models.CASCADE, null=True)
    image = models.ImageField()

    def __str__(self) -> str:
        return str(self.image)

class ProductSnapShot_Description_Images(models.Model):
    Product = models.ForeignKey(ProductSnapShot, on_delete=models.CASCADE, null=True)
    image = models.ImageField()

    def __str__(self) -> str:
        return str(self.image)