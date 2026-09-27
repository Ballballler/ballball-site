# 部署手册

目标：把站点跑在一台自己的 Linux 服务器（Ubuntu 22.04 / Debian 12 为例）上，
用 systemd 守护进程 + nginx 反代 + Certbot 上 HTTPS。

下面假设：

- 代码放在 `/srv/ballball`
- 域名是 `example.com`（替换成你自己的）
- 服务监听 `127.0.0.1:8800`，不直接暴露公网

---

## 0. 前置

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip nginx certbot python3-certbot-nginx rsync sqlite3
sudo useradd -r -s /bin/false ballball || true
```

---

## 1. 放代码

```bash
sudo mkdir -p /srv/ballball
sudo chown -R $USER:$USER /srv/ballball
# 本地：rsync -av --exclude '.venv' --exclude 'data' ./ user@server:/srv/ballball/
```

---

## 2. 装依赖

```bash
cd /srv/ballball
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

---

## 3. 写 `.env`

```bash
cat > /srv/ballball/.env <<'EOF'
APP_ENV=production
ADMIN_PASSWORD=换成你自己的强口令
SITE_URL=https://你的域名
# SECRET_KEY 留空会自动生成并写回这个文件，生成后别再动它
EOF
chmod 600 /srv/ballball/.env
```

`SITE_URL` 别漏：`sitemap.xml` 和 `robots.txt` 里的地址都由它拼出来，
不设的话搜索引擎会收到 `http://127.0.0.1:8800` 这种收录不了的地�址。

**验证方式**：`grep -c ADMIN_PASSWORD /srv/ballball/.env` 返回 1，且值不是 `admin12345`。
**常见失败**：把 `.env` 写进了 `data/` 或加了引号导致口令里带引号 —— 别加引号。

---

## 4. systemd 单元

```bash
sudo cp deploy/ballball.service /etc/systemd/system/ballball.service
sudo systemctl daemon-reload
sudo systemctl enable --now ballball
systemctl status ballball --no-pager
```

**验证方式**：`curl -sf http://127.0.0.1:8800/healthz` 返回 `{"status":"ok"}`。
**常见失败**：

- `WorkingDirectory` 写错 → 起不来，看 `journalctl -u ballball -n 50`；
- `.venv` 路径不对 → 报 `No such file or directory`；
- 端口被占用 → 换端口或杀掉占用进程 `sudo ss -lntp | grep 8800`。

**多 worker 说明**：个人站用单 worker 完全够，瓶颈在带宽不在 CPU。

---

## 5. nginx 反代

```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/ballball
sudo sed -i 's/example.com/你的域名/g' /etc/nginx/sites-available/ballball
sudo ln -sf /etc/nginx/sites-available/ballball /etc/nginx/sites-enabled/ballball
sudo nginx -t && sudo systemctl reload nginx
```

**验证方式**：`curl -I http://你的域名/` 返回 200。
**常见失败**：`nginx -t` 报 `conflicting server name` → 说明 default 站点占了同名 server_name，先 `sudo rm /etc/nginx/sites-enabled/default`。

**关于缓存与指纹**：nginx 给 css/js 设了 `expires 30d`，这本身没问题——
后端返回 HTML 时会自动给每个 css/js 的 URL 追加上 `?v=<内容哈希>`
（逻辑在 `app/assets.py`），改过的文件 URL 就变，浏览器必然重新拉取。
所以**不要**在 nginx 里手写版本号，也不要给 HTML 也套长缓存：
HTML 已经带 `Cache-Control: no-cache`，改完内容刷新就能看到。

nginx 没配好、暂时直接用 uvicorn 暴露时，上面这些缓存规则都不生效，
但指纹依然有效（只是白加了个查询串，不影响加载）。

---

## 6. HTTPS

```bash
sudo certbot --nginx -d 你的域名 --agree-tos -m 你的邮箱
sudo systemctl reload nginx
```

证书会自动续期（`systemctl status certbot.timer` 可确认）。

**上线后必做**：HTTP 全站跳 HTTPS 打开之后，把 `app/routers/admin.py` 里
`_set_cookie()` 的 `secure=False` 改成 `secure=True`，然后
`sudo systemctl restart ballball`。否则登录 Cookie 可能在明文连接上传输。

---

## 7. 备份

```bash
sudo cp deploy/backup.sh /usr/local/bin/ballball-backup
sudo chmod +x /usr/local/bin/ballball-backup
sudo mkdir -p /var/backups/ballball

# 手动跑一次
sudo ballball-backup

# 每天凌晨 3 点自动备份
echo "0 3 * * * root /usr/local/bin/ballball-backup" | sudo tee /etc/cron.d/ballball-backup
```

**回滚**：

```bash
sudo systemctl stop ballball
sudo cp /var/backups/ballball/site-YYYYMMDD-HHMM.db /srv/ballball/data/site.db
sudo cp /var/backups/ballball/admin-YYYYMMDD-HHMM.json /srv/ballball/data/admin.json
sudo chown -R ballball:ballball /srv/ballball/data
sudo systemctl start ballball
```

**上传的图片也要一起备份**：数据库只存图片路径，实体文件在
`static/uploads/<年月>/` 下。`deploy/backup.sh` 已把整个目录打包，
但如果你的图很多，单独给它排一条 rsync 到对象存储更省心：

```bash
rsync -a --delete /srv/ballball/static/uploads/ /var/backups/ballball/uploads/
```

---

## 8. 换头像、换名字之后

页面上用的分享卡（微信 / Twitter 分享出去的那张图）和浏览器标签页图标
都是**离线生成的静态文件**，不会自己跟着数据变。改完「关于我」之后重跑一次：

```bash
.venv/bin/pip install pillow            # 只在生成图片时需要
.venv/bin/python deploy/make_brand_assets.py --site http://127.0.0.1:8800
```

脚本会从 `/api/profile` 读你填的名字与一句话身份，生成：

| 文件 | 用途 |
| --- | --- |
| `static/og-image.png` | 分享出去的大图（1200×630） |
| `static/favicon.ico` | 老浏览器的标签页图标 |
| `static/apple-touch-icon.png` | 添加到手机主屏时的图标 |

`static/favicon.svg` 是手写的矢量图标，改配色直接编辑它。
改完页面的 `<title>` / 描述文案之后，再跑一次
`.venv/bin/python deploy/inject_head_meta.py` 把 og 标签重新写进各页。

两个脚本都是幂等的，重复跑只会覆盖同一段。

---

## 9. 更新部署

```bash
cd /srv/ballball
sudo systemctl stop ballball
rsync -av --exclude '.venv' --exclude 'data' --exclude '.env' ./ /srv/ballball/
.venv/bin/pip install -r requirements.txt      # 依赖有变时
sudo chown -R ballball:ballball /srv/ballball
sudo systemctl start ballball
curl -sf http://127.0.0.1:8800/healthz && echo OK
```

**回滚代码**：Git 的话直接 `git checkout <上一个 tag>` 再重启；
没用 Git 就恢复上一份备份目录。

---

## 10. 上线检查清单

- [ ] `curl https://你的域名/healthz` 返回 ok
- [ ] `/` `/movies.html` `/works.html` `/resume.html` 都能打开，无控制台报错
- [ ] `/admin.html` 能用新口令登录，登不进说明 `.env` 没生效
- [ ] 后台改一条电影，刷新前台立刻变化
- [ ] 后台能上传一张图片，且前台显示出来
- [ ] `.env` 里 `SITE_URL` 是真实域名，访问 `/sitemap.xml` 里的链接是绝对地址
- [ ] `/robots.txt` 里 `Sitemap:` 指向自己的域名
- [ ] 浏览器标签页图标是自己的（不是默认地球）
- [ ] 已改 `secure=True` 并重启
- [ ] `journalctl -u ballball -n 20` 里没有默认口令的警告
- [ ] 备份脚本跑通过一次，且 `/var/backups/ballball/` 里有文件
