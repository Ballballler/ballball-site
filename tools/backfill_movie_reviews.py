"""给「已经有短评、但长评还空着」的正式档案，依据短评补齐一篇长评。

背景：站长说「有些长评我不想写了，根据我的短评补齐」——所以这不是凭空生成，
而是**以他自己写的那句短评为骨**，按他已有 6 篇长评的调性铺开成三段：
    1. 这部片到底在讲什么 / 它的核心设计是什么；
    2. 技法层面（声音、节奏、表演、意象、结构）；
    3. 诚实的保留意见或立场收尾。
短评是差评的（如《寂静之地》），长评照样写差评 —— 不美化、不找补。

安全设计（沿用 backfill_movie_posters.py 的模式）：
    - 跑前自动备份 site.db（含 -wal/-shm）到 backup/movie-reviews-<时间>/
    - --dry-run 全程不写库
    - **只填 review 为空的行**；已经有长评的一律跳过，绝不覆盖站长自己写的字

用法：
    python tools/backfill_movie_reviews.py --dry-run
    python tools/backfill_movie_reviews.py
"""
from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.database import Base, SessionLocal, engine, ensure_extra_columns  # noqa: E402
from app import models as M  # noqa: E402

DB = ROOT / "data" / "site.db"
BACKUP_DIR = ROOT / "backup"

# 片名 -> 长评。按站长的短评为骨撰写，三段式，段间空行。
REVIEWS: dict[str, str] = {
    "釜山行": """它把丧尸片的战场从医院和超市搬进了一列开动的列车——这是个聪明的设计，因为车厢本身就是社交切片：商务座、普通车厢、最后挤满人的那一节。危险一来，等级和体面瞬间失效，人比丧尸先崩。

最动人的地方不是撕咬，是那些沉默的选择。父亲从「先顾自己」到把女儿推到安全那边的整条弧线，落地得扎实；那对夫妻、那对老年姐妹、那个流浪汉，每个配角都分到了一笔。结尾列车停下、只剩歌声的那一下，把前面所有的拥挤都抽空了。

要说缺点，中段的人性冲突写得偏直白，坏人坏得没有余地。但这不影响它是我心里最好的丧尸片——它证明了类型片也可以有真正的重量。""",
    "寂静之地": """设定其实很迷人：不能出声，于是所有的惊恐都被压成了呼吸和眼神。安静本身就是悬念，这个前提立住了，片子就有了魂。

问题出在人物上。为了制造冲突，剧本一再让角色做出明显不合理的决定——把婴儿生下来、在沙地上踩出响亮的一步、该跑的时候停下来聊天。这些不是「恐怖片的紧张」，是把观众的智商按住不让动。明明有一整个世界可以玩（声音如何被利用、沉默如何被打破），最后却退化成了最老套的那种「谁发出声音谁死」的追逐游戏。

所以我给的分不高，不是因为它不好看，而是因为它明明可以更好。恐怖片要进步，就得丢掉这种低级的戏剧套路。""",
    "招魂": """温子仁最擅长的其实是「日常里的不对劲」。衣柜、镜子、拍手的那一声「clap」——他把恐怖种在你家里最熟悉的地方，而不是什么废弃病院。前期的氛围调度是真的好，那种慢慢收紧的压力，是后来很多模仿者学不来的。

但现在回头看，它确实旧了。鬼屋驱魔的框架太标准，沃伦夫妇的调查线是按套路走的，真正的恐惧全靠几个 jump scare 顶着，而这些惊吓点看过一次就失效了。当年看它是被吓到，现在看它是被提醒「哦，这里要跳出一只鬼」。

放在它上映的那个年份，它是类型片里做得干净漂亮的一部；放到今天，它更像是一本被反复翻印的教科书——经典，但没什么新东西了。""",
    "危笑": """它吓人的方式很特别：不做血，不做鬼，做的是那种「笑」。嘴角咧到不自然的角度、眼神是空的、脸是往你这边凑过来的——这种「阴」比任何一个 jump scare 都持久，因为它把恐惧埋进了最无害的表情里。

规则的建立是它最扎实的地方：被诅咒的人会自杀、会传给别人、时限很短、无解。这种冷硬的宿命感，配上主角一点点被现实抛弃的过程（朋友不信、警察当她是疯子），让整部片像一场别人看不见的溺水。

当然，结尾那个巨物显形稍微破坏了前面积累的克制，把留白填得太满了。但就前面那一个多小时来说，它是近些年最让我坐立不安的恐怖片之一。""",
}


def backup_db() -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = BACKUP_DIR / f"movie-reviews-{stamp}"
    dest.mkdir(parents=True, exist_ok=True)
    for suffix in ("", "-wal", "-shm"):
        src = Path(str(DB) + suffix)
        if src.exists():
            shutil.copy2(src, dest / src.name)
    print(f"[备份] -> {dest}")
    return dest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not args.dry_run:
        backup_db()

    Base.metadata.create_all(bind=engine)
    ensure_extra_columns()

    db = SessionLocal()
    filled = skipped = missing = 0
    try:
        for title, review in REVIEWS.items():
            m = db.query(M.Movie).filter(M.Movie.title == title).one_or_none()
            if m is None:
                print(f"  [缺失] 《{title}》不在库里")
                missing += 1
                continue
            if (m.review or "").strip():
                print(f"  [跳过] 《{title}》已有长评（{len(m.review)} 字），不覆盖")
                skipped += 1
                continue
            if not (m.verdict or "").strip():
                print(f"  [警告] 《{title}》连短评都没有，仍然写入（依据是片单本身）")
            print(f"  [补写] 《{title}》 -> {len(review)} 字（短评 {len(m.verdict or '')} 字）")
            m.review = review
            filled += 1

        if args.dry_run:
            db.rollback()
            print(f"\n[dry-run] 会补 {filled} 篇，跳过 {skipped}，缺失 {missing}，未写库")
        else:
            db.commit()
            print(f"\n[完成] 补写 {filled} 篇，跳过 {skipped}，缺失 {missing}")
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
