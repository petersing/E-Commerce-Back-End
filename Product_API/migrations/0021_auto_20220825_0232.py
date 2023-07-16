# Generated by Django 3.2.12 on 2022-08-24 18:32

import Product_API.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Product_API', '0020_auto_20220825_0148'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='DescriptionImages',
        ),
        migrations.RemoveField(
            model_name='product',
            name='Images',
        ),
        migrations.AddField(
            model_name='product_image',
            name='Product',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='Product_API.product'),
        ),
        migrations.CreateModel(
            name='Product_Description_Images',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to=Product_API.models.Product_Description_Image_directory_path)),
                ('Product', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='Product_API.product')),
            ],
        ),
    ]