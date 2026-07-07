import requests
import sounddevice as sd
import soundfile as sf
import io

TEXT = "こんにちは。VOICEVOXのテストです。"
SPEAKER_ID = 3  # ずんだもん

# ① 音声クエリ生成
query = requests.post(
    "http://127.0.0.1:50021/audio_query",
    params={"text": TEXT, "speaker": SPEAKER_ID}
).json()

# ② 音声合成
response = requests.post(
    "http://127.0.0.1:50021/synthesis",
    params={"speaker": SPEAKER_ID},
    json=query
)

# ③ 再生
wav_io = io.BytesIO(response.content)
data, samplerate = sf.read(wav_io)
sd.play(data, samplerate)
sd.wait()

