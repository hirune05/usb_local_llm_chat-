import threading
import time

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

from config import CHANNELS, SAMPLE_RATE, WHISPER_MODEL_SIZE

# Whisper モデルは全セッションで共有（ロード重いので 1 回だけ）
_whisper_model: WhisperModel | None = None
_whisper_lock = threading.Lock()


def _get_whisper_model() -> WhisperModel:
    global _whisper_model
    with _whisper_lock:
        if _whisper_model is None:
            _whisper_model = WhisperModel(WHISPER_MODEL_SIZE)
        return _whisper_model


def warmup():
    """Whisper モデルを事前ロードする。"""
    print(f"--- Whisperモデル {WHISPER_MODEL_SIZE} のウォームアップ中... ---")
    _get_whisper_model()
    print("--- Whisperウォームアップ完了 ---")


class VoiceRecorder:
    def __init__(self) -> None:
        self.is_recording = False
        self.stop_event = threading.Event()
        self.record_thread: threading.Thread | None = None
        self.chunks: list[np.ndarray] = []
        self.record_error: str | None = None
        self.state_lock = threading.Lock()

    def start(self) -> tuple[bool, str | None]:
        with self.state_lock:
            if self.is_recording:
                return False, "already recording"
            self.is_recording = True
            self.stop_event.clear()
            self.chunks = []
            self.record_error = None
            self.record_thread = threading.Thread(target=self._record_loop, daemon=True)
            self.record_thread.start()
            return True, None

    def stop_and_transcribe(self) -> tuple[str | None, str | None]:
        with self.state_lock:
            if not self.is_recording:
                return None, "not recording"
            self.is_recording = False
            self.stop_event.set()

        if self.record_thread:
            self.record_thread.join(timeout=5)

        if self.record_error:
            return None, self.record_error

        audio = self._assemble_audio()
        if audio is None:
            return None, "no audio captured"

        try:
            model = _get_whisper_model()
            segments, _info = model.transcribe(audio)
            text = "".join(segment.text for segment in segments).strip()
            if not text:
                text = "no speech detected"
            return text, None
        except Exception as exc:
            return None, f"transcribe error: {exc}"

    def _record_loop(self) -> None:
        def callback(indata, _frames, _time, status) -> None:
            if status:
                pass
            self.chunks.append(indata.copy())

        try:
            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype="float32",
                callback=callback,
            ):
                while not self.stop_event.is_set():
                    time.sleep(0.05)
        except Exception as exc:
            self.record_error = f"record error: {exc}"
            self.stop_event.set()

    def _assemble_audio(self) -> np.ndarray | None:
        if not self.chunks:
            return None
        audio = np.concatenate(self.chunks, axis=0)
        return np.squeeze(audio)


_recorders: dict[str, VoiceRecorder] = {}


def get_voice_recorder(sid: str) -> VoiceRecorder:
    recorder = _recorders.get(sid)
    if recorder is None:
        recorder = VoiceRecorder()
        _recorders[sid] = recorder
    return recorder


def discard_voice_recorder(sid: str) -> None:
    _recorders.pop(sid, None)
