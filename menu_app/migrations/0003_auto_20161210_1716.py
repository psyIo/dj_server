# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-12-10 17:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('menu_app', '0002_auto_20161210_1612'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='menuitem',
            name='item_type',
        ),
        migrations.AddField(
            model_name='menuitem',
            name='is_category',
            field=models.BooleanField(default=False),
            preserve_default=False,
        ),
    ]