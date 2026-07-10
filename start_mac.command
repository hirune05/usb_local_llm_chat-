#!/bin/bash
# ==========================================================================
# USB portable launcher (macOS)
# 挿したUSB上のバンドル一式を、Ollama + VOICEVOX ENGINE + Flask アプリの順に起動する。
# スクリプトを右クリック→「開く」でGatekeeperを通し、以降はダブルクリックで起動可。
# ==========================================================================
set -u

# --- 場所解決（USBがどこにマウントされても動くように、スクリプトの場所を基点にする） ------
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

OLLAMA_BIN="$SCRIPT_DIR/bin/ollama_runtime/ollama"
VOICEVOX_BIN="$SCRIPT_DIR/bin/macos-arm64/run"
APP_BIN="$SCRIPT_DIR/app/conversation_app/conversation_app"

APP_PORT="${APP_PORT:-5001}"
OLLAMA_PORT=11434
VOICEVOX_PORT=50021

# 実行ログ（バンドル内に落として持ち出しを容易に）
LOG_DIR="$SCRIPT_DIR/app_data/logs"
mkdir -p "$LOG_DIR"
OLLAMA_LOG="$LOG_DIR/ollama.log"
VOICEVOX_LOG="$LOG_DIR/voicevox.log"
APP_LOG="$LOG_DIR/app.log"

# ログは追記式（>>）。上書きすると「他のPCで失敗した時の証拠」が次の起動で消えるため。
# 起動ごとの区切りが分かるようセッションヘッダを書いておく。
SESSION_STAMP="$(date '+%Y-%m-%d %H:%M:%S') on $(hostname)"
for log_file in "$OLLAMA_LOG" "$VOICEVOX_LOG" "$APP_LOG"; do
  echo "===== session start: $SESSION_STAMP =====" >> "$log_file"
done

# bash の job control を明示 ON にして、後段の `&` 起動サービスがそれぞれ独立した
# プロセスグループに配置されるようにする（非対話 shell はデフォルト OFF）。
# こうすると `kill -TERM -$PID` で子孫まとめて落とせる。VOICEVOX の `./run` は
# 内部で uvicorn ワーカを spawn するため PID 単発killでは残る。
set -m

# --- 子プロセスの掃除 -----------------------------------------------------
OLLAMA_PID=""
VOICEVOX_PID=""
APP_PID=""

kill_group() {
  local pid="$1" sig="$2"
  [ -z "$pid" ] && return 0
  kill "$sig" "-$pid" 2>/dev/null || kill "$sig" "$pid" 2>/dev/null || true
}

cleanup() {
  echo ""
  echo "🧹  終了処理: 子プロセスを停止します..."
  local pids=("$APP_PID" "$VOICEVOX_PID" "$OLLAMA_PID")
  for pid in "${pids[@]}"; do kill_group "$pid" -TERM; done
  # 猶予後にSIGKILL
  sleep 2
  for pid in "${pids[@]}"; do kill_group "$pid" -KILL; done
  echo "👋  終了しました"
}
trap cleanup EXIT INT TERM

# --- ポート衝突の早期検出 -----------------------------------------------
port_in_use() {
  lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
}

for port_pair in "$OLLAMA_PORT:Ollama" "$VOICEVOX_PORT:VOICEVOX" "$APP_PORT:アプリ"; do
  port="${port_pair%%:*}"
  label="${port_pair##*:}"
  if port_in_use "$port"; then
    echo "❌  ポート $port ($label) が既に使われています。"
    echo "    既存の Ollama/VOICEVOX/アプリを終了してから再度お試しください。"
    echo "    （macOSの AirPlay Receiver が 5000 番を占有します — その場合は APP_PORT を変えてください）"
    read -n 1 -s -r -p "何かキーを押して終了..."
    exit 1
  fi
done

# --- サービス起動待ちヘルパー -----------------------------------------------
# USB からの読み込みは内蔵SSDより遅いので、gemma4 (4GB) の初回ロードには数分要する。
# 呼び出し側で個別に秒数を指定できるようにし、アプリだけ長めに待つ。
wait_for() {
  local url="$1" name="$2" tries="${3:-60}"
  echo -n "⏳  $name の起動を待機中"
  for ((i=1; i<=tries; i++)); do
    if curl -s -o /dev/null -m 1 "$url"; then
      echo " ✅"
      return 0
    fi
    echo -n "."
    sleep 1
  done
  echo " ❌"
  echo "    $name が $tries 秒以内に応答しませんでした。$LOG_DIR のログを確認してください。"
  return 1
}

# --- 1. Ollama と VOICEVOX を起動 --------------------------------------
# 両者は互いに独立しているので、先に2つとも起動してから待つ。
# 逐次に待つと、USB読み込みで数十秒かかる2つのサービスのロード時間が直列に積み上がる。
echo "🚀  Ollama を起動します..."
export OLLAMA_MODELS="$SCRIPT_DIR/ollama_models"
"$OLLAMA_BIN" serve >> "$OLLAMA_LOG" 2>&1 &
OLLAMA_PID=$!

echo "🚀  VOICEVOX ENGINE を起動します..."
(cd "$SCRIPT_DIR/bin/macos-arm64" && ./run --host 127.0.0.1 --port "$VOICEVOX_PORT") >> "$VOICEVOX_LOG" 2>&1 &
VOICEVOX_PID=$!

wait_for "http://127.0.0.1:$OLLAMA_PORT/api/tags" "Ollama" || exit 1
wait_for "http://127.0.0.1:$VOICEVOX_PORT/version" "VOICEVOX ENGINE" || exit 1

# --- 2. Flask アプリ起動 -----------------------------------------------
# （アプリは Ollama と VOICEVOX の両方に依存するので、ここまで待ってから起動する）
echo "🚀  会話アプリを起動します..."
export WHISPER_MODEL_PATH="$SCRIPT_DIR/models/whisper-small"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export APP_PORT
"$APP_BIN" >> "$APP_LOG" 2>&1 &
APP_PID=$!
wait_for "http://127.0.0.1:$APP_PORT/" "会話アプリ" 300 || exit 1

# --- 3. ブラウザで開く -----------------------------------------------
echo ""
echo "🎉  起動完了! ブラウザで http://127.0.0.1:$APP_PORT を開きます"
open "http://127.0.0.1:$APP_PORT/"

echo ""
echo "==============================================================="
echo "  会話するには、ブラウザ画面で操作してください"
echo "  終了するには、このウィンドウを閉じるか Ctrl+C を押してください"
echo "==============================================================="

# アプリが落ちるまで待つ（子プロセスの中で一番外向きの窓口なので）
wait "$APP_PID"
