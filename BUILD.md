# USB ポータブル版のビルド手順（macOS / Apple Silicon）

このリポジトリのコード（レシピ）から、「USBを挿してダブルクリックするだけで動く」
ローカルLLM会話システム（パン）を再現するための完全な手順書。

検証済み環境: macOS 26.5 / Apple Silicon (ARM64) / USB 8GB以上

## 完成形のUSB構成

```
USB_LLM_CHAT/                     ← ボリューム名（任意。APFSフォーマット必須）
├── start_mac.command             ← ランチャー（このリポジトリに同梱）
├── app/
│   └── conversation_app/         ← PyInstaller成果物 (約180MB)
├── bin/
│   ├── macos-arm64/              ← VOICEVOX ENGINE (約2.0GB)
│   └── ollama_runtime/           ← Ollama本体 (約45MB)
├── models/
│   └── whisper-small/            ← faster-whisper モデル (約464MB)
├── ollama_models/                ← LLMモデル置き場 (gemma4: 約4.0GB)
│   ├── blobs/
│   └── manifests/
└── app_data/
    └── logs/                     ← 実行ログ（初回起動時に自動生成）
```

作業は USB 直書きではなく、まずローカルに `~/dev/usb_local_llm_chat_bundle/`
のような作業フォルダを作って組み立て、最後に rsync で USB へ転送する
（内蔵SSDのほうが速い＆USBを挿しっぱなしにしなくて済む）。

```bash
BUNDLE=~/dev/usb_local_llm_chat_bundle
mkdir -p "$BUNDLE"/{app,bin,models,ollama_models}
```

## 1. VOICEVOX ENGINE（音声合成）

GUI版アプリではなく、HTTPサーバ単体の「VOICEVOX ENGINE」を使う。

1. https://github.com/VOICEVOX/voicevox_engine/releases から
   `voicevox_engine-macos-arm64-0.25.2.7z.001` をダウンロード
   （分割7zアーカイブ。`.001` だけで全体が入っていることもあれば `.002` 以降もある。
   全部同じフォルダに置いて `.001` を解凍する）
2. 解凍（`brew install sevenzip` で入る `7zz` か、Keka などのGUIツール）:
   ```bash
   7zz x voicevox_engine-macos-arm64-0.25.2.7z.001
   ```
3. できた `macos-arm64/` フォルダを `$BUNDLE/bin/` に移動:
   ```bash
   mv macos-arm64 "$BUNDLE/bin/"
   chmod +x "$BUNDLE/bin/macos-arm64/run"
   ```
4. 動作確認（Ctrl+C で止める）:
   ```bash
   cd "$BUNDLE/bin/macos-arm64" && ./run --host 127.0.0.1 --port 50021
   # 別ターミナルで: curl http://127.0.0.1:50021/version
   ```

## 2. Ollama 本体（LLM実行エンジン）

Homebrew でインストールした実体（libexec の中身）を丸ごとコピーするだけで
ポータブルに動く。

```bash
brew install ollama            # 既に入っていればスキップ
cp -R "$(brew --prefix)/Cellar/ollama/$(ls $(brew --prefix)/Cellar/ollama | tail -1)/libexec/" \
      "$BUNDLE/bin/ollama_runtime/"
"$BUNDLE/bin/ollama_runtime/ollama" --version   # 動作確認（0.30.7 で検証済み）
```

## 3. LLM モデル（gemma4）

Ollama は環境変数 `OLLAMA_MODELS` でモデル置き場を変えられる。
**最初からバンドル内を指して pull すれば、コピー作業も不要で必要なモデルだけが入る**:

```bash
OLLAMA_MODELS="$BUNDLE/ollama_models" "$BUNDLE/bin/ollama_runtime/ollama" serve &
OLLAMA_MODELS="$BUNDLE/ollama_models" "$BUNDLE/bin/ollama_runtime/ollama" pull gemma4:e2b-it-qat
kill %1   # serve を止める
```

（既に `~/.ollama/models/` に pull 済みのモデルを流用したい場合は、
`manifests/registry.ollama.ai/library/<モデル名>/` と、そのマニフェストが参照する
`blobs/sha256-*` ファイル群をコピーしてもよい。ただし pull し直すほうが確実で簡単）

## 4. Whisper モデル（音声認識）

faster-whisper のモデルは **初回実行時に HuggingFace Hub から
`~/.cache/huggingface/hub/` へ自動ダウンロードされる**。
つまりキャッシュフォルダは最初から存在するわけではない。
アプリを一度実行してもいいが、モデルだけ先に落とすほうが早い:

```bash
# リポジトリの venv に huggingface_hub が入っている（faster-whisper の依存）
.venv/bin/python -c "from huggingface_hub import snapshot_download; \
    snapshot_download('Systran/faster-whisper-small')"
```

キャッシュの実体は symlink 込みの特殊構造なので、**symlink を実体化(-L)しながら**
バンドルへコピーする:

```bash
SNAP=~/.cache/huggingface/hub/models--Systran--faster-whisper-small/snapshots
rsync -aL "$SNAP/$(ls $SNAP | head -1)/" "$BUNDLE/models/whisper-small/"
# config.json / model.bin / tokenizer.json / vocabulary.txt の4つが入っていればOK
```

## 5. アプリ本体（PyInstaller ビルド）

```bash
cd <このリポジトリ>
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt pyinstaller
.venv/bin/pyinstaller app.spec --noconfirm
rsync -a --delete dist/conversation_app/ "$BUNDLE/app/conversation_app/"
```

ビルド設定はすべて `app.spec` に書いてある（ネイティブライブラリの収集、
`index.html`/`static/` の同梱、multiprocessing フックなど）。
**コード・static・index.html を変更したら必ず再ビルド**すること
（フロントエンドのJSも exe の中に焼き込まれるため）。

## 6. ランチャー

```bash
cp start_mac.command "$BUNDLE/"
chmod +x "$BUNDLE/start_mac.command"
```

ランチャーがやること: ポート衝突チェック → Ollama(11434) → VOICEVOX(50021) →
アプリ(5001) の順に起動 → ヘルスチェック → ブラウザを開く → 終了時に全プロセス掃除。
ログは `app_data/logs/` に追記式で残る。

## 7. USB への転送

1. **ディスクユーティリティ**で USB をフォーマット:
   - 表示 → すべてのデバイスを表示 → USBの親デバイスを選択 → 消去
   - フォーマット: **APFS**（exFAT/FAT32 は実行権限と symlink が消えるためNG）
   - 方式: **GUIDパーティションマップ**
   - 名前: 任意（例 `USB_LLM_CHAT`）
2. 転送と実行権限の確認:
   ```bash
   rsync -a "$BUNDLE/" /Volumes/USB_LLM_CHAT/
   chmod +x /Volumes/USB_LLM_CHAT/start_mac.command
   ```

## 8. 動作確認チェックリスト

- [ ] USB の `start_mac.command` を**右クリック→「開く」**（初回のみ。Gatekeeper対策）
- [ ] 3サービスの起動チェックがすべて ✅ になる（初回はモデルロードで1〜2分待つ）
- [ ] ブラウザが自動で開き、テキスト送信に返答が返る
- [ ] マイクボタン初回クリックで「"ターミナル"がマイクにアクセスを求めています」
      → **許可** を押す（拒否すると音声認識だけ失敗する）
- [ ] ターミナルを閉じる（or Ctrl+C）と全プロセスが止まる
- [ ] うまく動かないときは `app_data/logs/` の3ファイルを確認

## ハマりどころ（過去に踏んだ罠）

| 症状 | 原因と対策 |
|---|---|
| exe が無限に自己増殖する | `multiprocessing.freeze_support()` を app.py 冒頭で呼ぶ（対応済み） |
| 起動途中でランチャーに殺される | USBからのモデルロードは数分かかる。`wait_for` のタイムアウトは300秒に設定済み |
| 終了しても port 50021 が残る | VOICEVOX はワーカーを spawn する。`set -m` + プロセスグループkillで対応済み |
| 他のMacでチャット・音声が無反応 | JSの接続先ポートのハードコード（修正済み: `io()`）とCDN依存（修正済み: `static/vendor/` 同梱）|
| ブラウザで顔が表示されない | オフライン環境でCDNから p5.js が取れていない → `static/vendor/` 参照になっているか確認 |
| ポート5000が使えない | macOS の AirPlay Receiver が占有。本アプリは5001を使用 |
