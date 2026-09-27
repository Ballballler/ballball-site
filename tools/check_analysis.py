"""用合成音频验证分析管线：已知答案的输入，才能判断输出对不对。

三份样本：
  1. 120 BPM 的节拍点击 —— 应该报 120
  2. 没有节拍的合成器铺底 —— 应该报 0（不给数字）
  3. 220Hz + 277Hz（A 大调三音之一对）持续音 —— 应该认出 A 大调
"""
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
import tempfile

ROOT = Path(r"D:\ballball-site")
sys.path.insert(0, str(ROOT))

from app.audio_analysis import analyze_file  # noqa: E402

SR = 22050
SECONDS = 20


def click_track(bpm: int = 120) -> np.ndarray:
    total = SR * SECONDS
    y = np.zeros(total)
    period = int(SR * 60 / bpm)
    for start in range(0, total - period, period):
        burst = np.random.default_rng(0).normal(0, 1, 400) * np.exp(-np.linspace(0, 8, 400))
        y[start : start + 400] += burst * 0.9
    return y


def drone(freqs=(220.0, 277.18, 329.63)) -> np.ndarray:
    t = np.arange(SR * SECONDS) / SR
    y = np.zeros_like(t)
    for i, f in enumerate(freqs):
        y += np.sin(2 * np.pi * f * t) * (0.4 / (i + 1))
    # 缓一点的包络，避免整段一个电平
    y *= 0.6 + 0.4 * np.sin(2 * np.pi * 0.05 * t)
    return y


def pad_no_beat() -> np.ndarray:
    """滤过噪声当 pad：有音高重心，没有周期性节拍。"""
    rng = np.random.default_rng(7)
    noise = rng.normal(0, 1, SR * SECONDS)
    # 一阶低通，压成暗一点的铺底
    y = np.convolve(noise, np.ones(64) / 64, mode="same")
    return y / max(abs(y).max(), 1e-9) * 0.8


with tempfile.TemporaryDirectory() as tmp:
    cases = [
        ("120 BPM 节拍点击", click_track(120), dict(expect_bpm=120)),
        ("A 大调持续和弦", drone(), dict(expect_key="A")),
        ("无节拍 pad", pad_no_beat(), dict(expect_bpm=0)),
    ]
    for name, sig, expect in cases:
        path = Path(tmp) / f"{name}.wav"
        sf.write(str(path), sig.astype("float32"), SR)
        result = analyze_file(path)
        got_bpm = result["bpm"]
        got_key = result["key"]
        checks = []
        if "expect_bpm" in expect:
            ok = got_bpm == expect["expect_bpm"]
            checks.append(f"BPM {got_bpm}（期望 {expect['expect_bpm']}）{'✓' if ok else '✗'}")
        if "expect_key" in expect:
            ok = got_key.startswith(expect["expect_key"])
            checks.append(f"调性 {got_key}（期望 {expect['expect_key']}…）{'✓' if ok else '✗'}")
        print(f"{name:16s} | " + " | ".join(checks))
