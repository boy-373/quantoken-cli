"""HTTP 客户端：零依赖 urllib，自定义 UA（服务端拦截 python/curl 默认 UA）"""
import json
import urllib.error
import urllib.request

BASE = "https://site.pianam.cn"
UA = "QuantumToken-CLI/1.0"


class ApiError(Exception):
    def __init__(self, status, message, hint=""):
        super().__init__(message)
        self.status = status
        self.message = message
        self.hint = hint


def _hint_for(status):
    return {
        401: "API Key 无效或已停用，请到 trade.pianam.cn 控制台核对，或重新执行 qt login",
        402: "积分不足，请到 trade.pianam.cn 充值（1元=100积分）",
        404: "接口不存在，可能 CLI 版本过旧，尝试: pip install -U git+https://github.com/boy-373/quantoken-cli.git",
        413: "内容过大，请缩短输入",
        429: "请求过于频繁，稍后再试",
    }.get(status, "")


def request(method, path, key, body=None, timeout=300):
    """返回 (status, data_dict)。HTTP 错误抛 ApiError，网络错误抛 ApiError(-1)。"""
    url = BASE + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    req.add_header("User-Agent", UA)
    if key:
        req.add_header("Authorization", "Bearer " + key)
        req.add_header("X-API-Key", key)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", "ignore")
            try:
                return resp.status, json.loads(raw)
            except Exception:
                return resp.status, {"raw": raw}
    except urllib.error.HTTPError as e:
        try:
            detail = json.loads(e.read().decode("utf-8", "ignore"))
        except Exception:
            detail = {}
        msg = _extract_err(detail) or ("HTTP %d" % e.code)
        raise ApiError(e.code, msg, _hint_for(e.code))
    except urllib.error.URLError as e:
        raise ApiError(-1, "网络错误: %s" % getattr(e, "reason", e), "请检查网络后重试")


def _extract_err(detail):
    if not isinstance(detail, dict):
        return ""
    err = detail.get("error")
    if isinstance(err, dict):
        return str(err.get("message") or err.get("detail") or "")
    for k in ("detail", "message", "error"):
        v = detail.get(k)
        if v:
            return str(v)
    return ""
