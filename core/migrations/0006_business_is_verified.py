# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-27 05:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_auto_20160920_0632'),
    ]

    operations = [
        migrations.AddField(
            model_name='business',
            name='is_verified',
            field=models.BooleanField(default=False, verbose_name='Is Verified'),
        ),
    ]
