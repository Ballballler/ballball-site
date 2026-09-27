"""音频初步分析。

给一首曲子算出能直接摆到页面上给人看的一组参数：速度、调性、响度、明暗、
密度、留白，外加一条画波形用的包络线。

分工很清楚：
  - librosa 干重活（解码、节拍跟踪、色度向量），BSD 许可，pip 直装；
  - 判断部分自己写。作品只有几首，用不着一整套 MIR 流水线，
    而且「这几首对自己意味着什么」只有站长知道。

librosa 没装时整个模块退化成「不可用」，站点其余功能照常跑，不会 import 就崩。
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

from .config import MAX_AUDIO_BYTES, STATIC_DIR, UPLOAD_DIR

# 分析超过这个秒数就截断。够听完副歌了，也没必要为一首 demo 跑满十分钟。
MAX_ANALYZE_SECONDS = 300

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Krumhansl-Kessler 调性轮廓。大调小调各一条，用来跟色度向量做相关性匹配。
KS_MAJOR = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
KS_MINOR = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]


class AudioAnalysisError(RuntimeError):
    """分析跑不下去时抛出，message 直接给用户看。"""


def available() -> tuple[bool, str]:
    """librosa 装没装。返回 (能不能用, 版本或缺失原因)。"""
    try:
        import librosa  # noqa: PLC0415 - 依赖是可选的，不能在模块顶层 import

        return True, f"librosa {librosa.__version__}"
    except Exception as exc:  # pragma: no cover - 取决于环境
        return False, str(exc)


def _require_librosa():
    try:
        import librosa  # noqa: PLC0415
    except Exception as exc:  # pragma: no cover
        raise AudioAnalysisError(
            "自动分析依赖 librosa，当前环境没装。"
            "在项目目录里跑 pip install librosa 装上，再点一次分析。"
        ) from exc
    return librosa


def resolve_audio(audio_url: str) -> Path:
    """把作品里存的 audio_url 转成磁盘上的真实路径。

    库里存 /uploads/2026-09/xxx.mp3 这种站内地址；导 once 静态站时会被改成相对路径，
    所以两种形态都得认。找不到就直接报错，不猜。
    """
    raw = (audio_url or "").strip()
    if not raw:
        raise AudioAnalysisError("这个作品还没有音频文件")

    # 库里可能存着好几种写法，挨个试：绝对路径 / /uploads 开头 / 导出后的相对路径 / 只有文件名
    candidates = [
        Path(raw),
        STATIC_DIR / raw.lstrip("/"),
        UPLOAD_DIR / raw.lstrip("/"),
        UPLOAD_DIR / Path(raw).name,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate

    # 上传时按月份分子目录，最后兜一层按文件名搜
    for found in UPLOAD_DIR.rglob(Path(raw).name):
        return found
    raise AudioAnalysisError(f"找不到音频文件：{raw}")


def _load_array(path: Path, sr: int = 22050):
    """读音频为单声道 ndarray。mp3 解不开时退回 ffmpeg 转一遍 wav。"""
    librosa = _require_librosa()
    try:
        y, real_sr = librosa.load(str(path), sr=sr, mono=True)
    except Exception:
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise AudioAnalysisError(
                f"{path.name} 解不开，也没找到 ffmpeg 兜底。"
                "把 ffmpeg 放进 PATH，或者传 .wav / .flac。"
            )
        with tempfile.TemporaryDirectory() as tmp:
            wav = Path(tmp) / "decoded.wav"
            subprocess.run(
                [ffmpeg, "-y", "-i", str(path), "-ac", "1", "-ar", str(sr), str(wav)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=120,
            )
            y, real_sr = librosa.load(str(wav), sr=sr, mono=True)

    if y.size == 0:
        raise AudioAnalysisError("这个文件解出来是空的")
    limit = int(MAX_ANALYZE_SECONDS * real_sr)
    if y.size > limit:
        y = y[:limit]
    return y, real_sr


def _to_db(value: float) -> float:
    import numpy as np  # noqa: PLC0415

    return float(20 * np.log10(max(value, 1e-10)))


def estimate_key(y, sr) -> tuple[str, float]:
    """用色度向量配 KS 轮廓估调性。返回 (调名如 Am, 相关强度 0-1)。"""
    librosa = _require_librosa()
    import numpy as np  # noqa: PLC0415

    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    profile = chroma.mean(axis=1)
    if profile.sum() <= 0:
        return "", 0.0
    profile = profile / profile.sum()

    best_key, best_score, best_scale = "", -2.0, "major"
    for shift in range(12):
        rotated = np.roll(profile, shift)
        for scale, ks in (("major", KS_MAJOR), ("minor", KS_MINOR)):
            ref = np.array(ks, dtype=float)
            corr = float(np.corrcoef(rotated, ref)[0, 1])
            if corr > best_score:
                # np.roll 把 profile 往右挪了 shift 位，主音要往回数
                best_key = NOTE_NAMES[(-shift) % 12]
                best_score = corr
                best_scale = scale
    label = best_key if best_scale == "major" else f"{best_key}m"
    # 相关系数落在 -1..1，压成 0..1 好显示
    return label, round(max(0.0, (best_score + 1) / 2), 3)


def _waveform(y, points: int = 160) -> list[int]:
    """把振幅包络抽稀成 0-100 的整数序列，前端拿去画条形。"""
    import numpy as np  # noqa: PLC0415

    # array_split 不要求整除，最后一段短一点没关系
    frames = np.array_split(np.abs(y), points)
    peak = np.array([float(f.max()) if f.size else 0.0 for f in frames])
    top = float(peak.max()) or 1.0
    return [int(round(v / top * 100)) for v in peak[:points]]


def _describe(bpm: int, brightness: float, dyn_range: float,
              onset_rate: float, silence: float) -> tuple[list[str], str]:
    """把数值翻译成人话。返回 (短标签列表, 一句话总结)。"""
    if bpm and bpm < 70:
        speed = "很慢"
    elif bpm and bpm < 100:
        speed = "中慢"
    elif bpm and bpm < 120:
        speed = "中速"
    elif bpm and bpm < 140:
        speed = "偏快"
    elif bpm:
        speed = "快"
    else:
        speed = "速度测不出"

    if brightness < 900:
        tone = "偏暗"
    elif brightness < 2200:
        tone = "明暗居中"
    else:
        tone = "偏亮"

    if dyn_range > 14:
        dynamics = "起伏大"
    elif dyn_range > 7:
        dynamics = "起伏适中"
    else:
        dynamics = "压得很平"

    if onset_rate < 1.5:
        density = "织体稀疏"
    elif onset_rate < 5:
        density = "密度中等"
    else:
        density = "很密集"

    labels = ([speed] if bpm else []) + [tone, dynamics, density]
    if silence > 0.12:
        labels.append("留白多")

    sentence = (
        f"约 {bpm} BPM，{tone}，{dynamics}，{density}。"
        if bpm
        else f"测不出稳定节拍，所以不硬报速度。整体{tone}，{dynamics}，{density}。"
    )
    return labels, sentence


def analyze_file(path: Path) -> dict:
    """分析一个音频文件，返回可直接入库的字典。"""
    if not path.is_file():
        raise AudioAnalysisError(f"文件不存在：{path.name}")
    if path.stat().st_size > MAX_AUDIO_BYTES:
        raise AudioAnalysisError("文件超过单首上限，先压一版再分析")

    ok, engine = available()
    if not ok:
        raise AudioAnalysisError(f"自动分析不可用：{engine}")

    librosa = _require_librosa()
    import numpy as np  # noqa: PLC0415

    y, sr = _load_array(path)
    duration = round(len(y) / sr, 2)

    # 默认 hop_length=512 在这批素材上会低估几个 BPM（120 的点击测出 117），
    # 收到 256 之后同一份样本测到 120.19。代价是算得慢一点，可接受。
    hop = 256
    oenv = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    tempo_raw, beats = librosa.beat.beat_track(onset_envelope=oenv, sr=sr, hop_length=hop)
    raw_bpm = int(round(float(np.atleast_1d(tempo_raw)[0]))) if np.size(tempo_raw) else 0

    # 三道闸：节拍点数、节拍间隔是否匀、tempogram 上到底有没有那个峰。
    # 第三道最关键 —— 没有鼓的铺底，跟踪器照样能凑出一串「节拍」，
    # 那数字是假的。合成一张无节拍的噪声 pad 实测峰值显著度只有 2.0，
    # 有节拍的样本在 5 以上，门槛取 3.5。
    beat_times = librosa.frames_to_time(beats, sr=sr, hop_length=hop)
    steadiness = 0.0
    if beat_times.size >= 8:
        gaps = np.diff(beat_times)
        mean_gap = float(gaps.mean()) if gaps.size else 0.0
        if mean_gap > 0:
            steadiness = max(0.0, 1.0 - float(gaps.std() / mean_gap))

    tempogram = librosa.feature.tempogram(onset_envelope=oenv, sr=sr, hop_length=hop)
    curve = tempogram.mean(axis=1)
    spread = float(curve.std())
    peak_z = float((curve.max() - curve.mean()) / spread) if spread else 0.0

    steady = beat_times.size >= 8 and steadiness >= 0.75 and peak_z >= 3.5
    bpm = raw_bpm if steady else 0

    key, key_confidence = estimate_key(y, sr)

    rms = librosa.feature.rms(y=y)[0]
    rms_db = _to_db(float(np.mean(rms)))
    loud = np.percentile(rms, 95)
    quiet = np.percentile(rms, 5)
    dyn_range = round(_to_db(float(loud)) - _to_db(float(quiet)), 2)

    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    brightness = round(float(np.mean(centroid)), 1)

    onsets = librosa.onset.onset_detect(y=y, sr=sr)
    onset_rate = round(len(onsets) / duration, 2) if duration else 0.0

    silence = round(float(np.mean(rms < 0.003)), 3)

    labels, sentence = _describe(bpm, brightness, dyn_range, onset_rate, silence)

    return {
        "duration": duration,
        "sample_rate": sr,
        "bpm": bpm,
        "key": key,
        "key_confidence": key_confidence,
        "rms_db": round(rms_db, 2),
        "dynamic_range_db": dyn_range,
        "brightness_hz": brightness,
        "onset_rate": onset_rate,
        "silence_ratio": silence,
        "waveform": _waveform(y),
        "labels": labels,
        "verdict": sentence,
        "engine": engine,
        "analyzed_at": datetime.utcnow().isoformat(timespec="seconds"),
    }


def analyze_work_audio(audio_url: str) -> dict:
    """给后台用：传 audio_url，返回分析结果。"""
    return analyze_file(resolve_audio(audio_url))
