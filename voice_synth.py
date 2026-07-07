import io
import time

import numpy as np
import requests
import sounddevice as sd
import soundfile as sf

from config import VOICEVOX_SPEAKER_ID, VOICEVOX_URL
from extensions import socketio


def speak_voicevox(text: str, sid: str | None = None) -> None:
    if not text:
        return
    try:
        query = requests.post(
            f"{VOICEVOX_URL}/audio_query",
            params={"text": text, "speaker": VOICEVOX_SPEAKER_ID},
            timeout=10,
        ).json()

        response = requests.post(
            f"{VOICEVOX_URL}/synthesis",
            params={"speaker": VOICEVOX_SPEAKER_ID},
            json=query,
            timeout=30,
        )
        response.raise_for_status()

        wav_io = io.BytesIO(response.content)
        data, samplerate = sf.read(wav_io, dtype="float32")
        audio = np.mean(data, axis=1) if data.ndim > 1 else data

        frame_sec = 0.05
        window_size = max(int(samplerate * frame_sec), 1)
        rms_values = []
        for start in range(0, len(audio), window_size):
            chunk = audio[start:start + window_size]
            if chunk.size == 0:
                continue
            rms = float(np.sqrt(np.mean(np.square(chunk))))
            rms_values.append(rms)

        max_rms = max(rms_values) if rms_values else 0.0
        frame_ms = int(frame_sec * 1000)
        sd.play(data, samplerate)
        start_time = time.time()
        last_openness = -1.0

        for index, rms in enumerate(rms_values):
            norm = rms / max_rms if max_rms > 1e-6 else 0.0
            openness = float(norm * 0.8)
            if abs(openness - last_openness) > 0.02:
                socketio.emit("update_mouth", {"openness": openness, "duration": frame_ms}, to=sid)
                last_openness = openness

            target_time = (index + 1) * frame_sec
            delay = target_time - (time.time() - start_time)
            if delay > 0:
                socketio.sleep(delay)

        sd.wait()
        socketio.emit("update_mouth", {"openness": 0.0, "duration": 120}, to=sid)
    except Exception as exc:
        print(f"VOICEVOX再生エラー: {exc}")
