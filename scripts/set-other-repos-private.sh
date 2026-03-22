#!/usr/bin/env bash
# 将 GitHub 用户 Kikiero 下除 workspace-trader 外的仓库设为 private。
#
# 用法（在本机终端，勿把 token 写进仓库或提交）:
#   export GITHUB_TOKEN=ghp_xxxxxxxx   # Fine-grained 或 classic，需含修改仓库权限
#   ./scripts/set-other-repos-private.sh
#
# 依赖: curl, jq（brew install jq）
#
# 注意:
# - 从「公开仓库」fork 出来的仓库，GitHub 可能不允许改为 private，需先在网页上
#   了解政策或考虑 duplicate / detach fork。
# - 本脚本仅处理当前 API 能列出的仓库；私有仓库需 token 才能列出。

set -euo pipefail

OWNER="Kikiero"
KEEP_PUBLIC="workspace-trader"

if [[ -z "${GITHUB_TOKEN:-}" ]]; then
  echo "请设置环境变量 GITHUB_TOKEN（GitHub Settings → Developer settings → Personal access tokens）" >&2
  exit 1
fi

if ! command -v jq &>/dev/null; then
  echo "需要安装 jq: brew install jq" >&2
  exit 1
fi

echo "正在获取 ${OWNER} 的仓库列表..."
page=1
names=()
while true; do
  resp=$(curl -sS -H "Authorization: Bearer ${GITHUB_TOKEN}" \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "https://api.github.com/user/repos?per_page=100&page=${page}&affiliation=owner")
  count=$(echo "$resp" | jq 'length')
  if [[ "$count" -eq 0 ]]; then
    break
  fi
  while IFS= read -r n; do
    names+=("$n")
  done < <(echo "$resp" | jq -r '.[].name')
  if [[ "$count" -lt 100 ]]; then
    break
  fi
  page=$((page + 1))
done

if [[ ${#names[@]} -eq 0 ]]; then
  echo "未获取到任何仓库（检查 token 权限是否为 repo / 完整仓库访问）。" >&2
  exit 1
fi

echo "将处理以下仓库（跳过保留公开的 ${KEEP_PUBLIC}）:"
for repo in "${names[@]}"; do
  [[ "$repo" == "$KEEP_PUBLIC" ]] && continue
  echo "  - $repo"
done

read -r -p "确认将上述仓库设为 private? [y/N] " ok
[[ "$ok" =~ ^[yY]$ ]] || { echo "已取消。"; exit 0; }

for repo in "${names[@]}"; do
  if [[ "$repo" == "$KEEP_PUBLIC" ]]; then
    echo "[跳过] $repo — 保留为当前策略下的公开项目"
    continue
  fi
  echo "[PATCH] ${OWNER}/${repo} -> private"
  code=$(curl -sS -o /tmp/gh_patch_body.json -w "%{http_code}" -X PATCH \
    -H "Authorization: Bearer ${GITHUB_TOKEN}" \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "https://api.github.com/repos/${OWNER}/${repo}" \
    -d '{"private":true}')
  if [[ "$code" == "200" ]]; then
    echo "  OK"
  else
    echo "  失败 HTTP $code — 内容:" >&2
    cat /tmp/gh_patch_body.json >&2
    echo "" >&2
  fi
done

echo "完成。请到 https://github.com/${OWNER}?tab=repositories 核对。"
