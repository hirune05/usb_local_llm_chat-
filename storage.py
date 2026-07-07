import csv
import os

from config import CSV_FILE_PATH, CSV_HEADERS


def save_emotion_row(data):
    """フロントエンドから受信した感情データを CSV に追記する。
    成功時はメッセージ文字列を返し、失敗時は例外を送出する。"""
    file_exists = os.path.isfile(CSV_FILE_PATH)
    with open(CSV_FILE_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)
    return f"データが {CSV_FILE_PATH} に保存されました"
