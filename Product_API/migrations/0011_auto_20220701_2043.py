# Generated by Django 3.2.12 on 2022-07-01 12:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Product_API', '0010_auto_20220701_2035'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='InvalidSubItem',
            field=models.ManyToManyField(null=True, related_name='Invalid_SubItem', to='Product_API.ProductSubItem'),
        ),
        migrations.AlterField(
            model_name='product',
            name='SubItem',
            field=models.ManyToManyField(null=True, related_name='SubItem', to='Product_API.ProductSubItem'),
        ),
    ]
