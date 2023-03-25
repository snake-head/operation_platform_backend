# Generated by Django 4.1.7 on 2023-03-25 05:15

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Video',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('videoId', models.CharField(max_length=50, unique=True)),
                ('videoName', models.CharField(max_length=100, unique=True)),
                ('videoUrl', models.CharField(max_length=255, unique=True)),
                ('coverImgUrl', models.CharField(blank=True, max_length=255, null=True)),
                ('createdAt', models.DateTimeField(auto_now_add=True)),
                ('lastViewedAt', models.DateTimeField(auto_now=True)),
                ('courseId', models.CharField(max_length=50, unique=True)),
            ],
            options={
                'db_table': 'video',
            },
        ),
    ]