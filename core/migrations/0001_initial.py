# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-14 07:43
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Amenity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
            ],
            options={
                'verbose_name': 'Amenity',
                'verbose_name_plural': 'Amenities',
            },
        ),
        migrations.CreateModel(
            name='Business',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('taxpayer_name', models.CharField(max_length=255, verbose_name="Taxpayer's Name")),
                ('business_name', models.CharField(blank=True, max_length=255, null=True, verbose_name='Business Name')),
                ('address', models.TextField(blank=True, null=True, verbose_name='Business Address')),
                ('tel_number', models.CharField(max_length=100, verbose_name='Telephone Number')),
                ('barangay', models.CharField(blank=True, max_length=255, null=True, verbose_name='Barangay')),
                ('capital', models.BigIntegerField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Business',
                'verbose_name_plural': 'Businesses',
            },
        ),
        migrations.CreateModel(
            name='Division',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Description')),
                ('code', models.CharField(max_length=2, verbose_name='Code')),
            ],
            options={
                'verbose_name': 'Division',
                'verbose_name_plural': 'Divisions',
            },
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('establishment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Business')),
            ],
            options={
                'verbose_name': 'Location',
                'verbose_name_plural': 'Locations',
            },
        ),
        migrations.CreateModel(
            name='Section',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Description')),
                ('code', models.CharField(max_length=1, verbose_name='Code')),
            ],
            options={
                'verbose_name': 'Section',
                'verbose_name_plural': 'Sections',
            },
        ),
        migrations.CreateModel(
            name='Sector',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Description')),
                ('code', models.CharField(max_length=10, verbose_name='Code')),
            ],
            options={
                'verbose_name': 'Sector',
                'verbose_name_plural': 'Sectors',
            },
        ),
        migrations.CreateModel(
            name='Status',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
                ('description', models.TextField(verbose_name='Description')),
            ],
            options={
                'verbose_name': 'Status',
                'verbose_name_plural': 'Statuses',
            },
        ),
        migrations.AddField(
            model_name='division',
            name='section',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.Section'),
        ),
        migrations.AddField(
            model_name='business',
            name='division',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.Division'),
        ),
        migrations.AddField(
            model_name='business',
            name='sector',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.Sector'),
        ),
        migrations.AddField(
            model_name='business',
            name='status',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.Status'),
        ),
        migrations.AddField(
            model_name='amenity',
            name='establishment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Business'),
        ),
    ]
