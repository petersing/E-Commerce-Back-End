import itertools
from rest_framework import serializers
from .models import OrderRecord, OrderSubItem, PaymentRecord, OrderItem, ProductSnapShot, ProductSnapShot_Image, ProductSnapShot_Description_Images
from e_commerce_server.Public_Function import Convert_Internal_Image_To_Django_Style_File
from django.conf import settings
from Product_API.models import Product, ProductSubItem
from User_Manager_API.models import Client
from e_commerce_server.Public_Function import Create_Stripe_Payment
from rest_framework import exceptions
from typing import *
from django.db import transaction

class Payment_Serializers(serializers.ModelSerializer):
    class Meta:
        model = PaymentRecord
        fields = '__all__'


#### This algorithm may be a bad idea, but i can not found the suitable method for here!!!
class Make_Order_Serializers(serializers.Serializer):
    ClientInformation = serializers.JSONField()
    OrderData = serializers.JSONField()
    ClientID = serializers.UUIDField()
    PaymentList = ("Credit Card")
    DeliveryList = ("Free Shipping", "Express Shipping", "Speed Shipping")

    def __init__(self, instance=None, data=..., **kwargs):
        super().__init__(instance, data, **kwargs)
        self.TotalPrice = 0
        self.OrderList : Dict[Any, OrderRecord]= {}
        self.OrderItemList: Dict[str, List] = {}
        self.ProductChangeList: List[Product] = []
        self.SubItem_List = {}
        self.ProductSnapShotList = []
        self.ImageList = []
        self.DescriptionImageList = []

    @staticmethod
    def UpdateStock(ProductItem: Product , SubItem: ProductSubItem):
        StockProportion =  SubItem.Quantity/ (SubItem.Sell + SubItem.Quantity)
        if (StockProportion == 0):
            ProductItem.Stock = "SellOut"
        elif(StockProportion < 0.5):
            ProductItem.Stock = "Small"
        else:
            ProductItem.Stock = "Enough"

    def Checking_And_Update_SubItem(self, Data, Author, validated_data):
        PaymentMethod = validated_data['ClientInformation'].get("PaymentMethod", None)
        DeliveryMethod =validated_data['ClientInformation'].get('DeliveryMethod', None)
        Address = validated_data['ClientInformation'].get("Address", None)
        Phone =  validated_data['ClientInformation'].get('Phone', None)


        if (PaymentMethod not in self.PaymentList) or (DeliveryMethod not in self.DeliveryList) or (not Address) or (not Phone):
            
            raise exceptions.NotAcceptable('Please Input Payment Method,Delivery Method, Address and Phone')

        sorted_item = sorted(list(Data),key=lambda x:x['id'])

        ProductList = Product.objects.filter(id__in = [x['id'] for x in sorted_item]).prefetch_related("product_image_set", 'product_description_images_set', "SubItem").order_by('id').all()
        
        
        for ProductData, Sub in zip(ProductList, sorted_item):
            ### Check enough Stock and change database BUT NOT SAVE
            CheckStockEnough = []
            AllSubItem = ProductData.SubItem.filter(pk__in = Sub['SubItems'].keys()).order_by('id').all() 
            for sub_loc, x in enumerate(sorted(Sub['SubItems'].items(), key=lambda x: x[0])):
                Product_SubItem : ProductSubItem = AllSubItem[sub_loc]
                CheckStockEnough.append(Product_SubItem.Quantity >= x[1]['Count'])
                Product_SubItem.Quantity -= x[1]['Count']
                Product_SubItem.Sell += x[1]['Count']
                self.SubItem_List[str(Product_SubItem.pk)] = Product_SubItem
                ### Renew DataBase record for stock
                self.UpdateStock(ProductData, Product_SubItem)

            if all(CheckStockEnough):
                ProductImageList = ProductData.product_image_set.all()
                ProductDescriptionImageList = ProductData.product_description_images_set.all()
                SubItems = []
                for x in Sub['SubItems'].items():
                    Product_SubItem = self.SubItem_List[str(x[0])]
                    SubItems.append(OrderSubItem(Count = x[1]['Count'], Name=Product_SubItem.Name, Price=Product_SubItem.Price, Status= 'normal'))
                    self.TotalPrice += x[1]['Count']*Product_SubItem.Price

                Orderitem = OrderItem(ProductTitle=ProductData.ProductName, ProductID=ProductData)
                Orderitem.OrderImage.name = str(ProductImageList[0])

                SnapShot = ProductSnapShot(Description = ProductData.Description, 
                                           ProductName = ProductData.ProductName, 
                                           ShippingLocation = ProductData.ShippingLocation, 
                                           Seller = ProductData.Seller,
                                           OrderItemRecord = Orderitem)
            
                self.ProductSnapShotList.append(SnapShot)

                for img in ProductImageList:
                    images = ProductSnapShot_Image(Product= SnapShot)
                    images.image.name = str(img)
                    self.ImageList.append(images)

                for img in ProductDescriptionImageList:
                    images = ProductSnapShot_Description_Images(Product= SnapShot)
                    images.image.name = str(img)
                    self.DescriptionImageList.append(images)
                
                if self.OrderItemList.get(Author):
                    self.OrderItemList[Author].append({'order': Orderitem, 'sub': SubItems, 'SnapShot': SnapShot}) 
                else: 
                    self.OrderItemList[Author] = [{'order': Orderitem, 'sub': SubItems, 'SnapShot': SnapShot}]
                self.ProductChangeList.append(ProductData)

                ###Delte Stock Record
                ProductData.Clearup_Stock_Cache()
            else:
                raise exceptions.ErrorDetail("The Stock is not enough")
            

        NewOrder = OrderRecord( Buyer = Client.objects.get(id= validated_data['ClientID']), 
                                Seller = Client.objects.get(username = Author), 
                                PaymentMethod = PaymentMethod, 
                                DeliveryMethod = DeliveryMethod,
                                Address = Address,
                                Phone =  Phone)

        self.OrderList[Author] = NewOrder

    def create(self, validated_data):

        for Author, Data in itertools.groupby(validated_data['OrderData'], lambda item: item["Author"]):
            self.Checking_And_Update_SubItem(Data=Data, Author=Author, validated_data=validated_data)

        if self.TotalPrice > 999999.99:
            raise exceptions.NotAcceptable('The Checkout total amount over the max $999,999.99')
        
        with transaction.atomic():
            #### Makesure the stock is enough for buyer
            for i in self.OrderList.keys():
                self.OrderList[i].save()
                self.OrderList[i].Clearup_Cache()
                for x in self.OrderItemList[i]: 

                    Orderitems : OrderItem = x['order']
                    Orderitems.save()

                    SnapShot: ProductSnapShot = x["SnapShot"]
                    SnapShot.save()

                    OrderSubItem.objects.bulk_create(x['sub'])
                    Orderitems.SubItem.set(x['sub'])
                    self.OrderList[i].OrderList.add(Orderitems)

            #### Create Image
            ProductSnapShot_Image.objects.bulk_create(self.ImageList)
            ProductSnapShot_Description_Images.objects.bulk_create(self.DescriptionImageList)
            
            Product.objects.bulk_update(self.ProductChangeList, ['Stock'])
            
            ProductSubItem.objects.bulk_update(self.SubItem_List.values(), ['Quantity', "Sell"])


            StripeRecord = Create_Stripe_Payment(self.TotalPrice)
            Payment = Payment_Serializers(data = {'Stripe_ID' : StripeRecord['ID'], 'Buyer' : validated_data['ClientID'], 'payment_intent': StripeRecord['payment_intent']})
            Payment_record : PaymentRecord = Payment.save() if Payment.is_valid() else print(Payment.errors)
            Payment_record.Order.add(*self.OrderList.values())  

        Payment_record.Clearup_Cache()

        StripeRecord = {**StripeRecord, "DateCreated": Payment_record.date_created}
        
        return StripeRecord