# リアルタイム感情表現システム

ローカル LLM とキャラクター表情・音声を組み合わせた、対話型の感情表現システムです。
ユーザーの発話に対して、AI が **音声認識 → 感情を推定 → 表情アニメーション + 音声合成** をリアルタイムに返します。すべてローカルで動作し、オフラインで使用できます。

## 主な機能

- **テキスト/音声入力での会話**（音声は `faster-whisper` で文字起こし）
- **ローカル LLM による応答生成**（Ollama / gemma4:e2b）
- **感情に応じた表情アニメーション**（Valence-Arousal モデルでパラメータ補間）
- **VOICEVOX による音声合成**（ずんだもん）
- **会話・感情ログの CSV 保存**

## システム構成

<img width="4216" height="1879" alt="archi" src="https://github.com/user-attachments/assets/a5d028c4-0e88-4ac6-84c0-9a3b7dfc8d0e" />

## クイックスタート

### 方法1. Skills を用いた対話型セットアップと実行 (⭐️推奨)

> [!TIP]
> Claude Code を使用している場合は、以下コマンドで対話的にセットアップを実行できます。
>
> `/setup`

### 方法2. 手動セットアップ

#### 必要な環境（自動セットアップでサポートします）

| コンポーネント          | バージョン / 備考                                            |
| ----------------------- | ------------------------------------------------------------ |
| **macOS**               | 動作確認済み環境（他 OS は未検証）                           |
| **Python**              | 3.10 以上推奨                                                |
| **VOICEVOX**            | デスクトップアプリ。エンジンが `127.0.0.1:50021` で待ち受け  |
| **Ollama**              | ローカル LLM ランタイム                                      |
| **`gemma4:e2b` モデル** | 約 1.5 GB のダウンロード                                     |
| **マイク**              | 音声入力を使う場合のみ。macOS のプライバシー設定で許可が必要 |

#### 1. VOICEVOX を起動

[VOICEVOX 公式サイト](https://voicevox.hiroshiba.jp/) からアプリをダウンロードして起動。エンジンが `http://127.0.0.1:50021` で立ち上がります。

#### 2. Ollama のインストールとモデル取得

```bash
brew install ollama

# 別ターミナルでサーバを起動（開いたままにする）
ollama serve

# モデルを取得（数 GB のダウンロード）
ollama pull gemma4:e2b
```

#### 3. Python 仮想環境と依存パッケージ

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### 4. 起動

```bash
python app.py
```

ブラウザで [http://127.0.0.1:5000](http://127.0.0.1:5000) を開きます。

## 使い方

- **テキスト入力**: チャット欄にメッセージを入力 → 感情に応じた表情と音声で返答
- **音声入力**: マイクボタンを押して話しかけると `faster-whisper` で文字起こしされ、そのまま LLM へ送られます
- 会話ごとに `conversation_data.csv` と `emotion_data.csv` にログが追記されます

## 設定のカスタマイズ

主な設定は `config.py` に集約されています：

| 設定                  | デフォルト               | 説明                                                                            |
| --------------------- | ------------------------ | ------------------------------------------------------------------------------- |
| `LLM_MODEL`           | `gemma4:e2b`             | Ollama で使うモデル名                                                           |
| `WHISPER_MODEL_SIZE`  | `small`                  | faster-whisper のモデルサイズ（`tiny` / `base` / `small` / `medium` / `large`） |
| `VOICEVOX_URL`        | `http://127.0.0.1:50021` | VOICEVOX エンジンの URL                                                         |
| `VOICEVOX_SPEAKER_ID` | `3`                      | 話者 ID（3 = ずんだもん）                                                       |

別のモデルに切り替える場合は `LLM_MODEL` を変更し、`ollama pull <モデル名>` を実行してください。

## ファイル構成

```
.
├── app.py              # Flask + Socket.IO エントリーポイント
├── config.py           # 全体設定
├── llm_chat.py         # Ollama 連携・JSON ストリームのパース
├── voice_synth.py     # VOICEVOX 連携・口パク同期
├── voice_recorder.py   # 音声録音・faster-whisper 連携
├── sockets.py          # Socket.IO イベントハンドラ
├── emotion.py          # V/A 座標 → 表情パラメータ補間
├── storage.py          # CSV ログ保存
├── extensions.py       # Socket.IO シングルトン
├── index.html          # フロントエンド本体
├── static/             # フロントエンド資材（JS/CSS/画像）
├── requirements.txt
└── .claude/skills/setup/SKILL.md  # 対話型セットアップ用 Skill
```

## トラブルシューティング

### `python app.py` 起動時に Whisper モデルのダウンロードが走る

初回のみ `faster-whisper` のモデル（数百 MB）が `~/.cache/huggingface/` にダウンロードされます。少し時間がかかりますが正常です。

### マイクが反応しない / 録音できない

macOS の **システム設定 → プライバシーとセキュリティ → マイク** で、ターミナル（または iTerm / VS Code 等の親プロセス）にアクセス許可を与えてください。

### VOICEVOX 音声が出ない

- VOICEVOX アプリが起動しているか（`curl http://127.0.0.1:50021/version` で確認）
- システムの出力デバイスがミュートになっていないか
- ポート `50021` が他のプロセスと競合していないか

### Ollama 接続エラー

- `ollama serve` が起動しているか（`curl http://127.0.0.1:11434/api/tags` で確認）
- `ollama list` に `gemma4:e2b` が含まれるか

### `pip install` で `sounddevice` のインストールに失敗する

macOS では PortAudio が必要です：

```bash
brew install portaudio
pip install --force-reinstall sounddevice
```

## ライセンス

MIT
