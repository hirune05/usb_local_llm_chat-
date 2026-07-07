import csv
import os
import time

from config import TIMING_CSV_HEADERS, TIMING_CSV_PATH


def print_timing_table(total_time, llm_time, param_time,
                       prompt_tokens=None, completion_tokens=None):
    """処理時間を表形式で標準出力する。"""
    def pct(t):
        return (t / total_time * 100) if total_time > 0 else 0

    other_time = total_time - llm_time - param_time

    print("\n" + "=" * 50)
    print("           処理時間計測結果")
    print("=" * 50)
    print(f"{'項目':<20} | {'時間(秒)':<10} | {'割合(%)':<8}")
    print("-" * 50)
    print(f"{'全体処理時間':<20} | {total_time:<10.4f} | {'100.0':<8}")
    print(f"{'LLM応答生成':<20} | {llm_time:<10.4f} | {pct(llm_time):<8.1f}")
    print(f"{'パラメータ計算':<20} | {param_time:<10.4f} | {pct(param_time):<8.1f}")
    print(f"{'その他処理':<20} | {other_time:<10.4f} | {pct(other_time):<8.1f}")
    print("-" * 50)
    p = prompt_tokens if prompt_tokens is not None else "N/A"
    c = completion_tokens if completion_tokens is not None else "N/A"
    total = (prompt_tokens or 0) + (completion_tokens or 0)
    t = total if total > 0 else "N/A"
    print(f"{'トークン数':<20} | {'入力':<10} | {'出力':<8}")
    print("-" * 50)
    print(f"{'トークン':<20} | {p!s:<10} | {c!s:<8}")
    print(f"{'合計トークン':<20} | {t!s:<10} |")
    print("=" * 50 + "\n")


def save_timing_row(session_id, total_time, llm_time, param_time):
    """計測した処理時間を timing_data.csv に追記する。"""
    other_time = total_time - llm_time - param_time

    file_exists = os.path.isfile(TIMING_CSV_PATH)
    with open(TIMING_CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=TIMING_CSV_HEADERS)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "session_id": session_id,
            "total_time": round(total_time, 6),
            "llm_time": round(llm_time, 6),
            "param_time": round(param_time, 6),
            "other_time": round(other_time, 6),
        })
    print(f"--- タイミングデータが {TIMING_CSV_PATH} に保存されました ---")
