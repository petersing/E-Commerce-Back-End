from rest_framework import serializers
from .models import Product, Product_Image, ProductSubItem, Product_Description_Images
from rest_framework import exceptions
from typing import *
from django.core.cache import cache


class Product_Serializers(serializers.ModelSerializer):
    Images = serializers.ListField(child=serializers.FileField( max_length=100000,allow_empty_file=False,use_url=False ))
    DescriptionImages = serializers.ListField(child=serializers.FileField( max_length=100000,allow_empty_file=False,use_url=False), required =False)
    RemoveImages = serializers.JSONField(required=False)
    RemoveDescriptionImages = serializers.JSONField(required=False)
    RemoveSubItem = serializers.JSONField(required=False)
    SubItemList = serializers.JSONField(required=True)

    @staticmethod
    def CheckEnoughStock(Product: Product, SubItem: ProductSubItem) -> None:
        StockProportion =  SubItem.Quantity/ (SubItem.Sell + SubItem.Quantity)
        if (StockProportion == 0):
            Product.Stock = 'SellOut'
        elif(StockProportion < 0.5):
            Product.Stock = 'Small'
        else:
            Product.Stock = 'Enough'

    def create(self, validated_data: List[Any]) -> Product:
        Images = validated_data.pop('Images')
        DescriptionImages = validated_data.pop('DescriptionImages')
        SubItemList: List[Dict] = validated_data.pop('SubItemList')

        SubItem = []
        for Item in SubItemList:
            if (len(set(Item.keys()).intersection(('Name', 'Price', 'Properties', 'Quantity'))) == 4 and len(Item.keys()) == 4):
                SubItem.append(ProductSubItem(**Item))
            else:
                raise exceptions.APIException("Data Type not match, please use console to add product")

        product= Product(**validated_data)
        product.save()

        #### Create Images
        Product_Image.objects.bulk_create((Product_Image(Product= product, image = img) for img in Images))
        Product_Description_Images.objects.bulk_create((Product_Description_Images(Product= product, image = img) for img in DescriptionImages))

        ProductSubItem.objects.bulk_create(SubItem)

        product.SubItem.set(SubItem)

        cache.delete_pattern('PersonalProduct:User_{}*'.format(validated_data['Seller'].username))
        
       # User_Product_Caches(UserName=product.Seller.username, ForceUpdata=True)

        return product


    def update(self, instance: Product, validated_data: List[Any]) -> Product:
        instance.Description = validated_data['Description']
        instance.ProductName = validated_data['ProductName']
        instance.ShippingLocation = validated_data['ShippingLocation']
        instance.Category = validated_data['Category']
        instance.ProductStatus = validated_data['ProductStatus']

        if not validated_data["ProductStatus"]:
            PreDisable_Key: set = cache.get(('ChangeProduct'), set())
            PreDisable_Key.add(instance.id)
        else:
            PreDisable_Key: set = cache.get(('ChangeProduct'), set())
            PreDisable_Key.discard(instance.id)
        
        cache.set(('ChangeProduct'), PreDisable_Key)

        #### SubItem
        SubItem : Dict[int, ProductSubItem] = {}
        InvalideSubItem = {}

        i: ProductSubItem
        for i in instance.SubItem.all():
            if (i.pk in validated_data['RemoveSubItem']):
                InvalideSubItem[i.pk] = i
            else:
                SubItem[i.pk] = i

        item: Dict[Any]
        for item in validated_data['SubItemList']:
            if not (item.get('id', False)):
                NewSub = ProductSubItem(**item)
                NewSub.save()
                SubItem[NewSub.pk] = NewSub
            elif (item['id'] in SubItem):
                SubItem[item['id']].Quantity = item['Quantity']
                SubItem[item['id']].Name = item['Name']
                SubItem[item['id']].Price = item['Price']
                SubItem[item['id']].Properties = item['Properties']
                SubItem[item['id']].save()
                self.CheckEnoughStock(Product=instance, SubItem=SubItem[item['id']])

        instance.SubItem.set(SubItem.values())
        instance.InvalidSubItem.set(InvalideSubItem.values())
        
        #### Remove Images
        Product_Image.objects.filter(image__in=validated_data['RemoveImages']).delete()
        Product_Description_Images.objects.filter(image__in=validated_data['RemoveDescriptionImages']).delete()


        #### Create Images
        Product_Image.objects.bulk_create((Product_Image(Product= instance, image = img) for img in validated_data["Images"]))
        Product_Description_Images.objects.bulk_create((Product_Description_Images(Product= instance, image = img) for img in validated_data['DescriptionImages']))

        instance.save()
      #  Product_Caches(instance.id, True)
       # User_Product_Caches(UserName=instance.Seller.username, ForceUpdata=True)
        return instance
    
    class Meta:
        model = Product
        fields = '__all__'

