# Generated by Django 3.2.12 on 2022-07-04 17:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Chat_API', '0002_auto_20220705_0142'),
    ]

    operations = [
        migrations.AddField(
            model_name='chat_channel_record',
            name='ChatName',
            field=models.CharField(default='', max_length=100),
        ),
    ]
