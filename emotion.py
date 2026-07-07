import math
import numpy as np

# 論文の式(2)の w
W = 1.0
# 論文の式(2)の ε（ゼロ除算防止）
EPSILON = 1e-9

PARAM_NAMES = [
    "eyeOpenness", "pupilSize", "pupilAngle",
    "upperEyelidAngle", "upperEyelidCoverage", "lowerEyelidCoverage",
    "mouthCurve", "mouthHeight", "mouthWidth",
]

# --- ご注意 ---
# まだ確実な数値ではない
KEYFRAME_PARAMS = {
    "happy": np.array([1, 0.8, 0, 0, 0, 0.06, 30, 1.45, 2.5]),
    "angry": np.array([1, 0.65, 4, 30, 0.22, 0.16, -15, 0.65, 1.4]),
    "sad": np.array([1, 0.85, 0, -18, 0.14, 0.15, -18, 0.7, 1.6]),
    "astonished": np.array([1, 0.65, 0, -18, 0, 0, 12, 3, 1.15]),
    "sleepy": np.array([0.2, 0.75, -18, 0, 0, 0, 2, 2.5, 1.2]),
    "relaxed": np.array([0.2, 0.75, -14, 0, 0, 0.1, 14, 0.45, 1.3]),
}

KEYFRAME_VA = {
    "happy": np.array([0.89, 0.17]),
    "angry": np.array([-0.40, 0.79]),
    "sad": np.array([-0.81, -0.40]),
    "astonished": np.array([0.0, 1.0]),
    "sleepy": np.array([0.01, -1.0]),
    "relaxed": np.array([0.71, -0.65]),
}


def get_interpolated_expression(target_v, target_a):
    """ターゲットのVA座標に基づき、表情パラメータを補間する"""
    target_va = np.array([target_v, target_a])

    rtop_values = []
    params_list = []
    emotion_names = []

    for emotion_name, key_va in KEYFRAME_VA.items():
        distance = np.linalg.norm(target_va - key_va)
        rtop_k = 1.0 / (distance + EPSILON)
        rtop_values.append(rtop_k)
        params_list.append(KEYFRAME_PARAMS[emotion_name])
        emotion_names.append(emotion_name)

    rtop_values = np.array(rtop_values)
    T = 1  # 温度パラメータ
    exp_rtop = np.exp((rtop_values - np.max(rtop_values)) / T)
    softmax_weights = exp_rtop / np.sum(exp_rtop)

    print(f"\n=== V={target_v}, A={target_a} の重み分析 ===")
    print(f"{'感情':<10} | {'距離':<8} | {'rtop_k':<11} | {'r_k (softmax)':<15}")
    print("-" * 65)
    for i, emotion_name in enumerate(emotion_names):
        distance = np.linalg.norm(target_va - KEYFRAME_VA[emotion_name])
        print(f"{emotion_name:<12} | {distance:<10.4f} | {rtop_values[i]:<15.6f} | {softmax_weights[i]:<15.6f}")
    print("=" * 65 + "\n")

    print("\n=== r_k values (emotion weights, normalized) ===")
    for name, rk in zip(emotion_names, softmax_weights):
        print(f"{name}: {rk}")
    print("===============================================\n")

    # ===== 1. 重み付き平均（ベース計算） =====
    final_params = np.zeros(9)
    for w, p in zip(softmax_weights, params_list):
        final_params += w * p

    base_upperEyelidCoverage = final_params[4]

    print("--- ベース補間結果 (ファジー適用前) ---")
    print(f"Base eyeOpenness: {final_params[0]:.4f}")
    print(f"Base upperEyelidCoverage: {base_upperEyelidCoverage:.4f}")
    print("-" * 35)

    # ===== 2. ファジー制御による上書き =====
    weights_dict = {name: weight for name, weight in zip(emotion_names, softmax_weights)}

    # --- 2a. eyeOpenness (index 0) の上書き ---
    Wide_Score = (weights_dict.get("happy", 0) + weights_dict.get("angry", 0)
                  + weights_dict.get("sad", 0) + weights_dict.get("astonished", 0))
    Narrow_Score = weights_dict.get("sleepy", 0) + weights_dict.get("relaxed", 0)
    Score = Wide_Score - Narrow_Score
    k = 20.0
    sigmoid_output_eye = 1.0 / (1.0 + math.exp(-k * Score))

    MIN_OPENNESS = 0.2
    MAX_OPENNESS = 1.0
    final_params[0] = MIN_OPENNESS + (MAX_OPENNESS - MIN_OPENNESS) * sigmoid_output_eye

    # --- 2b. upperEyelidCoverage (index 4) の上書き（ハイブリッド方式）---
    Cover_Score = weights_dict.get("angry", 0) + weights_dict.get("sad", 0)
    No_Cover_Score = (weights_dict.get("happy", 0) + weights_dict.get("astonished", 0)
                      + weights_dict.get("sleepy", 0) + weights_dict.get("relaxed", 0))
    Score_coverage = Cover_Score - No_Cover_Score
    k_coverage = 20.0
    sigmoid_gate = 1.0 / (1.0 + math.exp(-k_coverage * Score_coverage))
    target_coverage = sigmoid_gate * base_upperEyelidCoverage

    print("--- upperEyelidCoverage ファジー計算 (ゲート * Base値 方式) ---")
    print(f"Cover_Score: {Cover_Score:.4f}, No_Cover_Score: {No_Cover_Score:.4f}, Score: {Score_coverage:.4f}")
    print(f"Sigmoid出力 (ゲート): {sigmoid_gate:.4f}")
    print(f"目標値 (Base値): {base_upperEyelidCoverage:.4f}")
    print(f"target_coverage (出力): {target_coverage:.4f}")

    final_params[4] = target_coverage

    # ===== 3. 最終結果の表示 =====
    print(f"\n--- 補間結果 (ファジー適用後): V={target_v}, A={target_a} ---")
    print(f"{'Parameter':<20} | {'Value':<12}")
    print("-" * 35)
    for i, (name, value) in enumerate(zip(PARAM_NAMES, final_params)):
        if i == 0:
            print(f"{name:<20} | {value:<12.4f}  <-- ファジー制御 (EyeOpen)")
        elif i == 4:
            print(f"{name:<20} | {value:<12.4f}  <-- ファジー制御 (EyelidCov)")
        else:
            print(f"{name:<20} | {value:<12.4f}")
    print("=" * 35 + "\n")
    return final_params


def va_to_param_dict(v, a):
    """V/A 座標から PARAM_NAMES をキーにした表情パラメータ dict を返す。"""
    params = get_interpolated_expression(v, a)
    return {name: val for name, val in zip(PARAM_NAMES, params)}
