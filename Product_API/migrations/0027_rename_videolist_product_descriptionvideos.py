# Generated by Django 4.1.5 on 2023-04-01 13:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Product_API', '0026_product_videolist'),
    ]

    operations = [
        migrations.RenameField(
            model_name='product',
            old_name='VideoList',
            new_name='DescriptionVideos',
        ),
    ]
