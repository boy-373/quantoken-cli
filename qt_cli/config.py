"""key 存取：环境变量 QUANTOKEN_API_KEY 优先，其次 ~/.qtcli/config.json"""
import json
import os

CONF_DIR = os.path.join(os.path.expanduser("~"), ".qtcli")
CONF_FILE = os.path.join(CONF_DIR, "config.json")


def load():
    try:
        with open(CONF_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save(data):
    os.makedirs(CONF_DIR, exist_ok=True)
    with open(CONF_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    try:
        os.chmod(CONF_FILE, 0o600)  # 仅本用户可读
    except Exception:
        pass


def get_key():
    key = os.environ.get("QUANTOKEN_API_KEY") or load().get("api_key") or ""
    return key.strip()


def mask(key):
    if not key:
        return "(未配置)"
    if len(key) <= 12:
        return key[:4] + "****"
    return key[:8] + "****" + key[-4:]
