const els = {
  btnStart: document.getElementById("btnStart"),
  btnStop: document.getElementById("btnStop"),
  btnTranscribe: document.getElementById("btnTranscribe"),
  btnConfirm: document.getElementById("btnConfirm"),
  status: document.getElementById("status"),
  timer: document.getElementById("timer"),
  meterBar: document.getElementById("meterBar"),
  player: document.getElementById("player"),
  text: document.getElementById("text"),
  lang: document.getElementById("lang"),
  tid: document.getElementById("tid"),
  warnings: document.getElementById("warnings"),
};

let mediaRecorder = null;
let chunks = [];
let recordedBlob = null;
let recordStartTs = 0;
let timerHandle = null;
let transcriptionId = "";

function setStatus(s) {
  els.status.textContent = s;
}

function fmtTime(ms) {
  const total = Math.max(0, Math.floor(ms / 1000));
  const m = String(Math.floor(total / 60)).padStart(2, "0");
  const s = String(total % 60).padStart(2, "0");
  return `${m}:${s}`;
}

function startTimer() {
  recordStartTs = Date.now();
  clearInterval(timerHandle);
  timerHandle = setInterval(() => {
    els.timer.textContent = fmtTime(Date.now() - recordStartTs);
  }, 200);
}

function stopTimer() {
  clearInterval(timerHandle);
  timerHandle = null;
}

async function startRecording() {
  els.warnings.textContent = "";
  els.lang.textContent = "—";
  els.tid.textContent = "—";
  transcriptionId = "";

  recordedBlob = null;
  chunks = [];

  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const mr = new MediaRecorder(stream);
  mediaRecorder = mr;

  mr.ondataavailable = (e) => {
    if (e.data && e.data.size > 0) chunks.push(e.data);
  };

  mr.onstop = () => {
    stream.getTracks().forEach((t) => t.stop());
    recordedBlob = new Blob(chunks, { type: mr.mimeType || "audio/webm" });
    els.player.src = URL.createObjectURL(recordedBlob);
    els.btnTranscribe.disabled = false;
    setStatus("Запись готова");
  };

  mr.start(250);
  els.btnStart.disabled = true;
  els.btnStop.disabled = false;
  els.btnTranscribe.disabled = true;
  els.btnConfirm.disabled = true;
  els.text.value = "";
  els.text.disabled = true;
  setStatus("Идёт запись…");
  startTimer();
}

function stopRecording() {
  if (!mediaRecorder) return;
  stopTimer();
  els.btnStop.disabled = true;
  setStatus("Остановка…");
  mediaRecorder.stop();
  mediaRecorder = null;
}

async function transcribe() {
  if (!recordedBlob) return;
  setStatus("Отправка на сервер…");
  els.btnTranscribe.disabled = true;
  els.btnConfirm.disabled = true;
  els.text.disabled = true;
  els.warnings.textContent = "";

  const fd = new FormData();
  fd.append("audio", recordedBlob, "recording.webm");

  const resp = await fetch("/api/transcribe/", { method: "POST", body: fd });
  const data = await resp.json().catch(() => ({}));

  if (!resp.ok || !data.ok) {
    setStatus("Ошибка");
    els.btnTranscribe.disabled = false;
    const msg = data && data.error ? data.error : `HTTP ${resp.status}`;
    els.warnings.textContent = msg;
    return;
  }

  transcriptionId = data.id || "";
  els.tid.textContent = transcriptionId || "—";
  els.lang.textContent = data.language || "—";
  els.text.value = data.text || "";
  els.text.disabled = false;
  els.btnConfirm.disabled = !els.text.value.trim();
  setStatus("Готово");

  const warnings = (data.warnings || []).filter(Boolean);
  els.warnings.textContent = warnings.length ? warnings.join(" ") : "";
}

async function confirmText() {
  const text = els.text.value || "";
  if (!text.trim()) return;
  setStatus("Подтверждение…");
  els.btnConfirm.disabled = true;

  const resp = await fetch("/api/confirm/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: transcriptionId, text }),
  });
  const data = await resp.json().catch(() => ({}));

  if (!resp.ok || !data.ok) {
    setStatus("Ошибка");
    const msg = data && data.error ? data.error : `HTTP ${resp.status}`;
    els.warnings.textContent = msg;
    els.btnConfirm.disabled = false;
    return;
  }

  els.text.value = data.text || text;
  setStatus("Подтверждено");
}

// Simple mic activity meter (optional, best-effort)
async function setupMeter() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const src = ctx.createMediaStreamSource(stream);
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 512;
    src.connect(analyser);

    const buf = new Uint8Array(analyser.frequencyBinCount);
    const tick = () => {
      analyser.getByteTimeDomainData(buf);
      let sum = 0;
      for (let i = 0; i < buf.length; i++) {
        const v = (buf[i] - 128) / 128;
        sum += v * v;
      }
      const rms = Math.sqrt(sum / buf.length);
      const pct = Math.max(0, Math.min(100, Math.round(rms * 200)));
      els.meterBar.style.width = `${pct}%`;
      requestAnimationFrame(tick);
    };
    tick();

    // Keep stream (meter) alive; browser will show mic indicator.
  } catch {
    // Ignore if permissions denied.
  }
}

els.btnStart.addEventListener("click", () => startRecording().catch((e) => (els.warnings.textContent = String(e))));
els.btnStop.addEventListener("click", stopRecording);
els.btnTranscribe.addEventListener("click", () => transcribe().catch((e) => (els.warnings.textContent = String(e))));
els.btnConfirm.addEventListener("click", () => confirmText().catch((e) => (els.warnings.textContent = String(e))));

els.text.addEventListener("input", () => {
  els.btnConfirm.disabled = !(els.text.value || "").trim();
});

setupMeter();

