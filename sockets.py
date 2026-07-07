# import time  # 時間計測機能: 一時無効化

from flask import request
from flask_socketio import emit

from emotion import va_to_param_dict
from extensions import socketio
from llm_chat import stream_chat_response
from storage import save_emotion_row
# from timing import print_timing_table, save_timing_row  # 時間計測機能: 一時無効化
from voice_recorder import discard_voice_recorder, get_voice_recorder
from voice_synth import speak_voicevox


@socketio.on("voice_start")
def handle_voice_start():
    recorder = get_voice_recorder(request.sid)
    ok, err = recorder.start()
    if not ok:
        emit("voice_error", {"message": err})
        return
    emit("voice_status", {"status": "recording"})


@socketio.on("voice_stop")
def handle_voice_stop():
    sid = request.sid
    recorder = get_voice_recorder(sid)

    def process_stop() -> None:
        socketio.emit("voice_status", {"status": "processing"}, to=sid)
        text, err = recorder.stop_and_transcribe()
        if err:
            socketio.emit("voice_error", {"message": err}, to=sid)
        else:
            socketio.emit("voice_transcript", {"text": text}, to=sid)
        socketio.emit("voice_status", {"status": "idle"}, to=sid)

    socketio.start_background_task(process_stop)


@socketio.on("disconnect")
def handle_disconnect():
    discard_voice_recorder(request.sid)


def _play_segments_sequentially(segments, sid):
    """セグメントを順に再生する。

    先頭セグメントの表情は LLM ストリーミング時に既に emit 済みなのでスキップし、
    2 つ目以降は音声再生の直前に emit して同期させる。
    """
    for index, seg in enumerate(segments):
        if index > 0:
            emotion = seg.get("emotion") or {}
            v_val = emotion.get("v")
            a_val = emotion.get("a")
            if v_val is not None and a_val is not None:
                socketio.emit("update_expression", va_to_param_dict(v_val, a_val), to=sid)
        text = seg.get("text", "")
        if text:
            speak_voicevox(text, sid)


@socketio.on("user_message")
def handle_message(data):
    """ユーザーのメッセージを LLM に投げ、ストリームをそのままクライアントへ流す"""
    messages = data["messages"]
    last_emotion = data.get("last_emotion")

    print("--- 受信データ確認 ---")
    print(f"last_emotion in data: {'last_emotion' in data}")
    if "last_emotion" in data:
        print(f"last_emotion value: {last_emotion}")
        print(f"last_emotion type: {type(last_emotion)}")
    print("--- 受信データ確認終了 ---")

    segments = []
    # --- 時間計測機能: 一時無効化 ---
    # timing_info = None
    # start_time = time.time()
    try:
        for kind, payload in stream_chat_response(messages, last_emotion):
            if kind == "stream":
                emit("bot_stream", payload)
            elif kind == "expression":
                emit("update_expression", payload)
            elif kind == "end":
                segments = payload.get("segments", [])
                emit("bot_stream_end", payload)
            # elif kind == "timing":
            #     timing_info = payload

        if segments:
            socketio.start_background_task(_play_segments_sequentially, segments, request.sid)

        # --- 時間計測結果の出力・CSV保存: 一時無効化 ---
        # if timing_info is not None:
        #     total_time = time.time() - start_time
        #     print_timing_table(
        #         total_time,
        #         timing_info["llm_time"],
        #         timing_info["param_time"],
        #         timing_info["prompt_tokens"],
        #         timing_info["completion_tokens"],
        #     )
        #     save_timing_row(
        #         request.sid,
        #         total_time,
        #         timing_info["llm_time"],
        #         timing_info["param_time"],
        #     )
    except Exception as e:
        print(f"エラーが発生しました: {e}")


@socketio.on("save_data")
def handle_save_data(data):
    print("--- CSV保存リクエスト受信 ---")
    print(data)
    try:
        message = save_emotion_row(data)
        print(f"--- {message} ---")
        emit("save_success", {"message": "データは正常に保存されました。"})
    except Exception as e:
        print(f"--- CSV保存エラー: {e} ---")
        emit("save_error", {"message": str(e)})


@socketio.on("manual_update_expression")
def handle_manual_update(data):
    """ブラウザコンソールからの手動表情更新"""
    try:
        v_val = float(data["v"])
        a_val = float(data["a"])
        print(f"--- 手動更新: V={v_val}, A={a_val} ---")
        emit("update_expression", va_to_param_dict(v_val, a_val))
        print("--- 表情パラメータを送信 (手動) ---")
    except (ValueError, KeyError) as e:
        print(f"--- 手動更新エラー: 無効なデータ {data} - {e} ---")
