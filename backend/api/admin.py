from django.contrib import admin

from .models import Transcription


@admin.register(Transcription)
class TranscriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "audio_original_name", "language")
    readonly_fields = ("created_at",)

