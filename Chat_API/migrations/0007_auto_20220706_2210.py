# Generated by Django 3.2.12 on 2022-07-06 14:10

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('Chat_API', '0006_alter_messagedata_sendername'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='chat_channel_record',
            name='User_A',
        ),
        migrations.RemoveField(
            model_name='chat_channel_record',
            name='User_B',
        ),
        migrations.AddField(
            model_name='chat_channel_record',
            name='User',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL),
        ),
    ]
