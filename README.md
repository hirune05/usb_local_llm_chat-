# USBポータブル ローカルLLM会話システム

[conversation_express_system](https://github.com/hirune05/conversation_express_system) をフォークし、
**USBメモリを挿してダブルクリックするだけで動く**ようにポータブル化したローカルLLM会話システムです。

ユーザーの発話に対して、AI が **音声認識 → 感情を推定 → 表情アニメーション + 音声合成** をリアルタイムに返します。
LLM・音声認識・音声合成のすべてがUSB内で完結し、**インストール不要・完全オフライン**で動作します。

## 主な機能

- **テキスト/音声入力での会話**（音声は `faster-whisper` で文字起こし）
- **ローカル LLM による応答生成**（Ollama / gemma4:e2b-it-qat）
- **感情に応じた表情アニメーション**（Valence-Arousal モデルでパラメータ補間）
- **VOICEVOX ENGINE による音声合成**（ずんだもん）＋口パク同期
- **会話・感情ログの CSV 保存**

## システム構成

<img width="4216" height="1879" alt="archi" src="https://github.com/user-attachments/assets/a5d028c4-0e88-4ac6-84c0-9a3b7dfc8d0e" />

USB版では、上記の Ollama / VOICEVOX ENGINE / アプリ本体（PyInstaller製exe）/ 各モデルを
すべてUSB内に同梱し、`start_mac.command` が一括起動します。

## 使い方（USB版）

対象: Apple Silicon の Mac。環境構築は一切不要です。

1. USB を挿す
2. USB 内の `start_mac.command` を**右クリック → 「開く」**（初回のみ。2回目以降はダブルクリックでOK）
3. ターミナルに起動チェックが並び、すべて ✅ になるとブラウザが自動で開く
   （初回はモデル読み込みに1〜2分かかります）
4. チャット欄に文字を打つか、マイクボタンで話しかける
   - マイクボタン初回クリック時に「**"ターミナル"がマイクにアクセスを求めています**」と出たら**許可**を押す
5. 終了するときはターミナルのウィンドウを閉じる（か Ctrl+C）。全プロセスが自動で停止します

うまく動かないときは、USB内 `app_data/logs/` の3つのログ（`ollama.log` / `voicevox.log` / `app.log`）に
原因が記録されています。

## USBの作り方

このリポジトリのコードから USB 一式をゼロから組み立てる手順は **[BUILD.md](BUILD.md)** を参照してください。
（VOICEVOX ENGINE・Ollama・各モデルの入手方法、PyInstaller ビルド、USBフォーマットまでの完全な手順書）

## 開発モード（USBを使わずに実行）

コードを変更・デバッグするときは、従来どおりローカル環境で実行できます。

### 必要な環境

| コンポーネント | 備考 |
| --- | --- |
| **macOS** | 動作確認済み環境（他 OS は未検証） |
| **Python 3.10+** | |
| **VOICEVOX** | デスクトップアプリでも [ENGINE単体版](https://github.com/VOICEVOX/voicevox_engine) でも可。`127.0.0.1:50021` で待ち受け |
| **Ollama** | `brew install ollama` |
| **`gemma4:e2b-it-qat` モデル** | 約 4 GB のダウンロード |
| **マイク** | 音声入力を使う場合のみ。macOS のプライバシー設定で許可が必要 |

### 手順

```bash
# 1. VOICEVOX を起動しておく（アプリ起動 or ENGINE の ./run）

# 2. Ollama サーバとモデル
brew install ollama
ollama serve          # 別ターミナルで開いたままにする
ollama pull gemma4:e2b-it-qat

# 3. Python 環境
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 4. 起動
.venv/bin/python app.py
```

ブラウザで [http://127.0.0.1:5001](http://127.0.0.1:5001) を開きます
（ポート 5000 は macOS の AirPlay Receiver が使うため 5001 を既定にしています。`APP_PORT` 環境変数で変更可）。

## 設定のカスタマイズ

主な設定は `config.py` に集約されています：

| 設定 | デフォルト | 説明 |
| --- | --- | --- |
| `LLM_MODEL` | `gemma4:e2b-it-qat` | Ollama で使うモデル名 |
| `WHISPER_MODEL_SIZE` | `small` | faster-whisper のモデルサイズ（`WHISPER_MODEL_PATH` 未設定時に使用） |
| `VOICEVOX_URL` | `http://127.0.0.1:50021` | VOICEVOX エンジンの URL |
| `VOICEVOX_SPEAKER_ID` | `3` | 話者 ID（3 = ずんだもん） |

環境変数（USB版のランチャーが設定します）:

| 環境変数 | 役割 |
| --- | --- |
| `APP_PORT` | アプリのポート（既定 5001） |
| `WHISPER_MODEL_PATH` | Whisper モデルのローカルパス（オフライン起動用） |
| `OLLAMA_MODELS` | Ollama のモデル置き場（USB側に向ける） |

## ファイル構成

```
.
├── app.py               # Flask + Socket.IO エントリーポイント
├── app.spec             # PyInstaller ビルド設定（USB用 exe のレシピ）
├── start_mac.command    # USB用ランチャー（3サービスの起動・監視・後始末）
├── BUILD.md             # USB一式をゼロから作る手順書
├── config.py            # 全体設定
├── llm_chat.py          # Ollama 連携・JSON ストリームのパース
├── voice_synth.py       # VOICEVOX 連携・口パク同期
├── voice_recorder.py    # 音声録音・faster-whisper 連携
├── sockets.py           # Socket.IO イベントハンドラ
├── emotion.py           # V/A 座標 → 表情パラメータ補間
├── storage.py           # CSV ログ保存
├── extensions.py        # Socket.IO シングルトン
├── index.html           # フロントエンド本体
├── static/              # フロントエンド資材（JS/CSS）
│   └── vendor/          # p5.js / socket.io.js の同梱コピー（オフライン動作用）
└── requirements.txt
```

## トラブルシューティング

USB版特有のハマりどころ（起動しない・他のMacで動かない等）は **[BUILD.md](BUILD.md) の「ハマりどころ」表**にまとめています。

### 開発モードで Whisper モデルのダウンロードが走る

`WHISPER_MODEL_PATH` 未設定時の初回のみ、faster-whisper のモデル（数百 MB）が
`~/.cache/huggingface/` に自動ダウンロードされます。正常な挙動です。

### マイクが反応しない / 録音できない

macOS の **システム設定 → プライバシーとセキュリティ → マイク** で、
ターミナル（または iTerm / VS Code 等の親プロセス）にアクセス許可を与えてください。

### VOICEVOX 音声が出ない

- エンジンが起動しているか（`curl http://127.0.0.1:50021/version` で確認）
- システムの出力デバイスがミュートになっていないか

### Ollama 接続エラー

- `ollama serve` が起動しているか（`curl http://127.0.0.1:11434/api/tags` で確認）
- `ollama list` に `gemma4:e2b-it-qat` が含まれるか

### `pip install` で `sounddevice` のインストールに失敗する

macOS では PortAudio が必要です：

```bash
brew install portaudio
pip install --force-reinstall sounddevice
```

## ライセンス

MIT
