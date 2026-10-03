# QuantumToken CLI (`qt`)

QuantumToken 平台官方命令行工具：**AI 对话 / 联网问答 / AI 出图 / 网页解析 / 余额查询**，一行命令搞定。零依赖，Windows / macOS / Linux 通吃。

## 安装

```bash
pip install git+https://github.com/boy-373/quantoken-cli.git
```

升级：

```bash
pip install -U git+https://github.com/boy-373/quantoken-cli.git
```

## 快速开始

```bash
# 1. 登录（API Key 在 https://trade.pianam.cn 控制台获取）
qt login qk_xxxxxxxxxxxx

# 2. 查余额
qt balance

# 3. 看模型和价格
qt models
```

## 命令一览

### AI 对话（纯文本，按模型计费 1-10 积分/次）

```bash
qt chat "用一句话介绍量子计算"
qt chat "写个爬虫思路" -m qwen-plus        # 换模型
```

### 智能体问答（自动联网搜索，~5 积分/次起）

```bash
qt ask "北船重工最近有什么新闻？"
qt ask "搜索一下今天 A 股热点板块"
```

### AI 出图（Seedream 5.0 Pro：1.5K=40 积分 / 2K=75 积分）

```bash
qt image "深蓝色夜空下的灯塔，海面波光粼粼，电影感"
qt image "赛博朋克猫咪" --size 2K -o cat.png   # 2K 大图并保存本地
```

### 网页/文本 AI 解析（1-5 积分/次）

```bash
qt extract --url https://example.com/article --question "这篇文章讲了什么？"
qt extract --url https://example.com/job --question "提取职位名、薪资、城市"
```

## API Key 配置方式（二选一）

```bash
qt login qk_xxx                    # 方式1：保存到 ~/.qtcli/config.json
export QUANTOKEN_API_KEY=qk_xxx    # 方式2：环境变量（优先级更高）
```

## 计费说明

**1 元 = 100 积分**，调用失败自动退积分。

| 能力 | 价格 |
|------|------|
| 对话（按模型） | 1 / 2 / 5 / 8 / 10 积分/次 |
| 智能体问答 | 对话积分 + 联网搜索 2 积分 |
| AI 出图 1.5K | 40 积分/张 |
| AI 出图 2K | 75 积分/张 |
| 网页解析 | 1 / 2 / 5 积分/次 |

## 其他接口

- OpenAI 兼容端点：`POST https://site.pianam.cn/api/v1/open/chat/completions`
- 完整 API 文档：https://site.pianam.cn/docs
- MCP Server（给 AI Agent 用）：`https://site.pianam.cn/mcp`
- Python SDK：https://github.com/boy-373/quantoken-sdk

## License

MIT
