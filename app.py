import logging
import os

from flask import Flask, render_template

import llm_chat
import voice_recorder
from config import SECRET_KEY
from extensions import socketio

DEBUG = True

# Socket.IO の polling リクエストでログが埋まるのを抑制
logging.getLogger("werkzeug").setLevel(logging.ERROR)

# 副作用で @socketio.on(...) ハンドラが登録される
import sockets  # noqa: E402, F401

app = Flask(__name__, static_folder="static", template_folder=".")
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
    print("サーバを http://127.0.0.1:5000 で起動します")
    socketio.run(app, debug=DEBUG, allow_unsafe_werkzeug=True)
