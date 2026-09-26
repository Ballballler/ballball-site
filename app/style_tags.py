"""音乐作品的风格标签推断。

这里不是 AI，是一套确定性规则：关键词 + BPM + 调性 + 完成度。
推断结果只当候选项交给后台点选，最终写进 tags 的永远是站长认可的那些。
想加新风格就往 KEYWORD_RULES 里加一行，不用动别的地方。
"""
from __future__ import annotations

# (标签, 关键词)：命中任意一个就作为候选。匹配不区分大小写。
KEYWORD_RULES: list[tuple[str, list[str]]] = [
    ("氛围", ["ambient", "atmosphere", "氛围", "环境音", "空间感", "pad", "drone"]),
    ("合成器", ["synth", "synthesizer", "合成器", "moog", "模拟", "analog"]),
    ("电子", ["electronic", "电音", "电子", "edm", "techno", "house", "trance"]),
    ("碎拍", ["break", "breakbeat", "碎拍", "jungle", "drum and bass", "dnb"]),
    ("舞曲", ["dance", "舞曲", "club", "disco", "groove", "律动"]),
    ("Lo-fi", ["lo-fi", "lofi", "低保真", "磁带", "tape", "底噪"]),
    ("钢琴", ["piano", "钢琴", "keys", "键盘"]),
    ("吉他", ["guitar", "吉他", "木吉他", "acoustic", "riff"]),
    ("弦乐", ["string", "弦乐", "violin", "小提琴", "cello", "大提琴"]),
    ("人声", ["vocal", "voice", "人声", "唱", "合唱", "choir", "和声"]),
    ("电影感", ["cinematic", "soundtrack", "score", "电影", "配乐", "史诗", "epic"]),
    ("实验", ["experiment", "实验", "noise", "噪音", "glitch", "故障"]),
    ("民谣", ["folk", "民谣", "ballad", "叙事"]),
    ("爵士", ["jazz", "爵士", "swing", "即兴", "improvis"]),
    ("摇滚", ["rock", "摇滚", "失真", "distortion", "punk"]),
    ("治愈", ["calm", "healing", "治愈", "安静", "温柔", "柔软", "soft", "quiet"]),
    ("暗色", ["dark", "darkwave", "horror", "恐怖", "阴", "哥特", "gothic", "阴郁"]),
    ("明亮", ["bright", "明亮", "阳光", "轻快", "upbeat", "happy"]),
    ("雨声", ["rain", "雨", "雷雨", "水滴"]),
    ("城市", ["city", "城市", "街头", "地铁", "夜晚的街"]),
]


def _bpm_tags(bpm: int) -> list[str]:
    """BPM 区间 → 速度类标签。太慢和太快都有明确性格，中间只标速度。"""
    if not bpm:
        return []
    if bpm < 70:
        return ["慢板", "氛围"]
    if bpm < 100:
        return ["中速"]
    if bpm < 120:
        return ["律动"]
    if bpm < 140:
        return ["舞曲感"]
    return ["高速", "碎拍"]


def _key_tags(key_signature: str) -> list[str]:
    """调性：带 m 结尾算小调，其余按大调处理。"""
    k = (key_signature or "").strip()
    if not k:
        return []
    return ["小调"] if k.lower().endswith("m") else ["大调"]


def _progress_tags(progress: int) -> list[str]:
    if not progress:
        return []
    if progress >= 90:
        return ["接近完成"]
    if progress < 30:
        return ["早期草稿"]
    return []


def suggest_style_tags(
    *,
    title: str = "",
    summary: str = "",
    notes: str = "",
    bpm: int = 0,
    key_signature: str = "",
    progress: int = 0,
    existing: list[str] | None = None,
) -> list[str]:
    """按规则推断候选风格标签。已存在的标签不再重复推荐。"""
    haystack = " ".join([title or "", summary or "", notes or ""]).lower()

    found: list[str] = []
    for tag, words in KEYWORD_RULES:
        if any(w.lower() in haystack for w in words):
            found.append(tag)

    for tag in _bpm_tags(bpm) + _key_tags(key_signature) + _progress_tags(progress):
        if tag not in found:
            found.append(tag)

    already = {t.strip() for t in (existing or [])}
    return [t for t in found if t not in already]
