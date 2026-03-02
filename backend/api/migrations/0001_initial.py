from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Transcription",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("audio_original_name", models.CharField(max_length=255, blank=True)),
                ("language", models.CharField(max_length=32, blank=True)),
                ("text", models.TextField(blank=True)),
                ("segments", models.JSONField(default=list, blank=True)),
                ("confirmed_text", models.TextField(blank=True)),
                ("confirmed_at", models.DateTimeField(null=True, blank=True)),
            ],
        ),
    ]

