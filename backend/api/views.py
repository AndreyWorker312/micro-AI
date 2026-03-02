import json
import re
import tempfile
from pathlib import Path

from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .asr import transcribe_upload_file
from .models import Transcription


def _normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


@require_GET
def healthz(_: HttpRequest) -> JsonResponse:
    return JsonResponse({"ok": True})


@csrf_exempt
@require_POST
def transcribe(request: HttpRequest) -> JsonResponse:
    if "audio" not in request.FILES:
        return JsonResponse({"ok": False, "error": "No file field 'audio'."}, status=400)

    f = request.FILES["audio"]
    if f.size and f.size > 25 * 1024 * 1024:
        return JsonResponse({"ok": False, "error": "File too large (limit 25MB)."}, status=413)

    suffix = Path(f.name).suffix or ".bin"
    with tempfile.NamedTemporaryFile(prefix="upload_", suffix=suffix, delete=False) as tmp:
        for chunk in f.chunks():
            tmp.write(chunk)
        upload_path = Path(tmp.name)

    try:
        result = transcribe_upload_file(upload_path)
    except Exception as e:
        return JsonResponse({"ok": False, "error": f"Transcription failed: {type(e).__name__}: {e}"}, status=500)
    finally:
        try:
            upload_path.unlink(missing_ok=True)
        except Exception:
            pass

    obj = Transcription.objects.create(
        audio_original_name=f.name or "",
        language=result.language,
        text=result.text,
        segments=result.segments,
    )

    warnings: list[str] = []
    if not result.text:
        warnings.append("Empty transcript. Try speaking louder / closer to mic.")

    return JsonResponse(
        {
            "ok": True,
            "id": str(obj.id),
            "language": result.language,
            "text": result.text,
            "segments": result.segments,
            "warnings": warnings,
        }
    )


@csrf_exempt
@require_POST
def confirm(request: HttpRequest) -> JsonResponse:
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return JsonResponse({"ok": False, "error": "Invalid JSON."}, status=400)

    tid = payload.get("id", "")
    text = payload.get("text", "")
    if not isinstance(text, str):
        return JsonResponse({"ok": False, "error": "Field 'text' must be string."}, status=400)

    normalized = _normalize_text(text)
    if not normalized:
        return JsonResponse({"ok": False, "error": "Text is empty after normalization."}, status=400)

    if tid:
        try:
            obj = Transcription.objects.get(id=tid)
            obj.confirmed_text = normalized
            obj.confirmed_at = timezone.now()
            obj.save(update_fields=["confirmed_text", "confirmed_at"])
        except Transcription.DoesNotExist:
            pass

    return JsonResponse({"ok": True, "text": normalized})

