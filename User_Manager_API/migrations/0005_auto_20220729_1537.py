# Generated by Django 3.2.12 on 2022-07-29 07:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('User_Manager_API', '0004_auto_20220729_1511'),
    ]

    operations = [
        migrations.CreateModel(
            name='BusinessSubscribe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('SubScribe_End', models.DateTimeField(null=True)),
                ('SubScribe_Date', models.DateTimeField(null=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='client',
            name='SubScribe_Date',
        ),
        migrations.RemoveField(
            model_name='client',
            name='SubScribe_End',
        ),
        migrations.AddField(
            model_name='client',
            name='Subscribe',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='User_Manager_API.businesssubscribe'),
        ),
    ]
