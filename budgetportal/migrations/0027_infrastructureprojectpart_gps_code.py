# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-08-15 10:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('budgetportal', '0026_add-provinces-to-infraproject'),
    ]

    operations = [
        migrations.AddField(
            model_name='infrastructureprojectpart',
            name='gps_code',
            field=models.CharField(default=b'', max_length=255),
        ),
    ]
