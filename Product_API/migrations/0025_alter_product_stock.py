# Generated by Django 4.1 on 2022-10-30 15:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Product_API', '0024_alter_product_stock'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='Stock',
            field=models.CharField(default='Enough', max_length=10),
        ),
    ]
