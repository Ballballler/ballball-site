"""初始数据。

只在数据库为空时写入一次。所有内容都能在后台改掉，
这里提供的是可直接上手的真实示例，不是 Lorem Ipsum。
"""
from __future__ import annotations

from .database import SessionLocal
from .models import (
    Category,
    Interest,
    JourneyStep,
    Movie,
    Profile,
    ResumeItem,
    SkillItem,
    Work,
)
from .page_sections import ensure_default_page_sections

MOVIE_GENRES = [
    ("心理惊悚", "#a78bfa", "靠氛围和人物状态压着你，不靠 jump scare"),
    ("超自然", "#38bdf8", "鬼、诅咒、附身这类超自然力量"),
    ("身体恐怖", "#fb7185", "肉体异变带来的生理不适"),
    ("恐怖喜剧", "#fbbf24", "一边笑一边被吓"),
    ("伪纪录片", "#34d399", "手持镜头 / 找到的录像"),
    ("邪典", "#f472b6", "风格强烈、有固定受众群"),
]

WORK_TYPES = [
    ("纯音乐", "#38bdf8", "钢琴 / 弦乐为主的器乐"),
    ("电子", "#a78bfa", "合成器、节拍驱动"),
    ("氛围", "#34d399", "Ambient / 声音景观"),
    ("影视配乐", "#fbbf24", "为画面服务的音乐"),
]

SKILLS = [
    ("Python", "#34d399", "后端与自动化"),
    ("音乐制作", "#a78bfa", "编曲、混音入门"),
    ("写作", "#fbbf24", "影评与随笔"),
]

MOVIES = [
    dict(
        title="闪灵",
        original_title="The Shining",
        year=1980,
        director="斯坦利·库布里克",
        country="美国 / 英国",
        rating=9.2,
        verdict="恐怖片的天花板，看完之后酒店的走廊花纹会跟着你回家。",
        review=(
            "库布里克把「空旷」本身变成了恐惧源。全景酒店那么大，人那么少，"
            "镜头永远贴着地面跟着丹尼的三轮车滑行，地毯的花纹像是有生命的图案。\n\n"
            "最厉害的地方是它几乎不用 jump scare。真正的压迫感来自声音设计——"
            "那种低频的嗡鸣、空房间里的回声、突然的安静。"
            "杰克·尼科尔森的表演是往失控方向一路加速的，你从第一帧就知道这个人会崩，"
            "但你不知道崩在哪一秒。\n\n"
            "库布里克版和斯蒂芬·金原著的差异很大，金本人不喜欢这版。"
            "我站库布里克：电影不需要忠于小说，它需要忠于自己的恐惧逻辑。"
        ),
        scare_level=3,
        recommend_level=5,
        genre="心理惊悚",
        tags=["经典", "库布里克", "心理压迫", "斯蒂芬·金改编"],
        watched_at="2023-11-02",
    ),
    dict(
        title="遗传厄运",
        original_title="Hereditary",
        year=2018,
        director="阿里·艾斯特",
        country="美国",
        rating=8.8,
        verdict="家庭创伤被拍成了诅咒，后半段会让你生理性不适。",
        review=(
            "很多人把它当鬼片看，其实它讲的是「你无法选择你的家人」。"
            "开头的葬礼、母亲安妮做的那些微缩模型——模型就是整个电影的隐喻："
            "所有人都是摆件，被看不见的手摆到指定位置。\n\n"
            "那场车内的戏是全片最狠的一刀，不是因为画面有多血腥，"
            "而是因为镜头赖在哥哥脸上不走了。他不敢看，观众替他看了。\n\n"
            "缺点是第三幕的信息密度太高，邪教设定一股脑倒出来，"
            "前面精心堆的家庭剧质感被冲淡了一些。即便如此，它仍然是近十年最好的恐怖片之一。"
        ),
        scare_level=5,
        recommend_level=4,
        genre="心理惊悚",
        tags=["A24", "家庭创伤", "高分", "细思极恐"],
        watched_at="2024-03-18",
    ),
    dict(
        title="逃出绝命镇",
        original_title="Get Out",
        year=2017,
        director="乔丹·皮尔",
        country="美国",
        rating=8.6,
        verdict="披着恐怖片外衣的社会讽刺，越想越冷。",
        review=(
            "皮尔的处女作，厉害在它把「微歧视」具象化了。"
            "白人 Liberal 一家表面上无比友好，越界的方式全在细节里："
            "爸爸不停说「my man」，聚会上的人摸他的肌肉、问他的身体数据。\n\n"
            "「沉入深渊」（Sunken Place）是这些年最精准的恐怖意象——"
            "你意识清醒，但身体失控，只能看着自己被接管。这个比喻太准了。\n\n"
            "结尾的反转在二刷时更好看，因为你开始注意第一幕里所有看似无害的对话，"
            "每一句都是伏笔。"
        ),
        scare_level=2,
        recommend_level=5,
        genre="恐怖喜剧",
        tags=["社会隐喻", "反转", "乔丹·皮尔", "入门友好"],
        watched_at="2023-08-09",
    ),
    dict(
        title="咒怨",
        original_title="呪怨 Ju-On: The Grudge",
        year=2002,
        director="清水崇",
        country="日本",
        rating=7.6,
        verdict="童年阴影制造机，伽椰子的那个声音刻进 DNA 了。",
        review=(
            "J 恐怖的巅峰之一。清水崇把规则写得极简：进了那栋房子就会被诅咒带走，"
            "没有原因，没有解法，不讲道理。正是这种「无理由」让它比鬼故事更吓人。\n\n"
            "技术上它非常克制——几乎没有配乐，全靠环境音。"
            "那种喉咙里挤出来的咯咯声，配上佐佐木希子苍白的脸和黑长发，"
            "构成了千禧年初最 iconic 的恐怖形象。\n\n"
            "缺点是叙事是分段式的，重复感比较强，第二遍看会疲。"
            "但第一次看，尤其是关灯看，依然稳。"
        ),
        scare_level=5,
        recommend_level=4,
        genre="超自然",
        tags=["日恐", "童年阴影", "清水崇", "氛围党"],
        watched_at="2022-10-31",
    ),
    dict(
        title="异形",
        original_title="Alien",
        year=1979,
        director="雷德利·斯科特",
        country="英国 / 美国",
        rating=9.0,
        verdict="太空不是星空，是没人听见你尖叫的密闭铁盒。",
        review=(
            "它本质是密室杀人片，只是把密室搬到了太空。"
            "诺斯特罗莫号的美术设计是工业感的、脏的、有油污的，"
            "这种「会坏的飞船」质感比后来所有干净的科幻片都可信。\n\n"
            "节奏教科书级别：前四十分钟几乎什么都没发生，靠日常对话建立船员关系，"
            "所以后面每一个人死亡你都有感觉。破胸那场戏之所以经典，"
            "是因为全组人真的不知道会发生什么，演员的惊吓反应是真的。\n\n"
            "雷普利的伟大在于她不是动作英雄，她是靠判断和纪律活下来的。"
        ),
        scare_level=4,
        recommend_level=5,
        genre="身体恐怖",
        tags=["科幻恐怖", "经典", "密闭空间", "雷德利·斯科特"],
        watched_at="2024-01-15",
    ),
    dict(
        title="仲夏夜惊魂",
        original_title="Midsommar",
        year=2019,
        director="阿里·艾斯特",
        country="美国 / 瑞典",
        rating=8.0,
        verdict="全程日光下的恐怖片，看完记得别去瑞典的夏至节。",
        review=(
            "所有画面都在白天、在花田里、在阳光灿烂中发生，"
            "但你会看得浑身发冷。这是艾斯特最反直觉的一次设计："
            "恐怖不需要黑暗。\n\n"
            "开场女主失去全家那场戏是整片的情绪地基，"
            "所以后面她在异教社区里被「接纳」时的崩溃才成立——"
            "她不是被洗脑，她是主动选择了被需要。\n\n"
            "男主这个角色被骂得很惨，但我觉得这正是重点："
            "电影是从一个冷暴力男友的视角展开的，最后他得到的下场是精确的。"
        ),
        scare_level=4,
        recommend_level=4,
        genre="邪典",
        tags=["日光恐怖", "A24", "邪教", "关系隐喻"],
        watched_at="2024-06-21",
    ),
]

WORKS = [
    dict(
        title="凌晨三点的走廊",
        kind="music",
        status="idea",
        summary="把《闪灵》里那种空旷酒店的回声做成一首曲子。",
        notes=(
            "构思：钢琴单音 + 长混响，中间加一层几乎听不清的低频嗡鸣。\n"
            "结构上想模仿酒店走廊的空间感——声音从远到近，再到突然的静音。\n"
            "难点是怎么让「静音」本身变成乐器，而不是单纯地停。"
        ),
        bpm=62,
        key_signature="Am",
        wtype="氛围",
        tags=["钢琴", "低频", "空间感"],
        progress=25,
    ),
    dict(
        title="心跳渐快（片尾曲练习）",
        kind="music",
        status="demo",
        summary="练习用 BPM 递增制造焦虑感，目标是一首 90 秒的片尾曲。",
        notes=(
            "已有一版 30 秒小样：从 60 BPM 涨到 132 BPM，"
            "每一段加一层打击乐。\n"
            "待解决：中段缺少一个记忆点，目前只是节奏在变，旋律没有钩子。"
        ),
        bpm=132,
        key_signature="Dm",
        wtype="电子",
        tags=["节拍", "焦虑", "片尾曲"],
        progress=45,
    ),
    dict(
        title="雨夜便利店",
        kind="music",
        status="idea",
        summary="Lo-fi + 环境采样，讲一个深夜便利店的场景。",
        notes=(
            "采样清单：收银提示音、冰柜嗡鸣、雨打雨棚、远处摩托车。\n"
            "和声想用大量 9 和弦制造湿漉漉的感觉。\n"
            "还没决定要不要加人声。"
        ),
        bpm=78,
        key_signature="Fmaj7",
        wtype="纯音乐",
        tags=["Lo-fi", "采样", "夜景"],
        progress=10,
    ),
    dict(
        title="主题动机：三个音",
        kind="music",
        status="demo",
        summary="只用三个音发展出一段 2 分钟的配乐，练极简写作。",
        notes=(
            "动机：下行小二度 + 上行纯四度。\n"
            "已完成 A 段的弦乐编排，B 段想转到关系大调再拉回来。\n"
            "这个练习的价值在于逼自己不用和弦填充。"
        ),
        bpm=96,
        key_signature="Cm",
        wtype="影视配乐",
        tags=["极简", "弦乐", "动机发展"],
        progress=60,
    ),
]

INTERESTS = [
    dict(
        title="恐怖电影",
        icon="🎬",
        description="从心理惊悚到身体恐怖都看，尤其喜欢靠氛围而不是靠音效吓人的那种。看完会写一篇评价。",
        link="movies.html",
        accent="#fb7185",
    ),
    dict(
        title="音乐构思",
        icon="🎧",
        description="把画面和情绪翻译成声音。目前主要在写主题动机和氛围片段，慢慢攒成完整的曲子。",
        link="works.html",
        accent="#a78bfa",
    ),
    dict(
        title="写代码",
        icon="💻",
        description="用 Python 把想法落成能跑的东西。比起炫技，更在意它是不是真的有用。",
        link="",
        accent="#34d399",
    ),
    dict(
        title="写东西",
        icon="✍️",
        description="影评、随笔、零散的想法。写下来才算真的想过一遍。",
        link="",
        accent="#fbbf24",
    ),
]

PROFILE = dict(
    name="Ballball",
    headline="把想法做成东西的人",
    tagline="在恐怖片里找灵感，在音乐里找节奏，在代码里把它们落地。",
    avatar="",
    bio=(
        "我是一个喜欢把「喜欢」做成实物的人。\n\n"
        "白天写代码，晚上看恐怖片，中间的空档用来想旋律。"
        "我不太相信「灵感」这个说法，更相信量变——"
        "看完一百部片才能说得出哪一部好在哪，写完三十段动机才知道自己喜欢什么和声。\n\n"
        "这个站点就是我的存档：看过的电影和我对它们的判断，"
        "还没做完的音乐构思，以及接下来想做的东西。"
        "电影下面开放了评论区，欢迎直接反驳我的评分。"
    ),
    location="中国",
    email="",
    links=[
        {"label": "GitHub", "url": "https://github.com/Ballballler"},
        {"label": "邮箱", "url": "mailto:hello@example.com"},
    ],
    highlights=[
        {
            "icon": "🎬",
            "title": "恐怖电影档案",
            "text": "每一部都写了长评，从氛围、节奏到缺陷都记下来。",
        },
        {
            "icon": "🎧",
            "title": "音乐构思",
            "text": "动机、BPM、和声走向——还没做完，但过程都在。",
        },
        {
            "icon": "🛠️",
            "title": "自己做自己维护",
            "text": "这个站从后端到前端都是自己写的，跑在自己的服务器上。",
        },
    ],
)


# 别叫 SKILLS —— 上面第 37 行那个 SKILLS 是「技能分类」（3 元组：名字/颜色/说明）。
# 这是技能项本身（5 元组），两者不是一回事，同名会让分类那处解包失败。
SKILL_ITEMS = [
    ("Python", 85, "语言与框架", "#22d3ee", "后端与自动化脚本的主力语言"),
    ("FastAPI", 78, "语言与框架", "#38bdf8", "这个站点的后端就是它"),
    ("SQLAlchemy", 70, "语言与框架", "#38bdf8", "ORM 与数据建模"),
    ("JavaScript", 75, "语言与框架", "#f59e0b", "原生 JS，不依赖框架"),
    ("CSS / 动画", 80, "语言与框架", "#a78bfa", "液态玻璃与 3D 效果全靠手写"),
    ("HTML", 82, "语言与框架", "#fb7185", "语义化与无障碍"),
    ("Linux / 运维", 65, "工程与部署", "#34d399", "nginx、systemd、备份脚本"),
    ("Git", 72, "工程与部署", "#f97316", "版本管理与回滚"),
    ("Docker", 60, "工程与部署", "#0ea5e9", "多阶段构建，压镜像体积"),
    ("SQL", 70, "工程与部署", "#6366f1", "查询与建模"),
    ("LLM 应用", 72, "数据与 AI", "#8b5cf6", "提示词设计与工具编排"),
    ("数据分析", 65, "数据与 AI", "#a855f7", "把数据整理成能看的结论"),
    ("音乐制作", 68, "音乐与影音", "#ec4899", "编曲、动机发展、混音入门"),
    ("声音设计", 55, "音乐与影音", "#f43f5e", "氛围与采样"),
    ("影评写作", 80, "内容与表达", "#fbbf24", "恐怖片长评"),
    ("技术写作", 75, "内容与表达", "#facc15", "文档与复盘"),
]

RESUME_ITEMS = [
    dict(
        kind="work",
        title="产品与内容负责人",
        org="（示例）某科技团队",
        role="Product & Content",
        location="北京 / 远程",
        start_date="2023.06",
        end_date="",
        current=True,
        summary="负责一条内容产品线的方向与节奏，把「想做的东西」拆成能交付的版本。",
        highlights=[
            "主导从 0 到 1 的内容工具站，后端到前端全部自建",
            "把 AI 能力接进实际流程，而不是做成演示 demo",
            "建立内容审核与数据结构规范，后续维护成本下降明显",
        ],
        tags=["产品", "AI 应用", "全栈"],
        link="",
    ),
    dict(
        kind="work",
        title="内容运营 / 增长",
        org="（示例）某内容平台",
        role="Content Ops",
        location="北京",
        start_date="2021.09",
        end_date="2023.05",
        current=False,
        summary="做内容选题、数据复盘和作者运营，学会了用数字而不是直觉做判断。",
        highlights=[
            "搭建选题到数据的闭环，复盘周期从月度缩短到周度",
            "独立产出多篇长评类内容，形成稳定的读者反馈",
        ],
        tags=["内容", "数据复盘", "运营"],
        link="",
    ),
    dict(
        kind="project",
        title="Hotspot Insight",
        org="个人项目",
        role="独立开发",
        location="本地 / 自部署",
        start_date="2025.03",
        end_date="",
        current=True,
        summary="一个自己写的 FastAPI 工具站：热点拆解、音乐检索、可视化、求职雷达与简历工具。",
        highlights=[
            "全站自研，无前端框架，样式集中在单一设计系统里",
            "用 Docker 多阶段构建压缩镜像体积",
        ],
        tags=["FastAPI", "Python", "自部署"],
        link="",
    ),
    dict(
        kind="education",
        title="数字媒体技术 · 本科",
        org="（示例）某大学",
        role="",
        location="中国",
        start_date="2017.09",
        end_date="2021.06",
        current=False,
        summary="课程覆盖程序设计、视听语言与交互设计，毕业设计做的是影像与声音的交互装置。",
        highlights=[
            "毕业设计把声音可视化与互动投影结合，校内展出",
        ],
        tags=["数字媒体", "交互设计"],
        link="",
    ),
    dict(
        kind="award",
        title="校内创意作品展 · 入围",
        org="（示例）某大学",
        role="",
        location="中国",
        start_date="2021.05",
        end_date="2021.05",
        current=False,
        summary="声音可视化互动装置入选年度作品展。",
        highlights=[],
        tags=["声音", "装置"],
        link="",
    ),
]


def seed_if_empty() -> None:
    """数据库为空时灌入初始内容；已有库缺哪张表就补哪张表。"""
    with SessionLocal() as db:
        # 页面区块先补：无论库空不空都要有，前台靠它决定渲染哪些区块
        ensure_default_page_sections(db)
        if db.query(Movie).count() or db.query(Profile).count():
            _seed_resume_and_skills(db)
            return

        cats: dict[str, dict[str, Category]] = {}
        for kind, rows in (
            ("movie_genre", MOVIE_GENRES),
            ("work_type", WORK_TYPES),
            ("skill", SKILLS),
        ):
            cats[kind] = {}
            for idx, (name, color, desc) in enumerate(rows):
                cat = Category(
                    kind=kind,
                    name=name,
                    slug=name,
                    color=color,
                    description=desc,
                    sort_order=idx,
                )
                db.add(cat)
                db.flush()
                cats[kind][name] = cat
        # 兴趣分类也建一份，方便后台继续扩展
        for idx, item in enumerate(INTERESTS):
            cat = Category(
                kind="interest",
                name=item["title"],
                slug=item["title"],
                color=item["accent"],
                description=item["description"],
                sort_order=idx,
            )
            db.add(cat)

        for idx, m in enumerate(MOVIES):
            cat = cats["movie_genre"].get(m.pop("genre", ""))
            db.add(Movie(**m, category_id=cat.id if cat else None, sort_order=idx))

        for idx, w in enumerate(WORKS):
            cat = cats["work_type"].get(w.pop("wtype", ""))
            db.add(Work(**w, category_id=cat.id if cat else None, sort_order=idx))

        for idx, it in enumerate(INTERESTS):
            db.add(Interest(**it, sort_order=idx))

        db.add(Profile(id=1, **PROFILE))
        db.commit()
        _seed_resume_and_skills(db)


# 成长路径的种子。每一步只回答三个问题：当时卡在哪、我怎么走的、得到了什么。
# 这是模板不是履历 —— 请在后台把它们改成你自己那几步，改完这段话的说服力才成立。
JOURNEY_STEPS = [
    {
        "stage": "start",
        "title": "从「看懂它到底怎么跑起来的」开始",
        "when": "起点",
        "stuck": "只会照着教程敲，东西一跑通就到此为止。合上教程，我其实说不清自己刚才做了什么。",
        "action": "开始逼自己把每一步拆开写下来：这一步输入什么、输出什么、为什么会这样。写不出来就说明没真懂，回头重看。",
        "gained": "一套「先拆再动手」的习惯。后来面对任何新东西，第一反应不再是找教程，而是先画出它的数据流。",
        "evidence": "现在写任何东西之前，先有一张草图。",
    },
    {
        "stage": "turn",
        "title": "第一次把想法做成别人能打开的东西",
        "when": "第一个转折点",
        "stuck": "本地跑得很好，但没法给别人看。每次演示都要开远程、开 IDE、解释为什么端口又变了。",
        "action": "咬牙把部署这条链走完：域名、反向代理、进程守护、备份。中间崩了三次，每次都把过程记下来。",
        "gained": "意识到「做完」和「能被用」之间隔着整整一条工程链。这条链我现在走得通。",
        "evidence": "这台站点本身就是那次之后的产物。",
    },
    {
        "stage": "turn",
        "title": "在恐怖片里找到了结构感",
        "when": "第二个转折点",
        "stuck": "一直把看片当消遣，看完就忘。写东西时也总被人说「有感觉但没结构」。",
        "action": "开始带着问题看片：它怎么铺、在哪一处收、留白留多久。看完写一句话，逼自己说清楚它到底做了什么。",
        "gained": "一套可迁移的节奏感。后来写方案、排功能、甚至安排一首曲子的段落，用的都是同一套判断。",
        "evidence": "恐怖电影档案里每部片子下面那一句短评。",
    },
    {
        "stage": "now",
        "title": "把音乐和代码放在同一张桌子上",
        "when": "现在",
        "stuck": "两个兴趣一直是分开的：白天写工程，晚上想曲子，彼此不搭理，两边都停在「还行」的程度。",
        "action": "开始把它们往一起拧 —— 用写工程的方式记创作笔记（结构、动机、未完成的部分），用听曲子的方式看代码节奏。",
        "gained": "发现两者其实是同一件事的两种表达：都是在有限约束里安排结构。这个发现让我两边都往前走了一点。",
        "evidence": "音乐构思那几页，和恐怖片档案那几页，是同一套方法写出来的。",
    },
    {
        "stage": "next",
        "title": "下一步：做一个真的会被别人用起来的东西",
        "when": "下一步",
        "stuck": "目前做的东西都还只服务于我自己。自己既是作者又是唯一用户，很容易把「我觉得好」当成「好用」。",
        "action": "准备把它开放出去，让真实的反馈进来 —— 包括那些不好听的。",
        "gained": "还没走到，但方向清楚了：从「我做了什么」转向「谁因此省了事」。",
        "evidence": "",
    },
]

def _seed_journey(db) -> None:
    """成长路径单独补：老库升级时这一块是新增的，不能因为库不空就跳过。"""
    if db.query(JourneyStep).count() == 0:
        for idx, step in enumerate(JOURNEY_STEPS):
            db.add(JourneyStep(**step, sort_order=idx))
        db.commit()


def _seed_resume_and_skills(db) -> None:
    """简历与技能单独判断，旧库升级时也能补上这两块。"""
    if db.query(SkillItem).count() == 0:
        for idx, (name, level, group, color, note) in enumerate(SKILL_ITEMS):
            db.add(
                SkillItem(
                    name=name,
                    level=level,
                    group=group,
                    color=color,
                    note=note,
                    sort_order=idx,
                )
            )
    if db.query(ResumeItem).count() == 0:
        for idx, item in enumerate(RESUME_ITEMS):
            db.add(ResumeItem(**item, sort_order=idx))
    db.commit()
    _seed_journey(db)
