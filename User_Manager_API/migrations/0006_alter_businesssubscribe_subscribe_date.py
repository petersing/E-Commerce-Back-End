# Generated by Django 3.2.12 on 2022-07-29 08:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('User_Manager_API', '0005_auto_20220729_1537'),
    ]

    operations = [
        migrations.AlterField(
            model_name='businesssubscribe',
            name='SubScribe_Date',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
