# Generated by Django 3.2.12 on 2022-07-05 09:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('Chat_API', '0003_chat_channel_record_chatname'),
    ]

    operations = [
        migrations.AddField(
            model_name='messagedata',
            name='Send',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
    ]
