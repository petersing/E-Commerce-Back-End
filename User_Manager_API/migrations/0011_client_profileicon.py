# Generated by Django 3.2.12 on 2022-07-31 12:18

import User_Manager_API.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('User_Manager_API', '0010_alter_businesssubscribe_subscribe_plan'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='ProfileIcon',
            field=models.ImageField(null=True, upload_to=User_Manager_API.models.user_directory_path),
        ),
    ]
