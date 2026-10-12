# 第 6 天：调用大模型 API ★ 正式进入 AI 应用开发

> 今天你要亲手把大模型"接进"自己的程序。
> 核心认知：**大模型就是一个 HTTP 接口，你发一段文字，它回一段文字。** 就这么简单。

---

## 1. 先理解：一次对话背后发生了什么

```
你的 Python 程序
      │  POST https://api.xxx.com/v1/chat/completions
      │  Header: Authorization: Bearer sk-xxx
      │  Body:   {"model": "...", "messages": [{"role":"user","content":"你好"}]}
      ▼
  模型服务（GPU 集群上跑的千亿参数模型）
      │  返回 JSON
      ▼
{"choices":[{"message":{"role":"assistant","content":"你好！有什么可以帮你？"}}],
 "usage":{"prompt_tokens":9,"completion_tokens":12,"total_tokens":21}}
```

**三个关键名词**：

| 名词 | 含义 |
|---|---|
| `messages` | 对话历史数组，每个元素 `{"role": ..., "content": ...}` |
| `role` | `system`（设定人设）/ `user`（用户）/ `assistant`（模型回复）/ `tool`（工具结果） |
| `token` | 模型计费和处理的最小单位，中文大致 1 字 ≈ 1–1.5 token |

**所以"AI 应用开发"的本质工作就是：决定往 `messages` 里塞什么。**

---

## 2. 准备：拿到 API Key

三种选择，任选其一（**代码写法几乎一样**，因为都兼容 OpenAI 协议）：

| 方案 | 说明 | 适合 |
|---|---|---|
| **国内云厂商**（DeepSeek / 通义 / 智谱 / 月之暗面等） | 注册即送额度，支付宝付费，网络稳定 | ⭐ 国内首选 |
| **OpenAI / Anthropic** | 需要海外支付方式 | 有条件的话 |
| **本地模型**（Ollama） | 完全免费离线，效果弱一些 | 练习用，不花钱 |

### 本地免费方案（想零成本练习就用这个）

1. 下载安装 <https://ollama.com/download>
2. 命令行拉一个模型：
   ```powershell
   ollama pull qwen2.5:7b
   ollama run qwen2.5:7b      # 测试一下，输入 /bye 退出
   ```
3. Ollama 会在 `http://localhost:11434/v1` 提供 OpenAI 兼容接口，Key 随便填。

### 配置密钥（★ 必须用环境变量）

在项目根目录建 `.env`：

```
# 换成你自己的
OPENAI_API_KEY=sk-你的密钥
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
```

再建 `.gitignore`：

```
.venv/
.env
__pycache__/
*.log
*.jsonl
```

安装依赖：

```powershell
uv add openai python-dotenv
uv add requests        # 第 3 节手写版要用
```

---

## 3. 第一种写法：纯 requests（理解原理，必须会）

```python
# raw_api.py —— 不用任何 SDK，直接发 HTTP 请求
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if not API_KEY:
    raise SystemExit("❌ 请在 .env 里配置 OPENAI_API_KEY")

url = f"{BASE_URL}/chat/completions"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

payload = {
    "model": MODEL,
    "messages": [
        {"role": "system", "content": "你是一个简洁的 Python 助教，回答不超过三句话。"},
        {"role": "user", "content": "什么是列表推导式？"},
    ],
    "temperature": 0.7,
}

resp = requests.post(url, headers=headers, json=payload, timeout=60)

# ★ 永远先检查状态码
if resp.status_code != 200:
    print("请求失败：", resp.status_code)
    print(resp.text[:500])
    raise SystemExit(1)

data = resp.json()
answer = data["choices"][0]["message"]["content"]
usage = data["usage"]

print("=" * 50)
print(answer)
print("=" * 50)
print(f"输入 {usage['prompt_tokens']} + 输出 {usage['completion_tokens']} = {usage['total_tokens']} tokens")
```

**这段代码就是所有 AI 应用的原子操作。** 把它抄到一个 `llm_raw.py` 里跑通，你就理解了 90% 的原理。

> 💡 为什么有些模型（如 o1、deepseek-reasoner）返回里还有 `reasoning_content`？
> 那是"思考过程"字段，正文仍在 `content` 里，取的时候优先用 `.get("content") or ""`。

---

## 4. 第二种写法：官方 SDK（日常开发用这个）

```python
# llm_sdk.py
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),        # 换厂商只改这一行
)
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# ① 最简调用
resp = client.chat.completions.create(
    model=MODEL,
    messages=[{"role": "user", "content": "用一句话解释什么是 API"}],
)
print(resp.choices[0].message.content)
print("tokens:", resp.usage.total_tokens)

# ② 带 system 人设 + 参数
resp = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "system", "content": "你是一个严谨的技术作家，只讲事实。"},
        {"role": "user", "content": "对比 Python 和 JavaScript，给 3 条要点。"},
    ],
    temperature=0.3,          # 0=最确定，1=最发散
    max_tokens=300,           # 限制输出长度（省钱 + 防跑飞）
    top_p=0.9,
)
print(resp.choices[0].message.content)
```

### 参数怎么调？

| 参数 | 作用 | 建议 |
|---|---|---|
| `temperature` | 随机性 | 写代码/抽取数据用 `0–0.3`；创意写作用 `0.8–1.0` |
| `max_tokens` | 输出上限 | 一定要设，防止模型啰嗦烧钱 |
| `top_p` | 采样范围 | 一般别动，用默认 |
| `seed` | 固定随机种子 | 需要可复现时设（部分厂商支持） |

> **规律**：`temperature` 和 `top_p` 只需调一个。做数据抽取、分类、JSON 输出时，`temperature=0`。

---

## 5. 流式输出（stream=True）：打字机效果

普通请求要等模型全部生成完才返回（可能十几秒），流式可以边生成边显示。

```python
# stream_demo.py
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL"))
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

stream = client.chat.completions.create(
    model=MODEL,
    messages=[{"role": "user", "content": "用 100 字介绍一下向量数据库"}],
    stream=True,
    temperature=0.5,
)

full = []
for chunk in stream:
    # 有些 chunk 没有 choices（比如最后一帧只带 usage），要判断
    if not chunk.choices:
        continue
    delta = chunk.choices[0].delta            # delta 是"增量"，不是完整内容
    piece = getattr(delta, "content", None)
    if piece:
        full.append(piece)
        print(piece, end="", flush=True)      # ★ 不换行 + 立刻输出

print("\n\n" + "=" * 40)
text = "".join(full)
print(f"共 {len(text)} 字")
```

**流式的三个实用技巧**：

```python
# ① 想要 usage？加 stream_options
stream = client.chat.completions.create(
    model=MODEL, messages=[...], stream=True,
    stream_options={"include_usage": True},
)
# 最后一帧会有 chunk.usage

# ② 想中途停止生成？直接 break，连接会关闭
for chunk in stream:
    piece = chunk.choices[0].delta.content or ""
    print(piece, end="", flush=True)
    if "够了" in piece:
        break
```

> **⚠️ 流式时无法对整段文本做后处理**（比如解析 JSON）。要么先收集完再处理，要么不用流式。

---

## 6. 结构化输出：让模型返回 JSON（★ 工程化最关键的一步）

自然语言没法给程序用。让模型吐 JSON，程序才能接手。

### 方法一：提示词约束 + 清洗（通用，所有模型都支持）

```python
# json_output.py
import json
import os
import re
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL"))

REVIEW = """这家店环境不错，但是服务员态度很差，等了四十分钟才上菜，菜品味道还行，价格偏贵。"""

prompt = f"""从下面的评论中抽取信息，只输出 JSON，不要任何解释文字。

输出格式：
{{
  "sentiment": "positive" 或 "negative" 或 "neutral",
  "score": 1 到 5 的整数,
  "pros": ["优点1", "优点2"],
  "cons": ["缺点1", "缺点2"]
}}

评论：
{REVIEW}
"""

resp = client.chat.completions.create(
    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    messages=[{"role": "user", "content": prompt}],
    temperature=0,                      # 抽取任务必须 0
)
raw = resp.choices[0].message.content
print("模型原始输出：\n", raw)


def extract_json(text: str) -> dict:
    """从模型输出里稳健地抠出 JSON。"""
    # 去掉 ```json ... ``` 包裹
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fence:
        text = fence.group(1).strip()
    # 截取第一个 { 到最后一个 }
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1:
        text = text[start:end + 1]
    return json.loads(text)


try:
    data = extract_json(raw)
    print("\n解析结果：")
    print(f"  情感：{data['sentiment']}  评分：{data['score']}")
    print(f"  优点：{data['pros']}")
    print(f"  缺点：{data['cons']}")
except json.JSONDecodeError as e:
    print("解析失败：", e)
```

### 方法二：官方 `response_format`（支持的厂商直接开）

```python
resp = client.chat.completions.create(
    model=MODEL,
    messages=[{"role": "user", "content": prompt}],
    response_format={"type": "json_object"},   # 强制返回 JSON
)
data = json.loads(resp.choices[0].message.content)
```

### 方法三：用 pydantic 做类型校验（生产级别）

```python
# pip install pydantic
from pydantic import BaseModel, Field, ValidationError

class Review(BaseModel):
    sentiment: str = Field(description="positive / negative / neutral")
    score: int = Field(ge=1, le=5)
    pros: list[str] = []
    cons: list[str] = []

try:
    review = Review.model_validate(data)      # 自动校验类型和范围
    print(review.sentiment, review.score)
    print(review.model_dump_json(indent=2, ensure_ascii=False))
except ValidationError as e:
    print("模型输出不符合格式：", e)
```

> **生产环境的铁律**：凡是模型输出要进数据库/进业务逻辑的，**必须校验**。
> 模型再听话也有 1% 概率返回惊喜，你的程序不能因此崩掉。

---

## 7. 稳健的封装：超时、重试、日志、成本统计

**这段代码建议直接存成 `llm.py`，后面所有项目都 import 它。**

```python
# llm.py
import os
import time
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI, APIError, APITimeoutError, RateLimitError

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("llm")

# 每 100 万 token 的价格（美元），按你用的厂商改
PRICING = {
    "gpt-4o-mini":     {"in": 0.15, "out": 0.60},
    "deepseek-chat":   {"in": 0.27, "out": 1.10},
    "qwen2.5:7b":      {"in": 0.0,  "out": 0.0},     # 本地模型免费
}


@dataclass
class LLMResult:
    text: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    seconds: float = 0.0

    @property
    def cost_usd(self) -> float:
        return 0.0     # 由调用方按模型算，见 LLM.cost


class LLM:
    def __init__(self, model: str | None = None, temperature: float = 0.7,
                 max_tokens: int = 1024, log_file: str = "llm_calls.jsonl"):
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
            timeout=60.0,
            max_retries=3,           # SDK 自带重试
        )
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.log_path = Path(log_file)

    def cost(self, r: LLMResult) -> float:
        p = PRICING.get(self.model, {"in": 0, "out": 0})
        return (r.prompt_tokens * p["in"] + r.completion_tokens * p["out"]) / 1_000_000

    def chat(self, messages: list[dict], **overrides) -> LLMResult:
        """普通调用。messages 就是 [{"role":..., "content":...}]"""
        params = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        params.update(overrides)

        t0 = time.time()
        try:
            resp = self.client.chat.completions.create(**params)
        except RateLimitError:
            log.warning("触发限流，等待 5 秒重试")
            time.sleep(5)
            resp = self.client.chat.completions.create(**params)
        except APITimeoutError:
            log.error("请求超时")
            raise
        except APIError as e:
            log.error("API 错误：%s", e)
            raise

        elapsed = time.time() - t0
        result = LLMResult(
            text=resp.choices[0].message.content or "",
            prompt_tokens=resp.usage.prompt_tokens if resp.usage else 0,
            completion_tokens=resp.usage.completion_tokens if resp.usage else 0,
            seconds=elapsed,
        )
        self._log(params["messages"], result)
        log.info("tokens=%d/%d  %.2fs  $%.6f",
                 result.prompt_tokens, result.completion_tokens,
                 elapsed, self.cost(result))
        return result

    def stream(self, messages: list[dict], **overrides):
        """流式调用，逐段 yield 文本。"""
        params = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": True,
        }
        params.update(overrides)
        for chunk in self.client.chat.completions.create(**params):
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def _log(self, messages: list[dict], result: LLMResult) -> None:
        record = {
            "model": self.model,
            "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
            "messages": messages,
            "reply": result.text,
            "prompt_tokens": result.prompt_tokens,
            "completion_tokens": result.completion_tokens,
            "seconds": round(result.seconds, 3),
        }
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    llm = LLM()
    r = llm.chat([{"role": "user", "content": "用一句话说明 Python 的字典是什么"}])
    print(r.text)
    print(f"花费 ${llm.cost(r):.6f}，耗时 {r.seconds:.2f}s")

    print("\n--- 流式 ---")
    for piece in llm.stream([{"role": "user", "content": "数 1 到 5，用中文"}], max_tokens=50):
        print(piece, end="", flush=True)
    print()
```

### 用 pandas 分析你的调用日志（把第 4 天用上）

```python
import pandas as pd
df = pd.read_json("llm_calls.jsonl", lines=True)
print(df[["ts", "model", "prompt_tokens", "completion_tokens", "seconds"]].tail())
print("\n总 token：", df["prompt_tokens"].sum() + df["completion_tokens"].sum())
print("平均延迟：", round(df["seconds"].mean(), 2), "秒")
```

---

## 8. 省钱 checklist（真金白银）

1. **`max_tokens` 永远设上限** —— 最便宜的保险。
2. **短任务用小模型** —— 分类、改写、抽取用便宜模型，只有复杂推理才上大模型。
3. **裁掉没用的历史** —— 多轮对话只保留最近 N 轮（第 7 天代码里会实现）。
4. **能不用模型就不用** —— 关键词判断、正则匹配、业务规则能解决的，别问模型。
5. **缓存重复请求** —— 同一个问题问两次，直接读缓存。
6. **精简 system prompt** —— 每次请求都会重复计费，别写 2000 字人设。

```python
# 一个 5 行缓存装饰器，高频重复场景能省一半钱
import hashlib, json
from functools import lru_cache

@lru_cache(maxsize=256)
def cached_answer(prompt: str) -> str:
    return LLM(temperature=0).chat([{"role": "user", "content": prompt}]).text

# 更稳的做法：以 prompt 的 hash 为 key 存到本地 json 文件
def cache_key(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()
```

---

## 9. 今日作业

1. 跑通 `raw_api.py`（requests 版），打印完整的 `data` JSON 看结构。
2. 跑通 `llm.py`，然后**故意填错 API Key**，观察报什么错，理解错误处理。
3. 写一个 `translate.py`：读取命令行参数里的中文，翻译成英文并输出。
   ```powershell
   python translate.py "今天天气很好"
   ```
   提示：用 `sys.argv` 或 `input()` 取参数。
4. 用第 6 节的 JSON 抽取，处理 3 条真实商品评论，把结果存成 `reviews.json`。
5. 挑战：加一个 `--stream` 参数，让 `translate.py` 支持流式输出。

---

## 10. 一分钟自测

- [ ] `messages` 里三种 role 分别是什么作用？
- [ ] `temperature=0` 适合什么任务？（抽取、分类、代码）
- [ ] 为什么流式输出要用 `flush=True`？
- [ ] 模型输出要进数据库前，必须做什么？（校验格式，如 pydantic）
- [ ] API Key 应该放在哪？（`.env` + `os.getenv`，绝不能硬编码）
- [ ] 为什么 `max_tokens` 一定要设？

---

上一课 → [`04_机器学习30分钟入门.md`](04_机器学习30分钟入门.md) ｜ 下一课 → [`06_项目_命令行聊天机器人.md`](06_项目_命令行聊天机器人.md)
