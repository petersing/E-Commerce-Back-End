# Generated by Django 3.2.12 on 2022-07-29 08:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('User_Manager_API', '0006_alter_businesssubscribe_subscribe_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='businesssubscribe',
            name='SubScribe_Date',
            field=models.DateTimeField(null=True),
        ),
    ]
