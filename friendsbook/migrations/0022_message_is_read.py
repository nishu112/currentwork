# Generated by Django 2.0.2 on 2018-02-25 15:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('friendsbook', '0021_remove_profile_is_read'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='is_read',
            field=models.BooleanField(default=False),
        ),
    ]