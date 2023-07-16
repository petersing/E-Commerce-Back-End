# Generated by Django 4.1 on 2022-09-27 08:44

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('Chat_API', '0012_remove_messagedata_sendername_messagedata_sender'),
    ]

    operations = [
        migrations.AlterField(
            model_name='messagedata',
            name='Sender',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
