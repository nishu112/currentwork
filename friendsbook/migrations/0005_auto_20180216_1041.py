# Generated by Django 2.0.2 on 2018-02-16 10:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('friendsbook', '0004_groups_sid'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='groups',
            name='cover',
        ),
        migrations.AlterField(
            model_name='groups',
            name='sid',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='cover_photo', to='friendsbook.Status'),
        ),
    ]