# Generated by Django 3.2.12 on 2022-07-05 09:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Chat_API', '0004_messagedata_send'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='messagedata',
            name='Send',
        ),
        migrations.AddField(
            model_name='messagedata',
            name='SenderName',
            field=models.CharField(default='', max_length=50),
        ),
    ]
