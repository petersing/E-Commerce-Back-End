# Generated by Django 4.0.7 on 2022-08-31 13:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Product_API', '0022_alter_product_subitem'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='SubItem',
            field=models.ManyToManyField(blank=True, related_name='SubItem', to='Product_API.productsubitem'),
        ),
    ]
