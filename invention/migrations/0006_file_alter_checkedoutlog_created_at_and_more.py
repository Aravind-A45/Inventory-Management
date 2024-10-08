# Generated by Django 4.2.8 on 2024-03-07 13:52

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invention', '0005_alter_checkedoutlog_created_at_alter_log_created_at_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='uploads')),
            ],
        ),
        migrations.AlterField(
            model_name='checkedoutlog',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2024, 3, 7, 19, 22, 27, 234246)),
        ),
        migrations.AlterField(
            model_name='log',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2024, 3, 7, 19, 22, 27, 234246)),
        ),
        migrations.AlterField(
            model_name='wastage',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2024, 3, 7, 19, 22, 27, 232217)),
        ),
    ]
