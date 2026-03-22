# OpenClaw 连接飞书（Feishu / Lark）

本机已安装官方插件 **`@openclaw/feishu`**（目录：`~/.openclaw/extensions/feishu`）。接下来需要你在**飞书开放平台**创建应用并写入凭证。

> 官方完整文档（随插件附带）：`~/.openclaw/extensions/feishu/node_modules/openclaw/docs/zh-CN/channels/feishu.md`  
> 在线同类说明：<https://open.feishu.cn/app>（国内飞书） / <https://open.larksuite.com/app>（Lark 国际版）

---

## 一、飞书侧（必做）

1. 打开 [飞书开放平台](https://open.feishu.cn/app) → **创建企业自建应用**。
2. 在 **凭证与基础信息** 复制 **App ID**、**App Secret**（勿泄露）。
3. **权限管理**：按文档批量导入机器人所需权限（含 `im:message`、`im:message:send_as_bot` 等）。
4. **应用能力** → 打开 **机器人**。
5. **事件订阅**：选择 **使用长连接接收事件**，订阅 **`im.message.receive_v1`**。  
   - 需先在本机 **启动 OpenClaw 网关**，否则长连接可能保存失败。
6. **版本管理与发布**：创建版本并**发布**（企业内审批通过）。

国际版 Lark：在 OpenClaw 配置里设置 `channels.feishu.domain` 为 `"lark"`（见下文）。

---

## 二、OpenClaw 侧（二选一）

### 方式 A：命令行（推荐）

```bash
openclaw channels add
```

按提示选择 **Feishu**，粘贴 **App ID** 与 **App Secret**。

### 方式 B：编辑 `~/.openclaw/openclaw.json`

在 `channels` 下增加（**把占位符换成你的真实凭证**；勿把含密钥的文件提交到 Git）：

```json
"feishu": {
  "enabled": true,
  "dmPolicy": "pairing",
  "domain": "feishu",
  "accounts": {
    "main": {
      "appId": "cli_xxxxxxxx",
      "appSecret": "xxxxxxxx",
      "botName": "你的机器人名"
    }
  }
}
```

Lark 国际版示例：将 `"domain": "feishu"` 改为 `"lark"`（或在 `accounts.main` 上覆盖 `domain`）。

也可用环境变量（便于不写进文件）：

```bash
export FEISHU_APP_ID="cli_xxx"
export FEISHU_APP_SECRET="xxx"
```

---

## 三、启动网关与配对

```bash
openclaw gateway restart
# 或
openclaw gateway
```

在飞书里打开机器人，**发一条消息**。默认私聊策略为 **pairing**：机器人会发配对码，在本机执行：

```bash
openclaw pairing approve feishu <配对码>
```

查看待配对：

```bash
openclaw pairing list feishu
```

---

## 四、常见问题

| 现象 | 处理 |
|------|------|
| 长连接保存失败 | 先 `openclaw gateway` 保持运行，再回开放平台保存事件订阅 |
| 群聊不回复 | 默认需 **@机器人**；把机器人拉进群并 @ |
| 收不到消息 | 检查应用已发布、权限齐全、事件为 `im.message.receive_v1`、网关已启动 |
| 安装后提示重启 | 执行 `openclaw gateway restart` |

---

## 五、与本交易工作区联动

飞书连上后，对话仍由 OpenClaw 网关路由；若要将某群/用户绑定到 `trading-orchestrator` 等 Agent，需在 `openclaw.json` 配置 **`bindings`**（参见官方文档「多 Agent 路由」一节）。

---

**安全提示**：`openclaw.json` 含敏感信息，请勿提交到公开仓库；密钥泄露请在飞书开放平台**重置 App Secret** 并更新配置。
