# 第 3 天：Python 语法速通 B —— 进阶

> 今天学的是**"从能跑 → 能维护"**的东西：函数、推导式、类型注解、异常、文件、类、模块。
> 这一课学完，你就有能力看懂开源 AI 项目的源码了。

---

## 1. 函数：把逻辑打包复用

```python
def greet(name):                 # def 定义函数
    """给用户打招呼。"""          # 文档字符串（可选，但强烈建议写）
    return f"你好，{name}！"

msg = greet("小明")
print(msg)
```

### 参数的各种花样

```python
# 1) 默认参数
def call_llm(prompt: str, temperature: float = 0.7, max_tokens: int = 512):
    return f"用 {temperature} 的随机性，最多生成 {max_tokens} tokens"

call_llm("你好")
call_llm("你好", temperature=0.2)          # 关键字参数，可读性好
call_llm("你好", max_tokens=1024)

# 2) 可变参数：任意个位置参数
def total(*numbers):
    return sum(numbers)

total(1, 2, 3)      # 6

# 3) 关键字可变参数：接收任意命名参数（★ 封装 API 时超常用）
def build_payload(**kwargs):
    return {"model": "gpt-4o-mini", **kwargs}

build_payload(temperature=0.5, max_tokens=256)
# {'model': 'gpt-4o-mini', 'temperature': 0.5, 'max_tokens': 256}
```

> ⚠️ **新手经典大坑：不要用可变对象当默认值**
> ```python
> def bad(item, box=[]):     # ❌ 这个 [] 是所有调用共享的！
>     box.append(item)
>     return box
>
> bad(1)   # [1]
> bad(2)   # [1, 2]  ← 见鬼了
>
> def good(item, box=None):  # ✅ 正确写法
>     if box is None:
>         box = []
>     box.append(item)
>     return box
> ```

### 多返回值（本质是元组）

```python
def stats(nums):
    return min(nums), max(nums), sum(nums) / len(nums)

lo, hi, avg = stats([90, 85, 77])
print(f"最低 {lo}，最高 {hi}，平均 {avg:.1f}")
```

### 作用域

```python
count = 0                 # 全局变量

def add():
    global count          # 想改全局变量必须声明（不推荐，尽量用返回值）
    count += 1

def pure_add(n):          # ✅ 推荐：通过参数传入、通过返回值传出
    return n + 1
```

---

## 2. 列表推导式：一行顶五行（AI 代码里到处都是）

```python
nums = [1, 2, 3, 4, 5, 6]

# 普通写法
squares = []
for n in nums:
    squares.append(n * n)

# 推导式写法
squares = [n * n for n in nums]

# 带条件
evens = [n for n in nums if n % 2 == 0]        # [2, 4, 6]

# 对字符串列表处理（清洗数据常用）
raw = ["  你好 ", "\n世界", " Python  "]
cleaned = [s.strip() for s in raw]             # ['你好', '世界', 'Python']
cleaned = [s.strip() for s in raw if s.strip()]  # 顺便去掉空串

# 字典推导式
words = ["apple", "banana", "cherry"]
lengths = {w: len(w) for w in words}
# {'apple': 5, 'banana': 6, 'cherry': 6}

# 嵌套：处理 API 返回的消息列表
messages = [{"role": "user", "content": "你好"}, {"role": "assistant", "content": "你好呀"}]
contents = [m["content"] for m in messages]
only_user = [m for m in messages if m["role"] == "user"]
```

> 读法：`[对每个元素做什么 for 元素 in 可迭代对象 if 条件]`

---

## 3. 类型注解：让你和编辑器都不迷路

```python
def embed(text: str, model: str = "text-embedding-3-small") -> list[float]:
    """把文本转成向量。"""
    return [0.1, 0.2, 0.3]      # 假数据

def chat(messages: list[dict], temperature: float = 0.7) -> str:
    return "模型回复"
```

Python **不强制**检查类型，但注解有三大好处：
1. VS Code 会给你**精准补全**（写 `messages[0].` 就提示 `["role"]`）
2. 别人（和三个月后的你）能立刻看懂函数怎么用
3. 配合 `pydantic` 可以自动校验数据（第 5 天会用到）

常用写法：

```python
from typing import Optional, Any

def find_user(uid: int) -> Optional[dict]:   # 可能返回 None
    ...

def process(data: list[str] | None) -> dict[str, Any]:   # Python 3.10+ 写法
    return {}
```

> **AI 相关**：几乎所有现代 AI 库（openai、langchain、pydantic）都重度使用类型注解，
> 不会读注解，你在编辑器里就得不到补全，写代码速度会慢一倍。

---

## 4. 异常处理：程序不能一碰错误就崩

```python
# 不处理：报错直接崩
# age = int("abc")     # ValueError

# 处理：程序继续跑
try:
    age = int("abc")
except ValueError as e:
    print("转换失败：", e)
    age = 0
```

### 完整结构 + 常见异常类型

```python
import json

def parse_model_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:       # 最常见：模型返回的不是合法 JSON
        print(f"JSON 解析失败: {e}")
        return {}
    except Exception as e:                  # 兜底（放最后）
        print(f"未知错误: {type(e).__name__}: {e}")
        return {}
    finally:
        print("无论如何都会执行（比如记日志）")
```

| 异常 | 什么时候出现 | AI 场景 |
|---|---|---|
| `ValueError` | 值不对，如 `int("abc")` | 配置项格式错 |
| `TypeError` | 类型不对，如 `"5" + 5` | 把字符串发给了要整数的参数 |
| `KeyError` | 字典没这个键，`d["x"]` | API 返回结构变了 |
| `IndexError` | 列表越界 | 空消息列表取 `[0]` |
| `FileNotFoundError` | 文件不存在 | 读知识库文档 |
| `requests.exceptions.Timeout` | 请求超时 | 调大模型接口 |
| `json.JSONDecodeError` | 不是合法 JSON | 模型输出格式跑偏 |

### ★ 重试：调用 AI API 的必备技能

```python
import time

def call_with_retry(fn, retries: int = 3, delay: float = 1.0):
    """失败就重试，每次等待时间翻倍（指数退避）。"""
    for attempt in range(1, retries + 1):
        try:
            return fn()
        except Exception as e:
            print(f"第 {attempt} 次失败：{e}")
            if attempt == retries:
                raise                     # 最后一次还失败，就抛出去
            time.sleep(delay)
            delay *= 2                    # 1s → 2s → 4s
```

> 网络请求 + 模型服务偶尔抽风是常态。**没有重试的 AI 代码不算能上线。**

---

## 5. 文件与路径：读写知识库、日志、配置

### 传统写法

```python
# 写（w 覆盖，a 追加，encoding 一定要写 utf-8！）
with open("notes.txt", "w", encoding="utf-8") as f:
    f.write("第一行\n")
    f.write("第二行\n")

# 读全部
with open("notes.txt", "r", encoding="utf-8") as f:
    content = f.read()
    print(content)

# 逐行读（大文件用这个，不占内存）
with open("notes.txt", "r", encoding="utf-8") as f:
    for line in f:
        print(line.strip())
```

> `with` 会自动关文件，**永远用 `with`，不要手动 `f.close()`**。

### 现代写法：pathlib（推荐）

```python
from pathlib import Path

base = Path("data")
base.mkdir(exist_ok=True)                 # 建目录（已存在也不报错）

p = base / "kb.txt"                       # 用 / 拼路径，跨平台
p.write_text("知识库内容", encoding="utf-8")
print(p.read_text(encoding="utf-8"))
print(p.exists(), p.suffix, p.stem)       # True .txt kb

# 遍历目录下所有 .md 文件（做 RAG 读文档时就这么写）
docs = list(Path("docs").glob("**/*.md"))
files = [f for f in Path(".").rglob("*.py") if ".venv" not in str(f)]
```

### JSON 读写：AI 项目的通用数据格式

```python
import json
from pathlib import Path

data = {
    "model": "gpt-4o-mini",
    "history": [{"role": "user", "content": "你好"}],
}

# 写：ensure_ascii=False 才能正常显示中文！
Path("session.json").write_text(
    json.dumps(data, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

# 读
loaded = json.loads(Path("session.json").read_text(encoding="utf-8"))
print(loaded["history"][0]["content"])
```

> **`ensure_ascii=False` 是中文项目的救命参数**，不加会变成 `\u4f60\u597d` 这种乱码。

---

## 6. 类（class）：打包状态 + 行为

新手不必深究面向对象，**只要会"看"和"用"就够**，但下面这个模式你要会写：

```python
class ChatSession:
    """一次对话会话：维护历史 + 统计消耗。"""

    def __init__(self, system_prompt: str = "你是一个有用的助手"):
        """构造函数：创建对象时自动调用。"""
        self.messages = []                                  # 实例属性
        self.total_tokens = 0
        self.system_prompt = system_prompt
        self.messages.append({"role": "system", "content": system_prompt})

    def add_user(self, text: str) -> None:
        self.messages.append({"role": "user", "content": text})

    def add_assistant(self, text: str, tokens: int = 0) -> None:
        self.messages.append({"role": "assistant", "content": text})
        self.total_tokens += tokens

    def last_user(self) -> str:
        for m in reversed(self.messages):
            if m["role"] == "user":
                return m["content"]
        return ""

    def summary(self) -> str:
        return f"共 {len(self.messages)} 条消息，消耗 {self.total_tokens} tokens"


# 使用
s = ChatSession("你是 Python 助教")
s.add_user("什么是类？")
s.add_assistant("类是对象的模板。", tokens=42)
s.add_user("什么是对象？")
print(s.last_user())
print(s.summary())
```

关键点：
- `__init__` 是初始化方法，`self` 代表"这个对象自己"，**每个方法第一个参数都必须是 self**
- `self.xxx = ...` 创建实例属性
- `类名()` 就是创建对象（实例化）

### dataclass：专门装数据的类（AI 项目里到处都是）

```python
from dataclasses import dataclass, field

@dataclass
class Document:
    doc_id: str
    text: str
    source: str = "unknown"
    tags: list[str] = field(default_factory=list)   # 可变默认值用 field

doc = Document(doc_id="d1", text="Python 是一门语言", source="手册.md")
print(doc.text)
print(doc)     # 自动生成好读的打印格式
```

---

## 7. 模块与导入

```python
# 方式 1：导入整个模块
import json
json.loads("{}")

# 方式 2：导入指定名字
from pathlib import Path

# 方式 3：起别名（社区惯例，写 AI 代码一定要会）
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# 方式 4：自己的文件也是模块
# utils.py 里定义 def clean(t): ...
from utils import clean
```

### 包结构（一个 AI 项目大概长这样）

```
my_ai_app/
├── .venv/
├── pyproject.toml          # 依赖声明（uv/pip 用）
├── .env                    # 密钥（★ 不要提交到 git）
├── main.py                 # 入口
├── app/
│   ├── __init__.py         # 有这个文件才算"包"
│   ├── llm.py              # 封装模型调用
│   ├── retriever.py        # 检索
│   └── utils.py            # 工具函数
├── data/                   # 知识库文档
└── tests/                  # 测试
```

### ★ 环境变量：密钥绝不能写死在代码里

```python
import os
from pathlib import Path

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise SystemExit("请先设置环境变量 OPENAI_API_KEY")

# 用 .env 文件（需要 pip install python-dotenv）
from dotenv import load_dotenv
load_dotenv()                                   # 读取同目录 .env
api_key = os.getenv("OPENAI_API_KEY")
```

`.env` 文件内容：

```
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
OPENAI_BASE_URL=https://api.openai.com/v1
```

> **三条铁律**：密钥进 `.env`、`.env` 进 `.gitignore`、代码里只读 `os.getenv()`。
> 把 key 硬编码进代码再传 GitHub，是最常见的"被刷爆账单"事故。

---

## 8. 常用标准库速查（AI 项目高频）

```python
import re          # 正则：清洗文本
re.findall(r"\d+", "共 128 tokens，耗时 3 秒")     # ['128', '3']

import time        # 计时、延时
t0 = time.time(); time.sleep(0.1); print(f"耗时 {time.time()-t0:.3f}s")

from datetime import datetime
datetime.now().strftime("%Y-%m-%d %H:%M:%S")      # 日志时间戳

import hashlib     # 生成 ID / 缓存键
hashlib.md5("文本".encode()).hexdigest()[:8]

import uuid
str(uuid.uuid4())                                  # 唯一 ID

import random
random.choice(["A", "B"]); random.sample(range(100), 5)

from collections import Counter, defaultdict
Counter(["a", "b", "a"])                           # {'a': 2, 'b': 1}
```

**正则小抄**（处理模型输出时很有用）：

```python
import re
text = "答案如下：```json\n{\"name\": \"小明\"}\n```"

# 提取代码块里的内容
m = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
print(m.group(1).strip() if m else text)
```

---

## 9. 综合练习：写一个"模型调用封装"骨架

不用真的联网，把结构写对就行（第 6 天会填上真实现）：

```python
# llm_client.py
import os
import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Reply:
    text: str
    tokens: int = 0


class LLMClient:
    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.7):
        self.model = model
        self.temperature = temperature
        self.history: list[dict] = []
        self.log_path = Path("llm_log.jsonl")

    def _build_payload(self, prompt: str) -> dict:
        messages = self.history + [{"role": "user", "content": prompt}]
        return {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
        }

    def chat(self, prompt: str) -> Reply:
        payload = self._build_payload(prompt)
        # TODO: 第 6 天在这里换成真的 HTTP 请求
        text = f"[模拟回复] 收到 {len(payload['messages'])} 条消息"
        tokens = len(text)

        self.history.append({"role": "user", "content": prompt})
        self.history.append({"role": "assistant", "content": text})
        self._log(payload, text)
        return Reply(text=text, tokens=tokens)

    def _log(self, payload: dict, reply: str) -> None:
        record = {"model": self.model, "payload": payload, "reply": reply}
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def reset(self) -> None:
        self.history.clear()


if __name__ == "__main__":
    client = LLMClient()
    print(client.chat("你好").text)
    print(client.chat("我叫小明").text)
    print(f"历史长度：{len(client.history)}")
    print("日志文件存在：", client.log_path.exists())
```

> `if __name__ == "__main__":` 的含义：**只有直接运行这个文件时才执行，被 import 时不执行。**
> 自己的测试代码都写在里面，这是标准做法。

---

## 10. 今日作业

1. 把第 9 节的 `llm_client.py` 敲一遍跑通，检查 `llm_log.jsonl` 里的内容。
2. 写函数 `chunk_text(text: str, size: int = 20) -> list[str]`：把长文本按 `size` 个字符切块（RAG 要用，第 8 天会回来感谢自己）。
3. 用 `pathlib` 统计当前目录下所有 `.py` 文件的行数总和。
4. 给 `call_with_retry` 加一个参数 `on_error: str = "raise"`，当它是 `"ignore"` 时失败返回 `None`。

---

## 11. 一分钟自测

- [ ] 默认参数能不能用 `[]`？（答：不能，用 `None` + 内部判断）
- [ ] `**kwargs` 收集什么？（答：关键字参数，打包成字典）
- [ ] 读文件为什么必须写 `encoding="utf-8"`？（答：Windows 默认 GBK，中文会乱码）
- [ ] `json.dumps` 中文乱码怎么办？（答：`ensure_ascii=False`）
- [ ] `if __name__ == "__main__":` 有什么用？（答：区分"直接运行"和"被导入"）
- [ ] 密钥应该放哪？（答：`.env` 环境变量，代码里 `os.getenv` 读）

---

上一课 → [`01_Python语法速通A_基础.md`](01_Python语法速通A_基础.md) ｜ 下一课 → [`03_AI必备数据三件套.md`](03_AI必备数据三件套.md)
