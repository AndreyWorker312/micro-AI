## ASR demo: микрофон → Django → Whisper → текст

Минимальное клиент‑серверное приложение:

- **Клиент (браузер)**: записывает аудио с микрофона (MediaRecorder), отправляет на сервер, показывает транскрипт, даёт отредактировать и подтвердить.
- **Сервер (Django)**: принимает файл, конвертирует через `ffmpeg`, транскрибирует через `faster-whisper` (бесплатно, CPU), отдаёт JSON.

### Запуск

Требуется установленный Docker и `docker-compose`.

```bash
docker-compose up --build
```

Открыть в браузере:

- `http://localhost:8080`

### Эндпоинты

- `GET /api/healthz/`
- `POST /api/transcribe/` (multipart/form-data, поле `audio`)
- `POST /api/confirm/` (JSON: `{ "id": "<uuid>", "text": "..." }`)

### Примечания

- Модель Whisper задаётся через `WHISPER_MODEL` в `docker-compose.yml` (по умолчанию `base`).
- Первый запуск может быть долгим: модель скачивается в volume `whisper_models`.

