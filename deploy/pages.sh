#!/usr/bin/env bash
# 把站点导出成静态站，并推送到 gh-pages 分支。
#
# 为什么必须本地导出：GitHub Pages 不会运行 Python，Action 里也没有你的数据库
# （data/site.db 被 .gitignore 挡着，本来就不该进仓库）。所以内容是本地拍快照、
# 产物推上去 —— 这也是静态博客的标准做法。
#
# 用法：
#   ./deploy/pages.sh                        # 用默认远端 origin / 默认域名
#   ./deploy/pages.sh --remote git@github.com:Ballballler/ballball-site.git
#   SITE_URL=https://ballballler.github.io/ballball-site ./deploy/pages.sh
# 推送时 Git 会用默认 SSH key。若你的 GitHub key 不是默认名
# （比如 id_ed25519_hotspot），先告诉 Git 用哪一把：
#   export GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519_hotspot"
# 长期方案是写 ~/.ssh/config 的 Host github.com 段。
set -euo pipefail

cd "$(dirname "$0")/.."

REMOTE="${REMOTE:-origin}"
BRANCH="gh-pages"
SITE_URL="${SITE_URL:-https://ballballler.github.io/ballball-site}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --remote) REMOTE="$2"; shift 2 ;;
    --branch) BRANCH="$2"; shift 2 ;;
    --site-url) SITE_URL="$2"; shift 2 ;;
    *) echo "不认识的参数：$1"; exit 1 ;;
  esac
done

if [ -x ".venv/Scripts/python.exe" ]; then VP=".venv/Scripts/python.exe"; else VP=".venv/bin/python"; fi
[ -x "$VP" ] || VP="python3"

echo "==> 1/3 导出静态站"
"$VP" tools/export_static.py --out dist --site-url "$SITE_URL"

# 让 Rate 资源也能被 Pages 直接发（下划线开头的目录会被 Jekyll 吞掉）
touch dist/.nojekyll

TMP="$(mktemp -d)"
echo "==> 2/3 组装 ${BRANCH} 分支"
cp -a dist/. "$TMP"/
cd "$TMP"
git init -q
git checkout -q -b "$BRANCH"
git add -A
git -c user.name="Ballballler" -c user.email="Ballballler@users.noreply.github.com" \
  commit -q -m "publish: $(date '+%Y-%m-%d %H:%M') 静态站快照"

echo "==> 3/3 推送到 ${REMOTE} 的 ${BRANCH}"
# 这个临时仓库里没有 origin，必须先补上远端的真实地址。
# REMOTE 既可以传「已有 remote 的名字」（origin），也可以直接传 URL。
cd - >/dev/null
REMOTE_URL="$(git remote get-url "$REMOTE" 2>/dev/null || echo "$REMOTE")"
cd "$TMP"
git remote add origin "$REMOTE_URL"
git push --force origin "$BRANCH"

cd - >/dev/null
rm -rf "$TMP"

cat <<EOF

推送完成。第一次部署还需要最后一步：
  GitHub 仓库 → Settings → Pages → Build and deployment
  Source 选「Deploy from a branch」
  Branch 选 ${BRANCH}、目录选 / (root) → Save

一两分钟后就能在 ${SITE_URL} 打开。
之后改内容只要重跑这条脚本：./deploy/pages.sh
EOF
