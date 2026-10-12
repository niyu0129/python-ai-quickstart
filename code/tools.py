"""
Agent 工具箱 —— 可直接被第 10 天的 Agent 循环调用。

包含：
    1. 一批安全可用的工具函数（计算、读文件、列目录、搜索、抓网页、计时）
    2. make_schema()：从函数的类型注解 + docstring 自动生成工具说明书
    3. REGISTRY / TOOLS_SCHEMA：注册表和说明书列表，直接喂给模型

用法：
    from tools import REGISTRY, TOOLS_SCHEMA
    resp = client.chat.completions.create(..., tools=TOOLS_SCHEMA)

    # 执行模型请求的调用
    fn = REGISTRY[name]
    result = fn(**json.loads(call.function.arguments or "{}"))

新增自己的工具：写好函数 + 加一行 @tool 装饰器即可。
"""

from __future__ import annotations

import inspect
import json
import math
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import get_type_hints

import requests
from dotenv import load_dotenv

load_dotenv()

# 工具能访问的项目根目录（安全边界：所有文件操作都限制在这里面）
PROJECT_ROOT = Path.cwd().resolve()

# 敏感文件名黑名单：绝不允许模型读到
SENSITIVE_NAMES = {".env", ".env.local", "id_rsa", "credentials.json", "secrets.json"}

PY_TO_JSON = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
}


# ============================================================
# 工具实现
# ============================================================
def calculator(expression: str) -> str:
    """计算数学表达式，支持 + - * / // % ** 和常用数学函数（sqrt、log、sin 等）。需要精确计算时使用。"""
    expr = expression.strip().replace("^", "**")
    if not re.fullmatch(r"[0-9a-zA-Z_+\-*/().,% ]+", expr):
        return "错误：表达式包含不允许的字符"
    allowed = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
    allowed.update({"abs": abs, "round": round, "min": min, "max": max, "sum": sum})
    try:
        result = eval(expr, {"__builtins__": {}}, allowed)      # 已用白名单限制字符集
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算失败：{type(e).__name__}: {e}"


def _safe_path(path: str) -> Path:
    """把用户/模型给的路径解析到项目内，越界就抛错。"""
    p = Path(path)
    resolved = (PROJECT_ROOT / p).resolve() if not p.is_absolute() else p.resolve()
    if PROJECT_ROOT != resolved and PROJECT_ROOT not in resolved.parents:
        raise PermissionError(f"拒绝访问项目目录之外的位置：{resolved}")
    return resolved


def read_file(path: str, max_chars: int = 4000) -> str:
    """读取项目目录内的文本文件内容。用户询问文件内容时使用。"""
    try:
        p = _safe_path(path)
    except PermissionError as e:
        return str(e)
    if p.name in SENSITIVE_NAMES or p.suffix in {".key", ".pem"}:
        return "拒绝访问：该文件被视为敏感文件"
    if not p.exists():
        return f"文件不存在：{path}"
    if p.is_dir():
        return f"{path} 是目录，请用 list_files 查看"
    if p.stat().st_size > 500_000:
        return "文件过大（>500KB），请指定更小的文件"
    text = p.read_text(encoding="utf-8", errors="ignore")
    if len(text) > max_chars:
        return text[:max_chars] + f"\n...[已截断，全文共 {len(text)} 字]"
    return text


def list_files(directory: str = ".", pattern: str = "*") -> str:
    """列出项目目录下的文件和子目录。用户询问"有哪些文件"时使用。"""
    try:
        p = _safe_path(directory)
    except PermissionError as e:
        return str(e)
    if not p.exists():
        return f"目录不存在：{directory}"
    if not p.is_dir():
        return f"{directory} 不是目录"
    items = sorted(p.glob(pattern))[:60]
    lines = []
    for f in items:
        try:
            if f.is_dir():
                lines.append(f"[目录] {f.name}/")
            else:
                lines.append(f"[文件] {f.name}  ({f.stat().st_size} 字节)")
        except OSError:
            lines.append(f"[无法访问] {f.name}")
    return "\n".join(lines) or "（空目录）"


def get_time(city: str = "本地") -> str:
    """查询当前日期和时间。用户问"现在几点""今天几号"时使用。"""
    return f"{city} 当前时间：{datetime.now():%Y-%m-%d %H:%M:%S}"


def date_calc(date: str, days: int) -> str:
    """日期加减。date 格式 YYYY-MM-DD，days 为天数（可为负）。"""
    try:
        d = datetime.strptime(date.strip(), "%Y-%m-%d")
    except ValueError:
        return "日期格式错误，应为 YYYY-MM-DD，例如 2025-03-08"
    return f"{date} 加 {days} 天是 {(d + timedelta(days=days)):%Y-%m-%d}"


def web_search(query: str, max_results: int = 5) -> str:
    """联网搜索最新信息。需要配置 TAVILY_API_KEY。用户问到最新消息、实时数据时使用。"""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "未配置搜索 API（TAVILY_API_KEY），无法联网搜索"
    try:
        r = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": api_key, "query": query, "max_results": int(max_results)},
            timeout=25,
        )
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return f"搜索失败：{type(e).__name__}: {e}"

    results = data.get("results", [])
    if not results:
        return "没有找到相关结果"
    lines = []
    for i, it in enumerate(results, 1):
        lines.append(f"{i}. {it.get('title', '')}\n   {it.get('url', '')}\n   "
                     f"{(it.get('content') or '')[:200]}")
    return "\n".join(lines)


def fetch_url(url: str, max_chars: int = 3000) -> str:
    """抓取网页正文文本。用户给出链接要看内容时使用。"""
    if not url.startswith(("http://", "https://")):
        return "只支持 http/https 链接"
    try:
        r = requests.get(url, timeout=25, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
    except Exception as e:
        return f"抓取失败：{type(e).__name__}: {e}"

    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", r.text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;|&amp;|&lt;|&gt;", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_chars:
        return text[:max_chars] + "...[已截断]"
    return text or "（页面没有可读文本）"


def run_python(code: str, timeout: int = 15) -> str:
    """
    在子进程中执行一小段 Python 代码并返回输出。

    ⚠️ 高风险工具：这不是真正的沙箱，仅供本地学习使用。
    生产环境必须用 Docker 容器 + 网络隔离 + 资源限制。
    """
    if len(code) > 2000:
        return "代码过长（上限 2000 字符）"
    banned = ["import os", "import sys", "import subprocess", "shutil", "socket",
              "__import__", "open(", "eval(", "exec(", "requests", "urllib"]
    for b in banned:
        if b in code:
            return f"代码包含被禁止的内容：{b}"
    try:
        proc = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, timeout=timeout,
            encoding="utf-8", errors="ignore", cwd=str(PROJECT_ROOT),
        )
        output = (proc.stdout or "") + (proc.stderr or "")
        return output.strip()[:3000] or "（无输出）"
    except subprocess.TimeoutExpired:
        return f"执行超时（{timeout} 秒）"


# ============================================================
# 自动生成工具说明书
# ============================================================
REGISTRY: dict[str, object] = {}


def make_schema(fn) -> dict:
    """从函数签名和 docstring 生成 OpenAI 风格的 tool schema。"""
    sig = inspect.signature(fn)
    hints = get_type_hints(fn)
    doc = (fn.__doc__ or "").strip()
    description = doc.split("\n")[0].strip() or fn.__name__

    props: dict[str, dict] = {}
    required: list[str] = []
    for name, param in sig.parameters.items():
        annotation = hints.get(name, str)
        props[name] = {
            "type": PY_TO_JSON.get(annotation, "string"),
            "description": "",
        }
        if param.default is inspect.Parameter.empty:
            required.append(name)
        else:
            props[name]["default"] = param.default

    return {
        "type": "function",
        "function": {
            "name": fn.__name__,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": props,
                "required": required,
            },
        },
    }


def tool(fn):
    """装饰器：注册工具并自动生成说明书。"""
    REGISTRY[fn.__name__] = fn
    return fn


# 注册所有工具
for _fn in [calculator, read_file, list_files, get_time, date_calc,
            web_search, fetch_url, run_python]:
    tool(_fn)

TOOLS_SCHEMA = [make_schema(fn) for fn in REGISTRY.values()]


# ============================================================
# 执行入口
# ============================================================
def execute_tool(name: str, arguments: str | dict) -> str:
    """
    统一执行入口：模型给什么就执行什么，并处理各种异常。

    arguments 可能是 JSON 字符串（模型返回）或已经解析好的字典。
    """
    if isinstance(arguments, str):
        try:
            args = json.loads(arguments or "{}")
        except json.JSONDecodeError as e:
            return f"参数解析失败（不是合法 JSON）：{e}"
    else:
        args = arguments or {}

    fn = REGISTRY.get(name)
    if fn is None:
        return f"未注册的工具：{name}。可用工具：{', '.join(REGISTRY)}"

    # 只传函数签名里有的参数（防止模型多传参数导致 TypeError）
    valid = set(inspect.signature(fn).parameters)
    extra = set(args) - valid
    args = {k: v for k, v in args.items() if k in valid}
    if extra:
        print(f"\033[90m[忽略多余参数 {extra}]\033[0m")

    try:
        return str(fn(**args))
    except TypeError as e:
        return f"参数不匹配：{e}（期望参数：{', '.join(valid)}）"
    except Exception as e:
        return f"工具执行出错：{type(e).__name__}: {e}"


if __name__ == "__main__":
    print(f"已注册 {len(REGISTRY)} 个工具：{', '.join(REGISTRY)}\n")
    print("=== 自动生成的 schema 示例（calculator）===")
    print(json.dumps(TOOLS_SCHEMA[0], ensure_ascii=False, indent=2))

    print("\n=== 直接测试工具 ===")
    print(execute_tool("calculator", '{"expression": "1234 * 56 / 7"}'))
    print(execute_tool("get_time", "{}"))
    print(execute_tool("date_calc", '{"date": "2025-03-08", "days": 30}'))
    print(execute_tool("list_files", '{"pattern": "*.py"}'))
    print(execute_tool("read_file", '{"path": ".env"}'))          # 应该被拒绝
    print(execute_tool("read_file", '{"path": "../../windows/win.ini"}'))  # 应该被拒绝
    print(execute_tool("run_python", '{"code": "print(2 ** 10)"}'))
    print(execute_tool("run_python", '{"code": "import os; os.system(\'dir\')"}'))  # 应该被拒绝
