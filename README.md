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

## USBの中身を更新する

作成済みの USB に、コードの修正や別モデルを反映させたいときの手順です。
以下では USB を `/Volumes/USB_LLM_CHAT` として説明します。

```bash
USB=/Volumes/USB_LLM_CHAT
```

USB さえ更新すれば動きます。手元の作業ミラー（`~/dev/usb_local_llm_chat_bundle/`）も
最新に保ちたい場合は、同じコピー操作をそちらにも行ってください。

### 何を変えたら何が必要か

| 変えたもの | 再ビルド | USBへの反映方法 |
| --- | --- | --- |
| Python コード（`app.py`, `llm_chat.py`, `config.py` など） | **必要** | exe を再ビルドして差し替え |
| フロントエンド（`index.html`, `static/`） | 不要 | ファイルをコピーするだけ |
| `start_mac.command`（ランチャー） | 不要 | ファイルをコピーするだけ |
| LLM モデルの入れ替え | **必要**（`config.py` を書き換えるため） | モデルを pull + exe 差し替え |
| Whisper モデルのサイズ変更 | 不要 | モデルを差し替え、ランチャーのパスを変更 |

`--onedir` ビルドなので、`index.html` と `static/` は exe の中ではなく
`app/conversation_app/_internal/` に**生のファイルとして置かれます**。Flask は起動時にそこから読むため、
フロントエンドだけの修正なら再ビルドせずファイルを置き換えるだけで反映されます。
逆に、USB 直下や `app/` 直下を探しても見つかりません（**編集すべきは `_internal/` の中**）。

### 1. Python コードを修正した場合

```bash
cd <このリポジトリ>
.venv/bin/pyinstaller app.spec --noconfirm            # exe を作り直す（BUILD.md「5. アプリ本体」と同じ）
rsync -a --delete dist/conversation_app/ "$USB/app/conversation_app/"
```

### 2. フロントエンド（HTML/CSS/JS）だけ修正した場合

再ビルド不要。`_internal/` に上書きコピーするだけです。

```bash
cd <このリポジトリ>
rsync -a index.html static "$USB/app/conversation_app/_internal/"
```

（`static` に末尾スラッシュを付けないこと。付けると中身だけが `_internal/` 直下に散らばります）

ランチャーだけを直した場合も、ビルド不要でコピーのみ：

```bash
cp start_mac.command "$USB/" && chmod +x "$USB/start_mac.command"
```

### 3. LLM モデルを別のものに変えたい場合

例として `qwen3:4b` に変える場合：

```bash
# (1) 新しいモデルを USB のモデル置き場に直接 pull する
OLLAMA_MODELS="$USB/ollama_models" "$USB/bin/ollama_runtime/ollama" serve &
OLLAMA_MODELS="$USB/ollama_models" "$USB/bin/ollama_runtime/ollama" pull qwen3:4b

# (2) 不要になった旧モデルを削除して容量を空ける（任意）
OLLAMA_MODELS="$USB/ollama_models" "$USB/bin/ollama_runtime/ollama" rm gemma4:e2b-it-qat
kill %1   # serve を止める
```

そのうえで `config.py` の `LLM_MODEL` を `"qwen3:4b"` に書き換え、
上の「1. Python コードを修正した場合」の手順で exe を再ビルドして反映します。

> **注意**: モデルは JSON 形式（`format="json"`）で感情つきの応答を返す必要があります。
> 小さすぎるモデルだと `llm_chat.py` のスキーマ通りに出力できず、表情が動かないことがあります。
> 新しいモデルに変えたら、必ず一度チャットして表情と音声が動くか確認してください。

### 4. Whisper（音声認識）モデルを変えたい場合

再ビルドは不要です。モデルを差し替えて、ランチャーが指すパスを合わせるだけです。

モデルの取得とコピーは [BUILD.md](BUILD.md) の「4. Whisper モデル」と同じ手順で、
モデル名と行き先だけ差し替えます（例: `Systran/faster-whisper-medium` → `$USB/models/whisper-medium/`）。

そのうえで `start_mac.command` の以下の行を書き換えてコピーします：

```bash
export WHISPER_MODEL_PATH="$SCRIPT_DIR/models/whisper-medium"
```

（`WHISPER_MODEL_PATH` は環境変数なので exe を作り直さずに切り替わります）

### 5. 更新後の確認

USB から `start_mac.command` を起動し、以下を確認してください：

- 3サービスすべてが ✅ になる
- チャットを1回送って、返答・表情・音声が返る
- 問題があれば `app_data/logs/` の3ファイルを見る（ログは追記式なので過去の起動も残っています）

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
