# 部署到 GitHub Pages

## 先说清楚一件事：Pages 不能跑后端

GitHub Pages **只分发静态文件**。它不会运行 Python，也没有数据库。
而我们这个站原本是 FastAPI + SQLite，所以发到 Pages 之后，**这些东西会失效**：

| 能力 | 自己的服务器 | GitHub Pages |
| --- | --- | --- |
| 浏览首页 / 电影 / 音乐 / 简历 | ✅ | ✅ 正常渲染 |
| 详情弹层、深链 `#movie-3` | ✅ | ✅ 正常 |
| 3D 技能球、唱片旋转 | ✅ | ✅ 正常 |
| 后台登录 `/admin.html` | ✅ | ❌ **没有**（导出时故意不包含，前台也不放入口） |
| 在线发评论 / 上传图片 | — | — 评论功能已整体移除 |
| 后台增删改查内容 | ✅ | ❌ 改完要本地重新导出 |

所以 Pages 版本的定位是：**一个只读的公开展示版**。要改内容，在本地改完重新导出。

> 想要完整能力（后台 + 数据库），还是得有一台自己的服务器，
> 看 `deploy/README.md`（systemd + nginx + HTTPS 那套）。两者不冲突：
> 服务器跑动态全功能版，Pages 跑公开静态版。

## ⚠️ 私有仓库要付费

这是 GitHub 的收费规则，不是我们能绕开的：

- **公开仓库** → Pages **免费**
- **私有仓库** → Pages 需要 **GitHub Pro 及以上**（目前 $4/月）

如果不打算付费，就把仓库建成 Public。代价是源码公开 ——
不过口令散列（`data/admin.json`）和数据库（`data/site.db`）都不在仓库里，
`.gitignore` 已经挡死了，真正公开出去的只有前端代码和部署脚本。

如果确实要私有，两条路：付 $4/月，或者改用自己的服务器（免费额度/VPS 几十块一个月）。

---

## 方案：本地导出 + gh-pages 分支

**为什么不能在 GitHub Actions 里导出？**
因为文章内容在 `data/site.db`，而这个文件被 `.gitignore` 挡着（它含你的个人数据，本来就不该进仓库）。
CI 里没有它，`export_static.py` 只会用空的示例库导出一份假数据 ——
拿假数据覆盖真站点，就是标准的「空壳上线」。所以导出必须在本地做。

流程是：

```
本地 FastAPI + SQLite（唯一数据源，后台在这里改）
        │  python tools/export_static.py
        ▼
     dist/（纯静态快照：HTML 内联了全部数据）
        │  deploy/pages.sh（或 pages.bat）
        ▼
   gh-pages 分支  →  GitHub Pages 自动上线
```

### 导出器做了三件刻意的事

1. **数据用 `TestClient` 调自己的接口取**，不是手写 SQL。
   这样静态快照和线上接口返回的结构天然一致，不会出现「本地好使、Pages 上少字段」。
2. **复用 `app/assets.py` 的指纹**。Pages 会给静态资源上缓存，
   没有 `?v=<hash>` 的话你改了样式、老访客还拿着上个月的文件。
3. **不导出 `admin.html`**。那儿没有后端，登录页只会报错，不如不出现。

---

## 第一次上线（照抄即可）

### 1. 建 GitHub 仓库

去 https://github.com/new 建一个仓库，名字比如 `ballball-site`。
按上面的付费规则选 Public / Private。

### 2. 配上 remote 并推送源码

```bash
cd D:/ballball-site
git remote add origin git@github.com:Ballballler/ballball-site.git
git push -u origin main
```

**验证**：`git ls-remote --heads origin main` 能列出分支。

**常见失败**：`Permission denied (publickey)` —— 加到 GitHub 的那把 key 叫
`id_ed25519_hotspot`，不是 Git 默认会尝试的 `id_rsa` / `id_ed25519`，所以必须告诉 SSH
用哪把。在 `~/.ssh/config` 里写一段：

```
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_hotspot
    IdentitiesOnly yes
```

或者临时指定：`export GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519_hotspot"`。
临时方式只对当前终端有效，而且 `deploy/pages.sh` 是在另一个临时目录里执行 push 的，
只配 `core.sshCommand` 会失效 —— 长期用还是写 config 最省事。

### 3. 导出并推送静态产物

```bash
./deploy/pages.sh                     # Git Bash / macOS / Linux
deploy\pages.bat                      # Windows 双击
```

脚本会：导出到 `dist/` → 在临时目录建一个只有静态产物的 `gh-pages` 分支 → force push。

**常见失败**：
- `Repository not found` → 第 2 步的 remote 没配对，或仓库是私有但 SSH key 没权限；
- 挂代理的话 force push 可能超时，走 SSH 而不用 HTTPS 会稳一些。

### 4. 打开 Pages

仓库 → **Settings → Pages** → Build and deployment

- Source：`Deploy from a branch`
- Branch：`gh-pages` / 目录 `/ (root)`
- Save

等 1～2 分钟，Settings → Pages 顶部会显示线上地址。

**验证**：`curl -I https://ballballler.github.io/ballball-site/` 返回 200；
打开首页能看到自己的名字和卡片（不是空白）。

**常见失败**：页面出来是 404 → 多半是 Branch 选成了 main 或者目录选了 `/docs`。

### 5. 绑定自己的域名（可选）

Pages 设置页的 **Custom domain** 填你的域名，然后在域名商那边加一条 CNAME：

```
yourdomain.com   CNAME   ballballler.github.io
```

勾上 **Enforce HTTPS**（证书 GitHub 自己签发，约 10 分钟生效）。
域名生效后记得把 `SITE_URL` 换掉再导出一次，否则 sitemap 里还是旧地址。

---

## ⚠️ 子路径陷阱（踩过，务必知道）

站点地址是 `https://<用户名>.github.io/<仓库名>/` —— **多一层子路径**。
普通网站跑在根目录，这里不是。后果：

**以 `/` 开头的地址会 404。** 比如 `/uploads/2026-09/x.mp3` 会被解析成
`https://<用户名>.github.io/uploads/2026-09/x.mp3`（根域名下没这个文件），
正确的地址是 `https://<用户名>.github.io/<仓库名>/uploads/2026-09/x.mp3`。

表现很有迷惑性：**页面看着完全正常，点播放却毫无反应** ——
因为 HTML 里的 css/js 一直用相对路径（`js/home.js`）没事，
出事的只有数据库里那些「上传后存下来的地址」（`audio_url` / `avatar` / `cover`）。

已修在 `tools/export_static.py` 的 `_relativize_local_urls()`：导出时把这些字段
开头的 `/` 去掉，让它们跟着当前页面走。**TMDB 的 https 外链不动**（绝对地址本来就没问题）。

**验证时必须在子路径下跑**，不能只测 `http://127.0.0.1:8899/works.html`：

```bash
mkdir -p /tmp/ghsim/ballball-site && cp -a dist/. /tmp/ghsim/ballball-site/
cd /tmp/ghsim && python -m http.server 8899 &
node check_static.js "http://127.0.0.1:8899/ballball-site"
```

`check_static.js` 里有条断言会用 `new Audio()` 真拉一次音频元数据 ——
**别删它**。光断言「`<audio>` 元素存在」是抓不到这个 bug 的。

## ⏱ HTML 会被缓存 10 分钟

Pages 对 HTML 固定发 `Cache-Control: max-age=600`（改不了）。
所以推完代码立刻打开页面，**可能还是旧内容**，等一会儿或强刷（Ctrl+F5）才更新。

导出时会写一份 `build.json`（只含一个 `built_at` 时间戳）并内联进页面，
`common.js` 的 `initStaleCheck()` 启动时比对一次：发现本地这份是旧的，
就弹一条「有新版本，点这里刷新」的提示条。只在静态站里生效，本地开发不打扰。

排查「改了内容线上没变」时，**先确认不是缓存**，再去怀疑代码：

```bash
curl -s https://<用户名>.github.io/<仓库名>/build.json   # 看线上构建时间
```

## 日常更新流程

1. 本地起服务：`.venv\Scripts\python.exe run.py --port 8800`
2. 进 `http://127.0.0.1:8800/admin.html` 改内容
3. 跑 `deploy/pages.sh`（或 `pages.bat`）
4. 一两分钟后 Pages 生效（HTML 另有最多 10 分钟缓存，见上一节）

**改了 CSS/JS 也要重新跑导出** —— 导出会把代码一起打进产物里。

## 上线检查清单

- [ ] 首页能打开，名字/简介是自己填的（不是示例数据）
- [ ] 电影页、音乐页的卡片都在，且**数量对得上后台**
- [ ] 点卡片能弹出详情（居中、有关闭按钮）
- [ ] **音频能真的播放**（不是只看得到播放器）—— 见「子路径陷阱」
- [ ] 简历页时间轴、技能球正常
- [ ] `sitemap.xml` 里的域名是你自己的
- [ ] `https://…/admin.html` 是说明页、带 noindex（后台没被传上去）
- [ ] 在仓库源码里搜不到 `admin.json` / `site.db`（`git log -p -- .gitignore` 之外）

## 回滚

静态站每次导出都是一份完整快照，回滚就是把旧产物推回去：

```bash
git log gh-pages          # 找上一个「publish:」提交
git push --force origin <那个commit>:gh-pages
```

也可以在 Settings → Pages 里临时把 Branch 切回 main 让站点下线。
