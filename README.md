# Ballball 的主页

一个从后端到前端都自己写的个人站点：**自我介绍开场 → 简历 → 恐怖电影档案 → 音乐构思**，
配一个能增删改查所有内容的管理后台。

技术栈：FastAPI + SQLAlchemy + SQLite，前端是原生 HTML / CSS / JS，没有构建步骤。

---

## 设计定调

**方向：暗色轨道星系 —— 「PERSONAL ORBIT」（融合 personal-orbit-v001）。**

在 personal-orbit 的视觉语言上做了两件事：**背景再压暗一档（`#070b12`）**、
**所有发光/高光减半**，保证不晃眼、耐看。

| 项目 | 决策 |
| --- | --- |
| 底色 | 近黑蓝 `#070b12`，玻璃面板走极低透明度的白，不发亮 |
| 强调 | 灰绿 `#8fb8a8`（主）/ 雾紫 `#a495bd` / 珊瑚 `#c79a92`，全部降饱和 |
| 字体 | 系统栈 + JetBrains Mono（HUD 标签、编号、评分） |
| 每个模块一个角色 | 电影=**幽灵 + 幽灵系宝可梦**（耿鬼/迷拟Q/烛光灵，手绘 SVG）<br>音乐=**会转的黑胶唱片**（CSS 生成）<br>经历=**阶梯状成长路径**（一级一级往上爬）<br>首页=**3D 环绕场景**（自我介绍开场） |

三维由两套引擎承担：

- 首页 Hero 的可交互 3D 场景：引入 Three.js + personal-orbit 的 W21 场景
  （`static/vendor/three.min.js`、`creative-runtime.js`、`creative-scenes.js`），
  拖动旋转 / 滑杆开合 / 自动呼吸，浏览器不支持 WebGL 时降级为静态提示、正文不受影响。
- `static/js/sphere.js` —— 自研 3D 技能球（简历页），不依赖 Three.js。

动画系统沿用 personal-orbit：`enter` 入场、`float` 漂浮、`ghost-float` 幽灵、
`record-spin` 唱片、`orbit-glow` 轨道呼吸。`prefers-reduced-motion` 下全部静止。

---

## 一、页面与能力

| 路径 | 说明 |
| --- | --- |
| `/` | 首页：自我介绍开场、3D 环绕轨道、关键词跑马灯、关于我、3D 技能球 + 简历摘要、兴趣、电影与作品预览 |
| `/resume.html` | 简历：自我介绍开场、3D 技能球、分组技能条、教育与经历时间轴（可直接打印成 PDF） |
| `/movies.html` | 恐怖电影档案：按分类筛选，点卡片看长评，支持 `#movie-3` 深链分享 |
| `/works.html` | 音乐构思：按状态和风格筛选，详情含 BPM / 调性 / 创作笔记 / 音频小样，以及后台跑出来的自动分析结果 |
| `/admin.html` | 管理后台：概览、关于我、简历经历、技能、兴趣爱好、电影、作品、分类、改口令（前台不放入口，直接输网址进） |
| `/healthz` | 健康检查（给监控和 nginx 用） |
| `/robots.txt` | 屏蔽 `/admin` 与 `/api/`，指向 sitemap |
| `/sitemap.xml` | 按数据库实际内容生成，含每部电影与作品的深链 |

后台需要口令登录，会话 12 小时。

**图片的自动分析**：后台作品列表每行都有「自动分析」，点一次就会把这首曲子
交给 librosa 跑一遍，算出速度、调性、平均响度、动态范围、频谱重心、起音密度，
外加一条 160 点的波形包络，结果存进 `work.analysis`。前台详情页直接读这个快照，
不关心它是怎么来的 —— 静态托管没有 Python，所以分析只能本地跑完再导出。

```
# 没装依赖也能跑站点，只是按钮会提示「自动分析依赖 librosa」
pip install librosa soundfile
```

几个判断是刻意保守的：

- **测不出就不给数**。合成一张没有节拍的噪声 pad 做验证，librosa 照样能凑出
  一串「节拍」。所以除了看节拍点数量，还要求节拍间隔足够匀、tempogram 上那个
  峰足够突出（实测无节拍素材显著度 2.0，有节拍的在 5 以上，门槛取 3.5）。
  不满足就留空，页面上写「测不出稳定节拍」。
- **不覆盖手写字段**。BPM 和调性只有原本为空时才自动填，你手写的永远优先。
- **mp3 解不开会退回 ffmpeg**，机器上有 ffmpeg 就基本不会走到报错那条分支。

准确性自己验：`python tools/check_analysis.py` 用三份已知答案的合成音频
（120 BPM 点击 / A 大调和弦 / 无节拍 pad）打一遍，**要求 3/3 通过**。

**图片上传**：后台的海报 / 封面 / 头像字段都能直接上传本地图片，
不再只能填外链。文件落在 `static/uploads/<年月>/`，文件名是随机串。

站点的「营业外」内容也一并做了：

- `/robots.txt` 与 `/sitemap.xml` 由后端根据数据库实际内容生成，屏蔽后台与接口；
- 每个页面都有完整的 Open Graph / Twitter 分享卡，分享出去有大图；
- 浏览器标签页图标是自绘的 SVG（`static/favicon.svg`），另有 `.ico` 与
  `apple-touch-icon.png` 兜底老浏览器与手机主屏；
- 后台改内容后**立刻生效**：CSS/JS 的 URL 带内容哈希，HTML 走 `no-cache`，
  不会出现「改了样式访客还是旧版」的经典问题（细节见 `app/assets.py`）。

---

## 二、本地跑起来

项目放在 **`D:\ballball-site`**（英文路径，避开中文+空格的老坑）。

**最简单：双击 `start.bat`** —— 它会自动建虚拟环境、装依赖、起服务、并打开后台。

手动的话：

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python run.py                      # http://127.0.0.1:8800
python run.py --port 9000          # 换端口
```

后台地址：`http://127.0.0.1:8800/admin.html`，默认口令 `admin12345`。

首次启动会自动：

1. 在 `data/site.db` 建表；
2. 灌入初始示例内容（6 部电影 + 4 个音乐构思 + 5 条简历经历 + 16 项技能 + 分类 + 兴趣）；
   **简历里的经历和技能都是示例数据，记得在后台替换成你自己的**；
3. 生成 `SECRET_KEY` 写进 `.env`；
4. 把初始管理口令做成散列存进 `data/admin.json`。

**默认口令是 `admin12345`。** 启动日志会警告，进后台第一件事就是改掉它。

---

## 三、环境变量

全部写在项目根目录的 `.env`（可参考 `.env.example`）。真正的环境变量优先级更高。

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `ADMIN_PASSWORD` | `admin12345` | 只在首次启动时生效，之后以后台改口令为准 |
| `SECRET_KEY` | 自动生成 | 会话 Cookie 的签名密钥，**丢了会导致所有登录态失效** |
| `APP_ENV` | `dev` | 设成 `production` 会关闭 `/api/docs` |
| `DATA_DIR` | `./data` | SQLite 与口令文件的存放目录 |
| `DATABASE_URL` | `sqlite:///data/site.db` | 换 PostgreSQL 只改这一行 |
| `SESSION_TTL_SECONDS` | `43200` | 后台会话有效期（12 小时） |
| `SITE_URL` | `http://127.0.0.1:8800` | 站点对外地址，sitemap 与分享卡用它拼绝对 URL。**部署后必改** |
| `MAX_UPLOAD_BYTES` | `8388608` | 单张上传图片的上限（8MB） |

---

## 四、部署到自己的服务器

详见 [`deploy/README.md`](deploy/README.md)，包含 systemd 单元、nginx 配置、
HTTPS（Certbot）、备份脚本和回滚步骤。最简流程：

```bash
# 1. 上传代码到 /srv/ballball
# 2. 建虚拟环境装依赖
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
# 3. 写 .env（至少设置 ADMIN_PASSWORD、SITE_URL 和 APP_ENV=production）
# 4. 起服务
sudo cp deploy/ballball.service /etc/systemd/system/
sudo systemctl enable --now ballball
# 5. nginx 反代 + Certbot 上 HTTPS
sudo cp deploy/nginx.conf /etc/nginx/sites-available/ballball
```

上线前的安全检查清单：

- [ ] `ADMIN_PASSWORD` 已改成强口令，不再是 `admin12345`
- [ ] `APP_ENV=production`（关闭 API 文档）
- [ ] `SITE_URL` 已改成真实域名，否则 sitemap 里全是 `127.0.0.1`
- [ ] HTTPS 已配置，Cookie 的 `secure` 打开（见 `app/routers/admin.py` 的 `_set_cookie`）
- [ ] `data/` 目录不在静态目录里，无法被公网下载
- [ ] 换过头像 / 名字之后重跑过 `deploy/make_brand_assets.py`，分享卡是新的

---

## 五、数据放在哪

```
data/
├── site.db       # 所有内容：profile / category / interest / movie / work
│                 #           / resume_item / skill_item
└── admin.json    # 管理口令的 PBKDF2 散列（不含明文）

static/uploads/   # 后台传上来的图片（数据库里只存路径，备份别漏了这个目录）
```

备份就是备份上面这些。SQLite 开了 WAL，热拷贝前建议走一次检查点，
`deploy/backup.sh` 已经处理好了，并且会把 `static/uploads/` 一起同步。

---

## 六、目录结构

```
app/
├── config.py        环境变量、密钥、上传与站点地址配置
├── database.py      引擎与会话（SQLite 开 WAL + 外键），含后加列的自动升级
├── models.py        7 张表：profile / category / interest / movie / work
│                    / resume_item / skill_item
├── schemas.py       Pydantic 请求与响应模型
├── security.py      口令散列、会话签名
├── assets.py        css/js 指纹（给 HTML 里的引用注入 ?v=内容哈希）
├── seed.py          初始示例内容
├── main.py          应用入口、页面路由、robots.txt / sitemap.xml
└── routers/
    ├── public.py    前台只读接口
    ├── admin.py     后台增删改查 + 图片上传
    └── deps.py      管理员鉴权依赖
static/
├── index.html  resume.html  movies.html  works.html  admin.html
├── favicon.svg            标签页图标（矢量，可手改）
├── favicon.ico            老浏览器兜底（脚本生成）
├── apple-touch-icon.png   添加到手机主屏（脚本生成）
├── og-image.png           分享卡大图（脚本生成）
├── uploads/               后台上传的图片
├── css/    fonts.css（自托管字体）orbit.css（全站统一主题）
├── fonts/  chakra-petch-{500,600,700}.woff2  jetbrains-mono-{400,700}.woff2
└── js/     common.js（请求/动画/详情弹层/卡片）sphere.js（3D 标签球）
            home.js  resume.js  movies.js  works.js  admin.js
deploy/
├── fetch_fonts.py          拉取自托管字体
├── make_brand_assets.py    生成分享卡与图标（依赖 Pillow，仅生成时需要）
├── inject_head_meta.py     把 og 标签写进各页 <head>
├── backup.sh               SQLite 快照 + 口令 + uploads
├── nginx.conf              nginx 反代（含缓存分层与 SEO 路由）
└── ballball.service        systemd 单元
```

字体是本地自托管的（合计约 90KB），部署后不依赖 Google Fonts。
需要重新拉取或换字体时跑 `python deploy/fetch_fonts.py`。

---

## 七、已知边界

- 音频（音乐小样）还是外链 URL，没做上传。图片已经能在后台上传了，
  音频文件通常几十 MB，建议直接丢对象存储或 CDN 再填 URL。
- 上传只收 jpg / png / webp / gif / avif，**有意不收 SVG**：
  SVG 能内嵌脚本，直接访问文件 URL 就是在同源下执行。图标类资源手写到 `static/` 下。
- sitemap 里的电影 / 作品条目用的是 `#movie-3` 这类锚点深链。
  如果以后给每部电影做独立页面，改 `app/main.py` 的 `sitemap()` 即可。
- 换 PostgreSQL 只需改 `DATABASE_URL`，模型里没有用 SQLite 专有类型。
  （注意 `app/database.py` 里的自动补列只对 SQLite 生效，
  换库时请用正式的迁移工具。）

---

## 八、改数据的安全约定（务必看）

**别让自动化脚本直接删线上库的行。**
2026-09-26 有一轮测试直接打 `127.0.0.1:8800` 的 admin 删除接口，
把 `work` / `skill_item` / `resume_item` 里 id 连续的前几条删掉了
（作品 4→1、技能 16→13、经历 5→3），而播种逻辑是「表空才灌默认值」，
删掉的行不会自己回来。

已经补回，并留下两样东西：

```bash
# 补回被误删的行（只 INSERT OR IGNORE，会先整体备份到 backup/db-restore-<日期>/）
python tools/restore_missing_rows.py --dry-run   # 先看要补什么
python tools/restore_missing_rows.py             # 真跑
```

写测试时请守两条：

1. **要测删除/隐藏，先自己造一条再删它**，不要拿列表第一行开刀。
2. 想跑破坏性用例，把 `DATABASE_URL` 指向临时库（`sqlite:///./data/test.db`）再启服务。

后台口令如果被改过（`data/admin.json` 里有 pbkdf2 散列），
`smoke.js` 后三组后台断言会整体失败——用下面任一种方式告诉它口令：

```bash
SMOKE_ADMIN_PASSWORD='你的口令' node smoke.js
# 或写进 .env：ADMIN_PASSWORD=你的口令
```

忘了口令就删掉 `data/admin.json` 重启，会退回默认 `admin12345`（首页会出警告条，
部署前一定要改掉）。

### 批量导入本地文件当作品

桌面上攒了一堆自己做的小样，想一次性传上来、顺手清掉旧条目时用它：

```bash
.venv/Scripts/python.exe tools/import_two_works.py --dry-run   # 只看计划，不动数据
.venv/Scripts/python.exe tools/import_two_works.py             # 真跑
.venv/Scripts/python.exe tools/import_two_works.py --keep-existing  # 只加不删
```

它做的事：按 `WORKS` 列表校验音频（复用 `_looks_like_audio`，不绕过防线）→
落盘到 `static/uploads/<年月>/` → 建 / 更新作品行 → **删掉本次导入之外的其余作品**。
跑之前自动把 `site.db`（含 -wal/-shm）备份到 `backup/works-import-<日期>/`。
要换文件或改名字，直接改脚本顶部的 `WORKS` 列表 —— 按 `title` 判重，重跑安全。

`.mp4` 这种带视频壳的文件不会被音频白名单收，先抽音轨再传：

```bash
ffmpeg -i input.mp4 -vn -c:a libmp3lame -q:a 2 output.mp3
```

### 恐怖片候选片单（待看 → 打分转正）

电影档案里除了「看过的」正式档案，还有一类 **候选片**（`status='candidate'`）：
别人推荐、还没看的片子。它们在前台电影页单独一栏「02 TO WATCH / 待看的片子」展示，
每张卡上有两个按钮 —— **打分**（打分即看过，自动转正进正式档案）和 **不看**（直接删掉）。

**候选片怎么进来的**：`tools/fetch_horror_candidates.py` 从 TMDB 官网抓真实元数据。

```bash
# 1. 抓元数据（改片单改脚本顶部 SLATE 列表）
.venv/Scripts/python.exe tools/fetch_horror_candidates.py

# 2. 导入电影档案（标成候选）
.venv/Scripts/python.exe tools/import_horror_candidates.py --dry-run
.venv/Scripts/python.exe tools/import_horror_candidates.py
.venv/Scripts/python.exe tools/import_horror_candidates.py --replace  # 清掉旧候选再导
```

导入脚本跟 `import_two_works.py` 一样安全：跑前自动备份 `site.db`、`--dry-run` 不写库、
按 `tmdb_id` 判重（重跑安全）、**绝不碰 `status='watched'` 的正式档案**。

**为什么不用 `app/tmdb.py`**：本机 `api.themoviedb.org` 被网络策略挡住（直连 ReadTimeout、
代理端口未开），httpx 走不通。改用 TMDB 官网自己的前端接口
`www.themoviedb.org/search/remote/movie?query=<片名>&language=zh-CN` ——
返回的 JSON 字段和 v3 API 完全一致，不需要 key。详情页补导演 / 片长 / 中文类型。

⚠️ **非英语片名必须写死 tmdb_id**：搜索接口对这个召回不稳。实测「Exhuma」并到了
`Exhumator`(1300292)、「The Wailing」并到了 `The Stranger`(1413713)，都是完全无关的片子。
所以 `SLATE` 里这类条目写成三元组 `("Exhuma", 2024, 838209)`。

**清理**：后台 `DELETE /api/admin/movies/candidates`（默认只删没打过分的，`keep_rated=false` 全删）。
