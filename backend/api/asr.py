import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from faster_whisper import WhisperModel

_MODEL: WhisperModel | None = None


def _get_model() -> WhisperModel:
    global _MODEL
    if _MODEL is None:
        model_name = os.getenv("WHISPER_MODEL", "base")
        _MODEL = WhisperModel(
            model_name,
            device=os.getenv("WHISPER_DEVICE", "cpu"),
            compute_type=os.getenv("WHISPER_COMPUTE_TYPE", "int8"),
        )
    return _MODEL


def _ffmpeg_to_wav_16k_mono(src: Path, dst: Path) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-i",
        str(src),
        "-ac",
        "1",
        "-ar",
        "16000",
        "-f",
        "wav",
        str(dst),
    ]
    subprocess.run(cmd, check=True)


@dataclass(frozen=True)
class TranscribeResult:
    text: str
    language: str
    segments: list[dict[str, Any]]


def transcribe_upload_file(upload_path: Path) -> TranscribeResult:
    model = _get_model()
    with tempfile.TemporaryDirectory(prefix="asr_") as tmpdir:
        tmpdir_p = Path(tmpdir)
        wav_path = tmpdir_p / "audio.wav"
        _ffmpeg_to_wav_16k_mono(upload_path, wav_path)

        segments_iter, info = model.transcribe(
            str(wav_path),
            vad_filter=True,
        )

        segs: list[dict[str, Any]] = []
        text_parts: list[str] = []
        for s in segments_iter:
            segs.append(
                {
                    "start": float(s.start),
                    "end": float(s.end),
                    "text": s.text,
                }
            )
            text_parts.append(s.text)

        return TranscribeResult(
            text=("".join(text_parts)).strip(),
            language=(info.language or "").strip(),
            segments=segs,
        )

