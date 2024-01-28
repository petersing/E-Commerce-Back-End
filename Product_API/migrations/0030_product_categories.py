# Generated by Django 4.2.3 on 2023-12-29 14:37

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('Product_API', '0029_rename_productstauts_product_productstatus'),
    ]

    operations = [
        migrations.CreateModel(
            name='Product_Categories',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Category', models.CharField(max_length=300)),
                ('Product', models.ManyToManyField(blank=True, related_name='Product', to='Product_API.product')),
                ('User', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]