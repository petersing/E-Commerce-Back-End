# Generated by Django 3.2.12 on 2022-06-18 14:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Product_API', '0003_product_quantity'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='InvalidSubItem',
            field=models.JSONField(default=dict),
        ),
        migrations.AlterField(
            model_name='product',
            name='SubItem',
            field=models.JSONField(default=dict),
        ),
    ]