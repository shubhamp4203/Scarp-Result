# Generated by Django 4.1.2 on 2022-10-07 14:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='result',
            name='seat_no',
            field=models.CharField(max_length=30, null=True),
        ),
    ]
