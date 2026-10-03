"""QuantumToken CLI 主入口：qt login/balance/models/chat/ask/image/extract"""
import argparse
import json
import os
import re
import sys

try:  # Windows 控制台中文保护
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from qt_cli import __version__
from qt_cli import client, config
from qt_cli.client import ApiError

# ---------------- 输出工具 ----------------

def _ansi(code):
    return "\033[%sm" % code if sys.stdout.isatty() else ""

C_OK, C_ERR, C_DIM, C_BOLD = _ansi("92"), _ansi("91"), _ansi("90"), _ansi("1")

def ok(msg):
    print("%s%s%s" % (C_OK, msg, _ansi("0")))

def fail(msg, hint=""):
    print("%s%s%s" % (C_ERR, msg, _ansi("0")))
    if hint:
        print("%s%s%s" % (C_DIM, hint, _ansi("0")))

def die(msg, hint="", code=1):
    fail(msg, hint)
    sys.exit(code)

def need_key():
    key = config.get_key()
    if not key:
        die("尚未配置 API Key。", "先执行: qt login <你的key>   （key 在 trade.pianam.cn 控制台获取）")
    return key

# ---------------- 子命令 ----------------

def cmd_login(args):
    key = (args.key or "").strip()
    if not key:
        try:
            key = input("粘贴 API Key (qk_ 开头): ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            die("已取消")
    if not key:
        die("key 不能为空")
    status, data = client.request("GET", "/api/v1/open/me", key)
    if status != 200:
        die("key 校验失败: %s" % _err(data), "请到 trade.pianam.cn 控制台核对 key")
    conf = config.load()
    conf["api_key"] = key
    config.save(conf)
    bal = data.get("balance", "?")
    ok("登录成功，key 已保存到 %s" % config.CONF_FILE)
    ok("当前余额: %s 积分 (key %s)" % (bal, config.mask(key)))

def cmd_logout(args):
    conf = config.load()
    conf.pop("api_key", None)
    config.save(conf)
    ok("已清除本地保存的 key（环境变量 QUANTOKEN_API_KEY 不受影响）")

def cmd_balance(args):
    key = need_key()
    status, data = client.request("GET", "/api/v1/open/me", key)
    if status != 200:
        die(_err(data), "执行 qt login 重新配置 key")
    bal = data.get("balance", "?")
    if isinstance(bal, (int, float)):
        bal = "%.2f" % bal
    ok("剩余积分: %s" % bal)
    email = data.get("email") or data.get("username")
    if email:
        print("%s账号: %s%s" % (C_DIM, email, _ansi("0")))

def cmd_models(args):
    key = need_key()
    status, data = client.request("GET", "/api/v1/open/models?site=api", key)
    if status != 200:
        die(_err(data))
    items = data if isinstance(data, list) else None
    if items is None and isinstance(data, dict):
        for k in ("models", "items", "data", "list"):
            if isinstance(data.get(k), list):
                items = data[k]
                break
    print("%s模型 | 积分/次 | 说明%s" % (C_BOLD, _ansi("0")))
    print("-" * 60)
    count = 0
    for it in items or []:
        if not isinstance(it, dict):
            print("- %s" % it)
            continue
        name = it.get("model") or it.get("name") or it.get("id") or "?"
        price = it.get("price", it.get("points", it.get("cost", "?")))
        desc = it.get("label") or it.get("description") or it.get("desc") or ""
        print("%-28s %6s %s" % (name, price, desc))
        count += 1
    if not count:
        print(json.dumps(data, ensure_ascii=False, indent=2)[:3000])
    print("-" * 60)
    print("%s出图: 1.5K=40积分/张  2K=75积分/张  |  网页解析: 1/2/5 积分%s" % (C_DIM, _ansi("0")))

def cmd_chat(args):
    key = need_key()
    body = {
        "model": args.model,
        "messages": [{"role": "user", "content": args.prompt}],
        "max_tokens": args.max_tokens,
        "stream": False,
    }
    status, data = client.request("POST", "/api/v1/open/chat/completions", key, body)
    if status != 200:
        die(_err(data))
    print(_content(data) or json.dumps(data, ensure_ascii=False)[:2000])

def cmd_ask(args):
    key = need_key()
    body = {
        "model": "auto",
        "messages": [{"role": "user", "content": args.prompt}],
        "stream": False,
    }
    if args.max_tokens:
        body["max_tokens"] = args.max_tokens
    print("%s思考中（智能体会自动联网搜索）…%s" % (C_DIM, _ansi("0")))
    status, data = client.request("POST", "/api/v1/open/universal/chat", key, body, timeout=300)
    if status != 200:
        die(_err(data))
    print(_content(data) or json.dumps(data, ensure_ascii=False)[:2000])

_IMG_MD_RE = re.compile(r"!\[[^\]]*\]\((https?://[^)\s]+)\)")
_IMG_URL_RE = re.compile(r"https?://[^\s\)\]\"'<>]+\.(?:jpe?g|png|webp)(?:\?[^\s\)\]\"'<>]*)?", re.I)

def cmd_image(args):
    key = need_key()
    size = "2K" if (args.size or "").upper().strip() in ("2K", "2048") else "1.5K"
    body = {
        "model": "auto",
        # 前缀触发词命中后端出图工具（"帮我画"），size 供 _pick_image_size 识别
        "messages": [{"role": "user", "content": "帮我画一张图：%s %s" % (args.prompt, size)}],
        "stream": False,
    }
    print("%s生成中（Seedream 5.0 Pro，约10-60秒）…%s" % (C_DIM, _ansi("0")))
    status, data = client.request("POST", "/api/v1/open/universal/chat", key, body, timeout=300)
    if status != 200:
        die(_err(data))
    content = _content(data)
    url = None
    m = _IMG_MD_RE.search(content or "")
    if m:
        url = m.group(1)
    if not url:
        m = _IMG_URL_RE.search(content or "")
        if m:
            url = m.group(0)
    if not url:
        die("未在回复中找到图片链接，原始回复:\n%s" % (content or json.dumps(data, ensure_ascii=False)[:1500]))
    ok("出图成功: %s" % url)
    if args.out:
        _download(url, args.out)
        ok("已保存: %s" % os.path.abspath(args.out))

def _download(url, path):
    import urllib.request
    req = urllib.request.Request(url, headers={"User-Agent": client.UA})
    with urllib.request.urlopen(req, timeout=120) as r, open(path, "wb") as f:
        f.write(r.read())

def cmd_extract(args):
    key = need_key()
    if not args.url and not args.text:
        die("需要 --url 或 --text 提供解析内容")
    body = {"source": "url" if args.url else "text"}
    body["url" if args.url else "text"] = args.url or args.text
    if args.question:
        body["question"] = args.question
    print("%s解析中…%s" % (C_DIM, _ansi("0")))
    status, data = client.request("POST", "/api/v1/open/extract", key, body)
    if status != 200:
        die(_err(data))
    result = None
    if isinstance(data, dict):
        for k in ("result", "content", "answer", "data", "text", "extracted"):
            v = data.get(k)
            if v not in (None, "", [], {}):
                result = v
                break
    if result is None:
        result = data
    if isinstance(result, (dict, list)):
        print(json.dumps(result, ensure_ascii=False, indent=2)[:8000])
    else:
        print(str(result)[:8000])

# ---------------- 工具 ----------------

def _err(data):
    if isinstance(data, dict):
        e = data.get("error")
        if isinstance(e, dict):
            return str(e.get("message") or e.get("detail") or e)
        for k in ("detail", "message", "error"):
            if data.get(k):
                return str(data[k])
    return json.dumps(data, ensure_ascii=False)[:500] if data else "未知错误"

def _content(data):
    try:
        c = data["choices"][0]["message"]["content"] or ""
        if isinstance(c, list):
            c = "".join(x.get("text", "") if isinstance(x, dict) else str(x) for x in c)
        return c.strip()
    except (KeyError, IndexError, TypeError, AttributeError):
        return ""

# ---------------- 参数解析 ----------------

def main():
    ap = argparse.ArgumentParser(
        prog="qt",
        description="QuantumToken 命令行工具 — AI对话/联网问答/AI出图/网页解析 (trade.pianam.cn)",
    )
    ap.add_argument("--version", action="version", version="qt %s" % __version__)
    sub = ap.add_subparsers(dest="cmd")

    p = sub.add_parser("login", help="保存 API Key（qt login qk_xxx）")
    p.add_argument("key", nargs="?", help="qk_ 开头的 API Key")
    p.set_defaults(fn=cmd_login)

    p = sub.add_parser("logout", help="清除本地保存的 Key")
    p.set_defaults(fn=cmd_logout)

    p = sub.add_parser("balance", help="查询剩余积分")
    p.set_defaults(fn=cmd_balance)

    p = sub.add_parser("whoami", help="同 balance")
    p.set_defaults(fn=cmd_balance)

    p = sub.add_parser("models", help="模型列表与价格")
    p.set_defaults(fn=cmd_models)

    p = sub.add_parser("chat", help="AI 对话（纯文本，按模型计费 1-10 积分）")
    p.add_argument("prompt", help="你的问题")
    p.add_argument("-m", "--model", default="qwen-flash", help="模型名（qt models 查看），默认 qwen-flash")
    p.add_argument("--max-tokens", type=int, default=1024)
    p.set_defaults(fn=cmd_chat)

    p = sub.add_parser("ask", help="智能体问答：自动联网搜索、可出图（~5积分/次起）")
    p.add_argument("prompt", help="你的问题")
    p.add_argument("--max-tokens", type=int, default=None)
    p.set_defaults(fn=cmd_ask)

    p = sub.add_parser("image", help="AI 出图（Seedream 5.0 Pro：1.5K=40 / 2K=75 积分）")
    p.add_argument("prompt", help="画面描述")
    p.add_argument("-s", "--size", default="1.5K", help="1.5K（默认）或 2K")
    p.add_argument("-o", "--out", default=None, help="保存图片到本地文件")
    p.set_defaults(fn=cmd_image)

    p = sub.add_parser("extract", help="网页/文本 AI 解析（1-5 积分）")
    p.add_argument("--url", default=None, help="要解析的网页地址")
    p.add_argument("--text", default=None, help="要解析的文本")
    p.add_argument("-q", "--question", default=None, help="针对内容提问（默认抽取结构化信息）")
    p.set_defaults(fn=cmd_extract)

    args = ap.parse_args()
    if not getattr(args, "fn", None):
        ap.print_help()
        sys.exit(0)
    try:
        args.fn(args)
    except ApiError as e:
        fail("[%s] %s" % (e.status, e.message), e.hint)
        sys.exit(1)
    except KeyboardInterrupt:
        print()
        die("已取消")


if __name__ == "__main__":
    main()
