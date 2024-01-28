from django.db import models
import time
from PIL import Image
import os
from django.conf import settings
from django.db.models import Q
from User_Manager_API.models import Client
from django.core.cache import cache

def Product_Image_directory_path(instance, filename):
    year, month, day= map(str, time.strftime("%Y %m %d").split())
    ext = filename.split('.').pop()
    filename = '{0}_{1}.{2}'.format(instance.Product.ProductName, time.time() , ext)
    return os.path.join('E-Commerce-DataBase\Product_DataBase', year, month, day, instance.Product.Seller.username ,filename)

def Product_Description_Image_directory_path(instance, filename):
    year, month, day= map(str, time.strftime("%Y %m %d").split())
    ext = filename.split('.').pop()
    filename = '{0}_Description_{1}.{2}'.format(instance.Product.ProductName, time.time() , ext)
    return os.path.join('E-Commerce-DataBase\Product_DataBase', year, month, day, instance.Product.Seller.username ,filename)
    

class ProductSubItem(models.Model):
    Name = models.CharField(max_length=100)
    Sell = models.IntegerField(default=0)
    Price = models.IntegerField()
    Quantity = models.IntegerField()
    Properties = models.JSONField(default=dict)
    
    def AllContent(self):
        return {'Name': self.Name, 'Price': self.Price, "Quantity": self.Quantity}


class Product(models.Model):

    id = models.AutoField(primary_key=True, editable=False);
    Description = models.JSONField(default=list)
    DescriptionVideos = models.JSONField(default=list)
    ProductName = models.CharField(default='', max_length=30)
    ShippingLocation = models.CharField(default='', max_length=50)
    SubItem = models.ManyToManyField(ProductSubItem, related_name='SubItem', blank=True)
    date_created = models.DateTimeField(auto_now_add=True, blank=True)
    Category = models.CharField(max_length=300)
    is_public = models.BooleanField(default=True)  
    InvalidSubItem = models.ManyToManyField(ProductSubItem, related_name='Invalid_SubItem', blank=True)
    Stock = models.CharField(max_length=10, default='Enough')
    Seller = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True)
    ProductStatus = models.BooleanField(default=True)

    def Clearup_Stock_Cache(self):
        cache.delete_pattern('Product:{}:SubItem*'.format(self.id))

    def Get_Cart_Response(self, ClientCart):
        SubTotalPrice = 0
        SubItems = {}
        AllOption = {}
        i : ProductSubItem
        for i in self.SubItem.all():
            if i.pk in ClientCart:
                SubItems[i.pk] = {'Count': ClientCart[i.pk]}
                SubTotalPrice += ClientCart[i.pk]*i.Price

            AllOption[i.pk] = i.AllContent()
        return  {'image': settings.IMAGE_SERVER_URL + str(self.product_image_set.first()), 'ProductName': self.ProductName, 'id': self.id, 
                'AllOption': AllOption, "SubItems": SubItems, "SubTotalPrice": SubTotalPrice, "Author": self.Seller.username}
    
    def Get_Lower_Price(self):
        x: ProductSubItem
        PriceList = []
        for x in self.SubItem.all():
            PriceList.append(x.Price)
        return min(PriceList)
    
    def BasicInformation(self):
        CacheName = 'Product:{}:BasicInformation'.format(self.id)
        CacheData = cache.get(CacheName)
        if CacheData != None:
            return CacheData
        else:
            Data = {'Price': self.Get_Lower_Price(), "Author": self.Seller.username, 'id': self.id}
            cache.set(CacheName, Data, 3600)
            return Data
        
class Product_Image(models.Model):
    Product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    image = models.ImageField(upload_to= Product_Image_directory_path)

    #### Limit the image size to 1024x 1024   MORE PIXEL MORE PIRCE REMEMBERRRRRRRRRRRRRRRRRRRRRRRRRRRR
    def save(self, *args, **kwargs) -> None:
        instance = super(Product_Image, self).save(*args, **kwargs)
        img = Image.open(self.image.path)
        img.thumbnail(settings.MAX_IMAGE_SIZE)
        img.save(self.image.path)
        return instance

    def __str__(self) -> str:
        return str(self.image)

class Product_Description_Images(models.Model):
    Product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    image = models.ImageField(upload_to= Product_Description_Image_directory_path)
    #### Limit the image size to 1024x 1024   MORE PIXEL MORE PIRCE REMEMBERRRRRRRRRRRRRRRRRRRRRRRRRRRR
    def save(self, *args, **kwargs) -> None:
        instance = super(Product_Description_Images, self).save(*args, **kwargs)
        img = Image.open(self.image.path)
        img.thumbnail(settings.MAX_IMAGE_SIZE)
        img.save(self.image.path)
        return instance

    def __str__(self) -> str:
        return str(self.image)
    