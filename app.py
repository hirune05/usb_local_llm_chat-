import logging
import multiprocessing
import os
import sys

# PyInstaller frozen 環境では multiprocessing の spawn ワーカーが親バイナリを再実行するため、
# freeze_support() で「ワーカーとして起動された」場合に __main__ を再入させず即 return させる。
# これを入れないと ctranslate2 等が Process() を作った瞬間に自己複製の無限ループになる。
multiprocessing.freeze_support()

# ログファイルへリダイレクトされると stdout はブロックバッファリングになり、print した内容が
# なかなかファイルに現れない。現地でのトラブル調査は app_data/logs/ が唯一の手がかりなので、
# 起動元（USBランチャー / 直接実行）に依存せず常に流れるよう、ここで行バッファリングを指定する。
for _stream in (sys.stdout, sys.stderr):
    if _stream is not None:
        _stream.reconfigure(line_buffering=True)

from flask import Flask, render_template

import llm_chat
import voice_recorder
from config import SECRET_KEY
from extensions import socketio

# PyInstaller で frozen 化された配布バンドルでは reloader/debugger を無効化して単一プロセス起動する
DEBUG = not getattr(sys, "frozen", False)

# Socket.IO の polling リクエストでログが埋まるのを抑制
logging.getLogger("werkzeug").setLevel(logging.ERROR)

# 副作用で @socketio.on(...) ハンドラが登録される
import sockets  # noqa: E402, F401

# PyInstaller で frozen 化された環境では index.html / static/ が sys._MEIPASS 配下に置かれる
_BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))

app = Flask(
    __name__,
    static_folder=os.path.join(_BASE_DIR, "static"),
    template_folder=_BASE_DIR,
)
app.config["SECRET_KEY"] = SECRET_KEY
socketio.init_app(app)


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


def warmup():
    """初回リクエスト時の遅延を避けるため、重いモデルを事前ロードする。
    どちらかが失敗しても起動は続行する。"""
    for name, fn in (("LLM", llm_chat.warmup), ("Whisper", voice_recorder.warmup)):
        try:
            fn()
        except Exception as exc:
            print(f"--- {name}ウォームアップ失敗（無視して続行）: {exc} ---")


if __name__ == "__main__":
    # Flask の reloader 使用時は子プロセス（WERKZEUG_RUN_MAIN=true）だけが実際に serve する。
    # 親プロセスでウォームアップしても無駄なのでスキップ。
    is_reloader_child = os.environ.get("WERKZEUG_RUN_MAIN") == "true"
    if is_reloader_child or not DEBUG:
        warmup()
    # macOS の AirPlay Receiver が 5000 を占有するので、USB配布時は APP_PORT で切り替え可能に
    port = int(os.environ.get("APP_PORT", "5001"))
    print(f"サーバを http://127.0.0.1:{port} で起動します")
    socketio.run(app, host="127.0.0.1", port=port, debug=DEBUG, allow_unsafe_werkzeug=True)
