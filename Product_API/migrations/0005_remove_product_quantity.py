# Generated by Django 3.2.12 on 2022-06-22 13:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Product_API', '0004_auto_20220618_2252'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='Quantity',
        ),
    ]
