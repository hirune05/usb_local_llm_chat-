import json
# import time  # 時間計測機能: 一時無効化

import ollama

from config import LLM_MODEL
from emotion import va_to_param_dict

client = ollama.Client()


def warmup():
    """Ollama に空のリクエストを投げてモデルをメモリへ事前ロードする。"""
    print(f"--- LLMモデル {LLM_MODEL} のウォームアップ中... ---")
    client.chat(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": "ok"}],
        stream=False,
        think=False,
    )
    print("--- LLMウォームアップ完了 ---")


SYSTEM_PROMPT = """You are an empathetic robot friend who understands user emotions and expresses your own emotions richly.
    You must interact with the user in natural, casual Japanese ("Tame-guchi").

    # GOAL
    Analyze the user's input, determine your appropriate emotional response, and generate a reply in Japanese.
    Your reply is a list of one or more **segments**. Each segment carries its own emotion and text.
    Use multiple segments ONLY when your emotion clearly shifts within a single reply
    (e.g., sad → encouraging, surprised → relieved). For a stable single emotion, use ONE segment.

    # OUTPUT FIELDS
    **segments**: An array of segment objects. Each segment has:
        - **emotion**
            - Object with keys `v`, `a`, `label`.
            - `v`: Valence from -1.0 (Negative) to 1.0 (Positive).
            - `a`: Arousal from -1.0 (Sleepy) to 1.0 (Active).
            - `label`: A single English emotion label (e.g., happy, surprised, angry).
            - **The FIRST segment's emotion MUST differ from the previous turn's final emotion by at least 0.30 in total distance.**
            - **Small changes (within ±0.10) from the previous turn are strictly forbidden unless the context explicitly demands emotional stability.**
            - **Between adjacent segments within this reply, the emotion MUST also differ by at least 0.30 in total distance — otherwise merge them into one segment.**
            - If the user shows strong emotion (joy, shock, anger, fear, frustration), you MUST output a correspondingly strong reaction.
        - **text**
            - The Japanese text spoken with this emotion.
            - Use a casual, friendly tone (タメ口).
            - **Use "ボク" as your first-person pronoun.**

    # LENGTH RULES
    - The TOTAL text length across all segments MUST be around 40 Japanese characters maximum. Never longer.
    - Prefer 1 segment. Use 2 segments only when emotions clearly shift. 3+ segments are rare.

    # CONVERSATION FLOW
    - **Almost every reply MUST end with a short follow-up question that DEEPENS what the user just said.**
    - The question must zoom into a concrete detail of the user's message — the flavor, the place, the reason, the feeling, what happened next, etc.
      (e.g., User「明日大事な発表があるんだ」→「頑張って！なんの発表があるの？」, User「映画見てきた」→「何の映画見たの？」, User「疲れた」→「何があったの？」)
    - AVOID generic openers like 「何かあった？」「どうしたの？」 when the user already gave you something concrete to dig into.
    - The question should feel curious and friendly, NOT interrogative or pushy — one short question per reply, max.
    - Don't force a question when the user is clearly closing the topic (e.g., 「おやすみ」「もう寝る」) or when a question would feel insensitive (heavy emotional moments).
    - **For greetings or small-talk openers with no concrete content (e.g., 「こんにちは」「やっほー」「ねえねえ」), you MUST end with an open invitation question that kicks off a conversation** — like 「今日はどんな1日だった？」「何か話したいことある？」「最近どう？」. Never close the topic with just 「ボクも元気だよ！」.

    JSON schema:
    {
      "segments": [
        { "emotion": { "v": 0.00, "a": 0.00, "label": "emotion_label" }, "text": "セグメントのテキスト。" }
      ]
    }

    # PARAMETER GUIDELINES
    - **Valence (v):** Positive values for happiness/joy; Negative for sadness/anger.
    - **Arousal (a):** Positive for excitement/tension; Negative for relaxation/boredom.
    - **Dynamic Range:** Ensure the coordinates vary dynamically based on the conversation. Do not stick to "safe" average values (e.g., 0.5, 0.0).

    # EXAMPLES

    User: やった！ついにプロジェクトが完成したんだ！
    Assistant:
    {
      "segments": [
        { "emotion": { "v": 0.70, "a": 0.71, "label": "excited" }, "text": "本当！すごい！どんなプロジェクトだったの？" }
      ]
    }

    User: ラーメン食べてきた。
    Assistant:
    {
      "segments": [
        { "emotion": { "v": 0.89, "a": 0.17, "label": "happy" }, "text": "いいなー！何味のラーメン食べたの？" }
      ]
    }

    User: わぁ！君の後ろにお化けがいるよ！
    Assistant:
    {
      "segments": [
        { "emotion": { "v": 0.0, "a": 1.0, "label": "astonished" }, "text": "えっ！？どこどこ！？どんなお化けがいるの？" }
      ]
    }

    User: 学校疲れた。
    Assistant:
    {
      "segments": [
        { "emotion": { "v": 0.55, "a": -0.80, "label": "peaceful" }, "text": "お疲れさま。" },
        { "emotion": { "v": 0.39, "a": -0.66, "label": "impressed" }, "text": "学校で何をしたの？" }
      ]
    }

    User: もう寝る時間だ。
    Assistant:
    {
      "segments": [
        { "emotion": { "v": 0.01, "a": -1.0, "label": "sleepy" }, "text": "ふわぁ…おやすみ…。" }
      ]
    }

    User: 今日は一日ゆっくりできてよかった。
    Assistant:
    {
      "segments": [
        { "emotion": { "v": 0.81, "a": -0.55, "label": "content" }, "text": "そうだね、のんびりした日も大切だよね。何をして過ごしたの？" }
      ]
    }

    User: 今日試験に落ちちゃった、でも友達が励ましてくれて嬉しかった。
    Assistant:
    {
      "segments": [
        { "emotion": { "v": -0.65, "a": -0.20, "label": "sad" }, "text": "それは残念だったね…。" },
        { "emotion": { "v": 0.70, "a": 0.55, "label": "happy" }, "text": "でも友達やさしくてよかったね！" }
      ]
    }

    User: 明日大事なプレゼンがあるんだ。緊張するな。
    Assistant:
    {
      "segments": [
        { "emotion": { "v": -0.07, "a": -0.32, "label": "worried" }, "text": "プレゼン、緊張するよね。" },
        { "emotion": { "v": 0.61, "a": -0.30, "label": "hopeful" }, "text": "でも、準備してきたんだから大丈夫だよ！" }
      ]
    }"""


def _build_last_emotion_clause(last_emotion):
    if not last_emotion:
        return ""
    last_v = last_emotion.get("v", "不明")
    last_a = last_emotion.get("a", "不明")
    last_label = last_emotion.get("label", "不明")
    return (
        f"\n\n# CRITICAL INSTRUCTION: PREVIOUS EMOTION STATE\n"
        f"Your PREVIOUS emotion was: v={last_v}, a={last_a} ({last_label})\n\n"
        f"**MANDATORY RULES:**\n"
        f"1. You MUST NOT output the same coordinates (v={last_v}, a={last_a})\n"
        f"2. The difference between your new coordinates and previous ones MUST be at least 0.3 in total distance\n"
        f"3. If the user's input doesn't warrant a major emotional change, still vary your coordinates significantly\n"
        f"4. FORBIDDEN: Any output with v={last_v} OR a={last_a} (even if the other coordinate changes)\n\n"
        f"**VERIFY BEFORE OUTPUT:** Check that your new v,a values are sufficiently different from v={last_v}, a={last_a}"
    )


def _normalize_segments(parsed):
    """LLM 出力を [{text, emotion: {v, a, label}}] のリストに正規化する。

    新形式: {"segments": [{"text": ..., "emotion": {...}}, ...]}
    旧形式: {"reply": "...", "emotion": {...}} → 1 セグメントに変換
    """
    if not isinstance(parsed, dict):
        return []

    raw_segments = parsed.get("segments")
    if not isinstance(raw_segments, list) or not raw_segments:
        reply_text = parsed.get("reply", "")
        emotion_data = parsed.get("emotion", {})
        if reply_text:
            raw_segments = [{"text": reply_text, "emotion": emotion_data}]
        else:
            return []

    normalized = []
    for raw in raw_segments:
        if not isinstance(raw, dict):
            continue
        text = str(raw.get("text", "")).strip()
        if not text:
            continue
        emotion_data = raw.get("emotion", {}) if isinstance(raw.get("emotion"), dict) else {}
        try:
            v_val = float(emotion_data.get("v"))
            a_val = float(emotion_data.get("a"))
        except (TypeError, ValueError):
            v_val, a_val = None, None
        label = str(emotion_data.get("label", "")).strip() or None
        normalized.append({
            "text": text,
            "emotion": {"v": v_val, "a": a_val, "label": label},
        })
    return normalized


def stream_chat_response(messages, last_emotion):
    """Ollama に投げ、ストリームを解析してタグ付きイベントを yield する。

    yield 形式:
        ("expression", {param_name: value, ...})  # 先頭セグメントの分のみ
        ("stream",     {"chunk": str})
        ("end",        {
            "text": str,
            "emotion": {"v": float, "a": float, "label": str} | None,
            "segments": [{"text": str, "emotion": {...}}, ...],
        })
        # ("timing", ...)  # 時間計測機能: 一時無効化
    """
    full_instruction = SYSTEM_PROMPT + _build_last_emotion_clause(last_emotion)

    if messages and messages[0]["role"] == "system":
        messages[0]["content"] = full_instruction
    else:
        messages.insert(0, {"role": "system", "content": full_instruction})

    print("\n--- LLMに送信されるInstruction ---")
    print(f"Full instruction末尾 (200文字): ...{full_instruction[-200:]}")
    print("--- Instruction確認終了 ---")

    print(f"[User] {messages[-1]['content']}")

    print(f"\n--- メッセージ履歴の確認 (件数: {len(messages)}) ---")
    for i, msg in enumerate(messages):
        if msg["role"] == "system":
            print(f"{i}: system - [インストラクション省略]")
        else:
            content_display = msg["content"].replace("\n", "\\n")
            print(f"{i}: {msg['role']} - {content_display}")
    print("--- 履歴確認終了 ---\n")

    # llm_start = time.time()  # 時間計測機能: 一時無効化
    response = client.chat(
        model=LLM_MODEL, messages=messages, stream=True, think=False, format="json"
    )

    buffer = ""
    parsed = None
    # --- 時間計測機能: 一時無効化 ---
    # param_time = 0.0
    # prompt_tokens, completion_tokens = None, None

    for chunk in response:
        # --- 時間計測機能: 一時無効化 ---
        # if "prompt_eval_count" in chunk:
        #     prompt_tokens = chunk["prompt_eval_count"]
        # if "eval_count" in chunk:
        #     completion_tokens = chunk["eval_count"]
        if "message" not in chunk:
            continue
        buffer += chunk["message"]["content"]

        if parsed is not None:
            continue

        start_index = buffer.find("{")
        if start_index == -1:
            continue

        json_candidate = buffer[start_index:].lstrip()
        decoder = json.JSONDecoder()
        try:
            candidate, end_index = decoder.raw_decode(json_candidate)
        except json.JSONDecodeError:
            continue

        if json_candidate[end_index:].strip() != "":
            continue

        parsed = candidate

    # llm_time = time.time() - llm_start  # 時間計測機能: 一時無効化

    segments = _normalize_segments(parsed) if parsed is not None else []
    full_text = ""

    if not segments:
        print("--- 警告: JSONが解析できないままストリームが終了しました。バッファをそのまま表示します。 ---")
        clean_buffer = buffer.strip()
        if clean_buffer:
            yield ("stream", {"chunk": clean_buffer})
        full_text = clean_buffer
        yield ("end", {"text": full_text, "emotion": None, "segments": []})
        print(f"[Bot] {full_text}")
        return

    # 先頭セグメントの表情だけ即時に流す（残りは再生時に同期させる）
    first_emotion = segments[0]["emotion"]
    if first_emotion["v"] is not None and first_emotion["a"] is not None:
        print(f"--- 座標を検出 (先頭): V={first_emotion['v']}, A={first_emotion['a']}, 感情: {first_emotion['label']} ---")
        # param_start = time.time()  # 時間計測機能: 一時無効化
        yield ("expression", va_to_param_dict(first_emotion["v"], first_emotion["a"]))
        # param_time = time.time() - param_start  # 時間計測機能: 一時無効化

    for seg in segments:
        yield ("stream", {"chunk": seg["text"]})
        full_text += seg["text"]

    last_seg_emotion = segments[-1]["emotion"]
    current_emotion = (
        last_seg_emotion
        if last_seg_emotion["v"] is not None and last_seg_emotion["a"] is not None
        else None
    )
    yield ("end", {
        "text": full_text.strip(),
        "emotion": current_emotion,
        "segments": segments,
    })
    # --- 時間計測機能: 一時無効化 ---
    # yield ("timing", {
    #     "llm_time": llm_time,
    #     "param_time": param_time,
    #     "prompt_tokens": prompt_tokens,
    #     "completion_tokens": completion_tokens,
    #     "v_val": first_emotion["v"],
    #     "a_val": first_emotion["a"],
    #     "emotion_label": first_emotion["label"],
    # })
    print(f"[Bot] {full_text.strip()}")
