# LLM
LLM_MODEL = "gemma4:e2b-it-qat"

import os

# Whisper (STT)
WHISPER_MODEL_SIZE = "small"
# USB配布時は WHISPER_MODEL_PATH 環境変数でローカル同梱モデルを指すことでオフライン起動する
WHISPER_MODEL_PATH = os.environ.get("WHISPER_MODEL_PATH")
SAMPLE_RATE = 16000
CHANNELS = 1

# CSV
CSV_FILE_PATH = "emotion_data.csv"
CONVERSATION_CSV_PATH = "conversation_data.csv"
# TIMING_CSV_PATH = "timing_data.csv"  # 時間計測機能: 一時無効化
CSV_HEADERS = [
    "subject_id", "timestamp", "emotion_label", "animationDuration",
    "eyeOpenness", "pupilSize", "pupilAngle",
    "upperEyelidAngle", "upperEyelidCoverage", "lowerEyelidCoverage",
    "mouthCurve", "mouthHeight", "mouthWidth",
]
CONVERSATION_CSV_HEADERS = [
    "session_id", "timestamp", "user_message", "bot_response",
    "emotion_v", "emotion_a", "emotion_label",
]
# TIMING_CSV_HEADERS = [  # 時間計測機能: 一時無効化
#     "timestamp", "session_id",
#     "total_time", "llm_time", "param_time", "other_time",
# ]

# VOICEVOX
VOICEVOX_URL = "http://127.0.0.1:50021"
VOICEVOX_SPEAKER_ID = 3  # ずんだもん

# Flask
SECRET_KEY = "C0HThSwr"
