# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-04-18 23:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Training',
            fields=[
                ('uuid', models.CharField(max_length=64, primary_key=True, serialize=False)),
                ('data', models.TextField(default='[]')),
                ('target', models.TextField(default='[]')),
            ],
        ),
    ]
