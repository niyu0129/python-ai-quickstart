# 🐍 Python 速查（手机版）

> 写代码时随手查。**建议存备忘录，用搜索找关键词。**
> 只收录 AI 应用开发真正用得上的。

---

## 1️⃣ 变量与类型

```python
name = "小明"      # 字符串
age = 22           # 整数
price = 9.9        # 浮点
ok = True          # 布尔（大写开头）
nothing = None     # 空值
```

类型转换：
```python
int("42")      # 42
float("3.14")  # 3.14
str(42)        # "42"
int(3.9)       # 3（截断，不是四舍五入）
```

查类型：
```python
type(age)      # <class 'int'>
```

---

## 2️⃣ f-string（最重要的一招）

```python
name = "小明"
n = 128

f"用户 {name} 用了 {n} 个 token"
f"两倍是 {n * 2}"          # 可以算表达式
f"保留两位：{3.14159:.2f}"  # 3.14
f"百分比：{0.856:.1%}"      # 85.6%
```

**拼提示词全靠它：**
```python
prompt = f"""根据资料回答问题。

【资料】
{context}

【问题】
{question}"""
```

---

## 3️⃣ 字符串常用方法

```python
s = "  Hello, AI  "

s.strip()              # 去两端空格
s.lower() / s.upper()  # 转大小写
s.replace("AI", "ML")  # 替换
s.split(",")           # 切成列表
"-".join(["a", "b"])   # 拼成 "a-b"
"AI" in s              # 是否包含
len(s)                 # 长度
s[0]  s[-1]  s[0:5]    # 索引、切片
```

**模型返回内容清洗（高频）：**
```python
text = "```json\n{...}\n```"
text.replace("```json", "").replace("```", "").strip()
```

---

## 4️⃣ 列表 list

```python
scores = [90, 85, 77]

scores[0]           # 90
scores[-1]          # 77（最后一个）
scores[1:3]         # [85, 77]
len(scores)         # 3

scores.append(88)      # 末尾追加
scores.insert(0, 100)  # 指定位置插入
scores.remove(85)      # 删除某个值
scores.pop()           # 删最后一个
scores.sort()          # 原地排序
sorted(scores)         # 返回新列表
sum(scores)  max(scores)  min(scores)
```

**★ 最重要的用法：多轮对话**
```python
messages = []
messages.append({"role": "user", "content": "你好"})
messages.append({"role": "assistant", "content": "你好呀"})

# 只保留最近 10 轮
messages = messages[-20:]
```

---

## 5️⃣ 字典 dict

```python
config = {"model": "gpt-4o-mini", "temperature": 0.7}

config["model"]                    # 取值
config["temperature"] = 0.2        # 改值
config["top_p"] = 1.0              # 新增
config.get("timeout", 30)          # ★ 取不到给默认值
"model" in config                  # 判断存在

config.keys()  config.values()  config.items()

for k, v in config.items():
    print(k, v)
```

**★ 嵌套字典（API 请求体就长这样）**
```python
payload = {
  "model": "gpt-4o-mini",
  "messages": [{"role": "user", "content": "你好"}],
  "temperature": 0.7,
}

payload["messages"][0]["content"]   # "你好"
```

安全取嵌套值（防崩）：
```python
choices = data.get("choices", [])
if not choices:
    print("返回异常：", list(data.keys()))
```

---

## 6️⃣ 元组与集合

```python
point = (10, 20)      # 元组，不可改
x, y = point          # 解包

tags = {"python", "ai", "python"}
# {'python', 'ai'}  ← 自动去重

a & b   # 交集
a | b   # 并集
a - b   # 差集
```

用途：
- 元组 → 固定结构 `(role, content)`
- 集合 → 去重、快速判断"见过没有"

---

## 7️⃣ 判断

```python
if score >= 90:
    print("优秀")
elif score >= 60:
    print("及格")
else:
    print("不及格")
```

**注意**
- 是 `elif`，不是 `else if`
- 逻辑用 `and` / `or` / `not`（不是 && || !）
- 缩进 4 个空格，没有 `{}`

**真值判断（AI 代码常见）**
```python
api_key = ""
if not api_key:
    raise ValueError("请配置 API Key")
```
空字符串、0、None、[]、{} 都算 False

---

## 8️⃣ 循环

```python
for s in [90, 85]:        # 遍历
    print(s)

for i, s in enumerate(lst, start=1):   # 带序号
    print(i, s)

for n, a in zip(names, ages):          # 同时遍历
    print(n, a)

for i in range(5):        # 0,1,2,3,4
for i in range(1, 11):    # 1..10
```

**while + break / continue**
```python
count = 0
while True:
    count += 1
    if count == 3:
        continue     # 跳过本次
    if count > 5:
        break        # 跳出循环
```

**★ 流式打印（打字机效果）**
```python
for chunk in stream:
    print(chunk, end="", flush=True)
```
`end=""` 不换行，`flush=True` 立即显示

---

## 9️⃣ 函数

```python
def greet(name, temperature=0.7):
    """打招呼。"""
    return f"你好 {name}"
```

**★ 参数的各种花样**
```python
def f(a, b=1, *args, **kwargs):
    ...
```
- `b=1` → 默认参数
- `*args` → 任意个位置参数
- `**kwargs` → 任意个关键字参数

**多返回值**
```python
def stats(nums):
    return min(nums), max(nums)

lo, hi = stats([1, 2, 3])
```

**★ 必须记住的坑**
```python
# ❌ 默认值不能是可变对象
def bad(x, box=[]):
    box.append(x)
    return box
bad(1)   # [1]
bad(2)   # [1, 2]  ← 出问题了

# ✅ 正确写法
def good(x, box=None):
    if box is None:
        box = []
    box.append(x)
    return box
```

---

## 🔟 推导式

```python
# 列表推导式（一行顶五行）
squares = [n * n for n in range(5)]
evens = [n for n in range(10) if n % 2 == 0]

# 清洗字符串列表
raw = ["  你好 ", "\n世界"]
cleaned = [s.strip() for s in raw if s.strip()]

# 字典推导式
lengths = {w: len(w) for w in ["apple", "fig"]}

# 处理 API 返回
contents = [m["content"] for m in messages]
```

读法：
```
[对每个元素做什么 for 元素 in 可迭代 if 条件]
```

---

## 1️⃣1️⃣ 异常与重试

```python
try:
    n = int("abc")
except ValueError as e:
    print("转换失败：", e)
    n = 0
except Exception as e:          # 兜底，放最后
    print("未知错误：", e)
finally:
    print("无论如何都执行")
```

**常见异常速查**
- `ValueError` 值不对
- `TypeError` 类型不对
- `KeyError` 字典没这个键
- `IndexError` 列表越界
- `FileNotFoundError` 文件不存在
- `JSONDecodeError` 不是合法 JSON

**★ 指数退避重试（调 API 必备）**
```python
import time

def retry(fn, times=3, delay=1.0):
    for i in range(1, times + 1):
        try:
            return fn()
        except Exception as e:
            print(f"第 {i} 次失败：{e}")
            if i == times:
                raise
            time.sleep(delay)
            delay *= 2      # 1s → 2s → 4s
```

---

## 1️⃣2️⃣ 文件与路径

```python
from pathlib import Path

p = Path("data/kb.txt")
p.write_text("内容", encoding="utf-8")
text = p.read_text(encoding="utf-8")

p.exists()   p.suffix   p.stem

# 建目录
Path("data").mkdir(exist_ok=True)

# 遍历文件
files = list(Path("docs").glob("**/*.md"))

# 用 / 拼路径，跨平台
p = Path("data") / "kb" / "a.md"
```

**★ 相对路径的基准目录**
```python
BASE = Path(__file__).parent   # 脚本所在目录
kb = BASE / "data" / "kb.txt"
```
比 `Path("data/kb.txt")` 可靠得多

---

## 1️⃣3️⃣ JSON

```python
import json

data = {"model": "gpt", "history": []}

# 写（★ ensure_ascii=False 中文才正常）
Path("s.json").write_text(
    json.dumps(data, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

# 读
loaded = json.loads(Path("s.json").read_text(encoding="utf-8"))
```

**★ 从模型输出里稳健抠 JSON**
```python
import re, json

def extract_json(text):
    text = (text or "").strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if m:
        text = m.group(1).strip()
    s, e = text.find("{"), text.rfind("}")
    if s != -1 and e != -1:
        text = text[s:e+1]
    return json.loads(text)
```

---

## 1️⃣4️⃣ 类

```python
class ChatSession:
    def __init__(self, system="你是助手"):
        self.messages = []
        self.tokens = 0
        self.messages.append(
            {"role": "system", "content": system})

    def add_user(self, text):
        self.messages.append(
            {"role": "user", "content": text})

    def summary(self):
        return f"{len(self.messages)} 条消息"


s = ChatSession("你是助教")
s.add_user("什么是类")
print(s.summary())
```

要点：
- `__init__` 创建对象时自动调用
- `self` 是"这个对象自己"，每个方法第一个参数
- `self.xxx = ...` 创建实例属性

**dataclass（装数据的类）**
```python
from dataclasses import dataclass, field

@dataclass
class Document:
    doc_id: str
    text: str
    source: str = "unknown"
    tags: list[str] = field(default_factory=list)
```

---

## 1️⃣5️⃣ 模块与导入

```python
import json
from pathlib import Path
import numpy as np          # 别名（社区惯例）
import pandas as pd
import matplotlib.pyplot as plt

from utils import clean      # 自己的文件也是模块
```

**`if __name__ == "__main__":`**
只有直接运行这个文件时才执行
被 import 时不执行

**★ 环境变量（密钥管理）**
```python
import os
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("OPENAI_API_KEY")
if not key:
    raise SystemExit("请在 .env 配置 OPENAI_API_KEY")
```

三条铁律：
1. 密钥进 `.env`
2. `.env` 进 `.gitignore`
3. 代码里只读 `os.getenv()`

---

## 1️⃣6️⃣ 常用标准库

```python
import re
re.findall(r"\d+", "共 128 tokens")   # ['128']

import time
t0 = time.time()
# ...
print(f"耗时 {time.time()-t0:.2f}s")

from datetime import datetime
datetime.now().strftime("%Y-%m-%d %H:%M:%S")

import uuid
str(uuid.uuid4())        # 唯一 ID

from collections import Counter
Counter(["a", "b", "a"])  # {'a': 2, 'b': 1}
```

---

## 1️⃣7️⃣ npm 式对照：装包

```
# uv（推荐，快）
uv add requests
uv pip install -r requirements.txt

# 原生 pip
python -m pip install requests

# 国内换源
python -m pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 1️⃣8️⃣ 六个最常踩的坑

**1. 中文标点**
`print（"你好"）` ← 全角括号，报 SyntaxError

**2. 忘了 return**
```python
def add(a, b):
    a + b       # ❌ 没 return，返回 None
```

**3. 类型不匹配**
```python
"年龄：" + 22        # ❌ TypeError
f"年龄：{22}"        # ✅
```

**4. 空列表取 [0]**
```python
if messages:               # ✅ 先判空
    print(messages[0])
```

**5. 字符串和数字比较**
```python
"5" == 5     # False
int("5") == 5  # True
```

**6. 循环里发网络请求**
慢 10 倍 → 改用线程池

---

## 1️⃣9️⃣ 报错怎么读

```
Traceback (most recent call last):
  File "app.py", line 12        ← 出错的文件和行
    data["choices"][0]
KeyError: 'choices'             ← ★ 只看这一行
```

**流程**
1. 读最后一行 → 知道错误类型
2. 看上面的行号 → 定位到自己的代码
3. `print(type(x), repr(x)[:200])` 看变量
4. 还不行 → 把完整报错丢给 AI 问

---

## 2️⃣0️⃣ 每天必用的三行

```python
# 看这行到底发了什么（调 API 前必做）
print(len(messages), [m["role"] for m in messages])

# 看变量类型和值
print(type(x), repr(x)[:200])

# 看耗时
t0 = time.time(); ...; print(f"{time.time()-t0:.2f}s")
```

---

配套 → `手机版_AI应用速查.md`
完整版 → `../01_Python语法速通A_基础.md`
