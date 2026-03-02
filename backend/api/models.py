import uuid

from django.db import models


class Transcription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    audio_original_name = models.CharField(max_length=255, blank=True)

    language = models.CharField(max_length=32, blank=True)
    text = models.TextField(blank=True)
    segments = models.JSONField(default=list, blank=True)

    confirmed_text = models.TextField(blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.id} ({self.created_at:%Y-%m-%d %H:%M:%S})"

