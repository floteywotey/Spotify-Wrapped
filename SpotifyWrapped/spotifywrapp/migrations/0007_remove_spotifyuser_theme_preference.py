# Generated by Django 5.1.2 on 2024-12-01 22:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("spotifywrapp", "0006_spotifyuser_theme_preference"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="spotifyuser",
            name="theme_preference",
        ),
    ]