# Generated by Django 3.2.12 on 2022-07-05 09:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Chat_API', '0005_auto_20220705_1741'),
    ]

    operations = [
        migrations.AlterField(
            model_name='messagedata',
            name='SenderName',
            field=models.CharField(max_length=50),
        ),
    ]
