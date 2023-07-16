# Generated by Django 3.2.12 on 2022-08-24 17:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Product_API', '0019_auto_20220804_2234'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product_image',
            name='product',
        ),
        migrations.AddField(
            model_name='product',
            name='DescriptionImages',
            field=models.ManyToManyField(blank=True, related_name='Description_Image', to='Product_API.Product_Image'),
        ),
        migrations.AddField(
            model_name='product',
            name='Images',
            field=models.ManyToManyField(blank=True, related_name='Product_Image', to='Product_API.Product_Image'),
        ),
    ]