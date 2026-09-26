# Ballball 的主页

一个从后端到前端都自己写的个人站点：**自我介绍开场 → 简历 → 恐怖电影档案（开放评论区）→ 音乐构思**，
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
| `/movies.html` | 恐怖电影档案：按分类筛选，点卡片看长评与评论区，支持 `#movie-3` 深链分享 |
| `/works.html` | 音乐构思：按状态筛选，详情含 BPM / 调性 / 创作笔记 / 音频小样 / 评论区 |
| `/admin.html` | 管理后台：概览、关于我、简历经历、技能、兴趣爱好、电影、作品、分类、评论、改口令 |
| `/healthz` | 健康检查（给监控和 nginx 用） |
| `/robots.txt` | 屏蔽 `/admin` 与 `/api/`，指向 sitemap |
| `/sitemap.xml` | 按数据库实际内容生成，含每部电影与作品的深链 |

评论对所有访客开放，只需要填昵称（可留空，默认是「匿名访客」）。
后台需要口令登录，会话 12 小时。

**评论管理**：后台「评论」页可以按状态筛选（全部 / 待审核 / 已公开 / 已隐藏），
每条都显示它挂在哪部电影或哪个作品下面（不是光秃秃的 `#3`）。
默认即发即显；如果被人刷屏，在 `.env` 里设 `COMMENT_MODERATION=1` 重启，
之后新留言会先扣下来，审核通过才公开——待审数量会显示在侧边栏和概览页上。

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
| `COMMENT_RATE_LIMIT` | `10` | 同一 IP 在窗口期内的评论上限 |
| `COMMENT_RATE_WINDOW` | `600` | 限流窗口（秒） |
| `COMMENT_MODERATION` | `0` | 设为 `1` 开启先审后发：留言要在后台点「通过」才公开 |
| `SITE_URL` | `http://127.0.0.1:8800` | 站点对外地址，sitemap 与分享卡用它拼绝对 URL。**部署后必改** |
| `MAX_UPLOAD_BYTES` | `8388608` | 单张上传图片的上限（8MB） |
| `TRUST_PROXY` | `1` | 是否信任 `X-Forwarded-For`。**不挂反向代理时请设为 0** |

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
- [ ] 没有挂在反向代理后面时，`TRUST_PROXY=0`
- [ ] `data/` 目录不在静态目录里，无法被公网下载
- [ ] 换过头像 / 名字之后重跑过 `deploy/make_brand_assets.py`，分享卡是新的

---

## 五、数据放在哪

```
data/
├── site.db       # 所有内容：profile / category / interest / movie / work
│                 #           / resume_item / skill_item / comment
└── admin.json    # 管理口令的 PBKDF2 散列（不含明文）

static/uploads/   # 后台传上来的图片（数据库里只存路径，备份别漏了这个目录）
```

备份就是备份上面这些。SQLite 开了 WAL，热拷贝前建议走一次检查点，
`deploy/backup.sh` 已经处理好了，并且会把 `static/uploads/` 一起同步。

---

## 六、目录结构

```
app/
├── config.py        环境变量、密钥、限流、上传与站点地址配置
├── database.py      引擎与会话（SQLite 开 WAL + 外键），含后加列的自动升级
├── models.py        8 张表：profile / category / interest / movie / work
│                    / resume_item / skill_item / comment
├── schemas.py       Pydantic 请求与响应模型
├── security.py      口令散列、会话签名、IP 哈希
├── assets.py        css/js 指纹（给 HTML 里的引用注入 ?v=内容哈希）
├── seed.py          初始示例内容
├── main.py          应用入口、页面路由、robots.txt / sitemap.xml
└── routers/
    ├── public.py    前台只读接口
    ├── comments.py  匿名评论（含限流与先审后发）
    ├── admin.py     后台增删改查 + 图片上传 + 评论审核
    └── deps.py      管理员鉴权依赖
static/
├── index.html  resume.html  movies.html  works.html  admin.html
├── favicon.svg            标签页图标（矢量，可手改）
├── favicon.ico            老浏览器兜底（脚本生成）
├── apple-touch-icon.png   添加到手机主屏（脚本生成）
├── og-image.png           分享卡大图（脚本生成）
├── uploads/               后台上传的图片
├── css/    fonts.css（自托管字体）base.css（令牌/背景氛围）glass.css（玻璃 + 3D 球）
│           pages.css  resume.css（时间轴与打印样式）admin.css
├── fonts/  chakra-petch-{500,600,700}.woff2  jetbrains-mono-{400,700}.woff2
└── js/     common.js（请求/动画/评论区/卡片）sphere.js（3D 标签球）
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

- 评论限流存在进程内存里。**多 worker 部署时每个进程各算一份**，
  要严格限流就改到 Redis，或干脆用 `--workers 1`。
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
