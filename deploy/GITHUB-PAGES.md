# 部署到 GitHub Pages

## 先说清楚一件事：Pages 不能跑后端

GitHub Pages **只分发静态文件**。它不会运行 Python，也没有数据库。
而我们这个站原本是 FastAPI + SQLite，所以发到 Pages 之后，**这些东西会失效**：

| 能力 | 自己的服务器 | GitHub Pages |
| --- | --- | --- |
| 浏览首页 / 电影 / 音乐 / 简历 | ✅ | ✅ 正常渲染 |
| 详情弹层、深链 `#movie-3` | ✅ | ✅ 正常 |
| 3D 技能球、唱片旋转 | ✅ | ✅ 正常 |
| 后台登录 `/admin.html` | ✅ | ❌ **没有**（导出时故意不包含） |
| 在线发评论 / 上传图片 | ✅ | ❌ 换成 Giscus（见下） |
| 后台增删改查内容 | ✅ | ❌ 改完要本地重新导出 |

所以 Pages 版本的定位是：**一个只读的公开展示版**。要改内容，在本地改完重新导出。

> 想要完整能力（后台 + 评论 + 数据库），还是得有一台自己的服务器，
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
**常见失败**：`Permission denied (publickey)` → SSH key 没加到 GitHub。
先跑 `ssh -T git@github.com`，应该回 `Hi Ballballler!`。

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

## 评论区：接 Giscus

静态站写不了数据库，评论交给 [Giscus](https://giscus.app) ——
它把评论存在你的 GitHub Discussions 里，访客用 GitHub 账号发言，不需要服务器。

配置一次即可：

1. 仓库 → Settings → **勾选 Discussions**
2. 打开 https://giscus.app 装一下 App（授权给这个仓库即可）
3. 在 giscus.app 页面填仓库名，让它给出 `data-repo-id` 和 `data-category-id`
4. 导出时把这几个值传进环境变量

```bash
export GISCUS_REPO="Ballballler/ballball-site"
export GISCUS_REPO_ID="R_xxxxxxxxxx"
export GISCUS_CATEGORY="Announcements"
export GISCUS_CATEGORY_ID="DIC_xxxxxxxxxx"
./deploy/pages.sh
```

Windows 的话在 `deploy\pages.bat` 同一目录建个 `pages-env.bat` 先 set 好这几个变量，
或者在命令行里先 `set GISCUS_REPO=...` 再跑。

没配置也不影响上线 —— 评论区会显示一句「这是静态导出的只读版本」，历史评论照常展示。

---

## 日常更新流程

1. 本地起服务：`.venv\Scripts\python.exe run.py --port 8800`
2. 进 `http://127.0.0.1:8800/admin.html` 改内容
3. 跑 `deploy/pages.sh`（或 `pages.bat`）
4. 一两分钟后 Pages 生效

**改了 CSS/JS 也要重新跑导出** —— 导出会把代码一起打进产物里。

## 上线检查清单

- [ ] 首页能打开，名字/简介是自己填的（不是示例数据）
- [ ] 电影页 6 张卡、音乐页 4 张卡都在
- [ ] 点卡片能弹出详情（居中、有关闭按钮）
- [ ] 简历页时间轴、技能球正常
- [ ] `sitemap.xml` 里的域名是你自己的
- [ ] `https://…/admin.html` 返回 404（后台没被传上去）
- [ ] 在仓库源码里搜不到 `admin.json` / `site.db`（`git log -p -- .gitignore` 之外）
- [ ] Giscus 配置好之后，评论区能加载出发言框

## 回滚

静态站每次导出都是一份完整快照，回滚就是把旧产物推回去：

```bash
git log gh-pages          # 找上一个「publish:」提交
git push --force origin <那个commit>:gh-pages
```

也可以在 Settings → Pages 里临时把 Branch 切回 main 让站点下线。
