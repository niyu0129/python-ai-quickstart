# 第 2 天：Python 语法速通 A —— 基础

> 今天把"能写逻辑"的部分全部拿下：变量、类型、字符串、列表、字典、判断、循环。
> **每个知识点后面都有一行「AI 里用来干嘛」**，看不懂语法就先看用途，有目标才学得进去。

---

## 1. 变量：名字 = 值

```python
name = "小明"        # 字符串
age = 22             # 整数
height = 1.75        # 浮点数
is_student = True    # 布尔值（True / False，首字母大写）
nothing = None       # 空值，表示"没有"

print(name, age, height, is_student)
```

- Python 是**动态类型**：不用写 `int age = 22;`，赋值时自动判断类型。
- 变量名规则：字母/数字/下划线，不能数字开头，区分大小写。**用下划线命名**：`user_name`、`api_key`。

```python
type(age)      # <class 'int'>
type(height)   # <class 'float'>
```

**类型转换**（API 返回值经常是字符串，需要转）：

```python
int("42")        # 42
float("3.14")    # 3.14
str(42)          # "42"
int(3.9)         # 3   ← 直接截断，不是四舍五入
```

> ⚠️ **AI 相关**：模型 API 返回的 token 数是整数，但配置文件读出来常常是字符串，类型转换是日常。

---

## 2. 字符串（str）—— AI 里 80% 的数据是字符串

```python
prompt = "请用一句话解释什么是大语言模型"
print(len(prompt))            # 长度
print(prompt[0])              # 第 0 个字符（从 0 开始！）
print(prompt[-1])             # 最后一个字符
print(prompt[0:5])            # 切片：第 0 到第 4 个字符（不含 5）
```

### f-string：最重要的一招

```python
name = "小明"
tokens = 128

print(f"用户 {name} 消耗了 {tokens} 个 token")        # 直接嵌变量
print(f"两倍是 {tokens * 2}")                          # 可以算表达式
print(f"保留两位小数：{3.14159:.2f}")                   # 3.14
print(f"百分比：{0.856:.1%}")                           # 85.6%
```

**AI 里的用法**（构建提示词的核心手法）：

```python
user_question = "什么是向量数据库？"
context = "向量数据库是专门存储和检索向量（embedding）的数据库。"

# 这就是 RAG 里组装提示词的真实写法
prompt = f"""请根据下面的资料回答用户问题，只使用资料中的信息。

【资料】
{context}

【用户问题】
{user_question}
"""
print(prompt)
```

### 常用字符串方法

```python
s = "  Hello, AI World  "

s.strip()              # 去掉两端空格 → "Hello, AI World"
s.lower()              # 转小写
s.upper()              # 转大写
s.replace("AI", "ML")  # 替换
s.split(",")           # 按逗号切分成列表 → ['Hello', ' AI World']
"a" in s               # 是否包含 → True
"-".join(["a", "b"])   # 拼接 → "a-b"

text = "  你好，\n世界  "
print(text.strip())    # 处理模型返回的多余换行/空格，非常常用
```

> **AI 相关**：模型返回的 JSON 常常带 ```json 代码块标记，用 `.replace()` + `.strip()` 清洗是标准动作。

---

## 3. 列表（list）：有序、可修改 —— 装"多条数据"

```python
scores = [90, 85, 77, 92]

scores[0]           # 90
scores[-1]          # 92
scores[1:3]         # [85, 77]  切片
len(scores)         # 4

scores.append(88)       # 末尾追加
scores.insert(0, 100)   # 在位置 0 插入
scores.remove(85)       # 删除第一个值为 85 的元素
scores.pop()            # 删除并返回最后一个
scores.sort()           # 原地排序（改变原列表）
scores.sort(reverse=True)
sorted(scores)          # 返回新列表，不改原列表
sum(scores), max(scores), min(scores)
```

### ★ AI 里的头号数据结构：消息列表

**所有多轮对话，本质都是一个列表在 append。**

```python
messages = [
    {"role": "system",    "content": "你是一个专业的 Python 助教。"},
    {"role": "user",      "content": "什么是列表？"},
    {"role": "assistant", "content": "列表是 Python 里有序可变的序列。"},
]

# 用户又问了新问题 → 追加进历史
messages.append({"role": "user", "content": "那字典呢？"})

# 发给模型时，整个列表一起发过去 —— 这就是"记忆"
for m in messages:
    print(f"{m['role']:>9}: {m['content'][:30]}")
```

> 记住这张图：`messages` 列表 = 对话记忆。第 6 天的聊天机器人，核心就是维护这个列表。

---

## 4. 字典（dict）：键值对 —— 配置、JSON、API 参数

```python
config = {
    "model": "gpt-4o-mini",
    "temperature": 0.7,
    "max_tokens": 512,
}

config["model"]                  # 取值
config["temperature"] = 0.2      # 改值
config["top_p"] = 1.0            # 新增键
config.get("timeout", 30)        # 取不到就返回默认值 30（安全取值，推荐）
"model" in config                # 判断键是否存在 → True

config.keys()      # 所有键
config.values()    # 所有值
config.items()     # 键值对

for k, v in config.items():
    print(k, "=", v)
```

**JSON 长这样，字典就长这样**（模型 API 的请求体就是嵌套字典）：

```python
payload = {
    "model": "gpt-4o-mini",
    "messages": [
        {"role": "user", "content": "你好"}
    ],
    "temperature": 0.7,
}
print(payload["messages"][0]["content"])   # 你好   ← 一层层剥开
```

> **AI 相关**：`requests.post(url, json=payload)` 一个 `json=` 参数就把字典变成 JSON 发出去。
> 嵌套字典取值是写 AI 代码时最高频的动作，务必练熟 `d["a"][0]["b"]`。

---

## 5. 元组（tuple）与集合（set）

```python
point = (10, 20)          # 元组：不可修改
x, y = point              # 解包（超常用）

rgb = (255, 128, 0)
r, g, b = rgb

# 集合：自动去重、无序
tags = {"python", "ai", "python", "llm"}
print(tags)               # {'python', 'ai', 'llm'}  ← 去重了
a = {1, 2, 3}
b = {3, 4}
a & b     # 交集 {3}
a | b     # 并集 {1, 2, 3, 4}
a - b     # 差集 {1, 2}
```

> **AI 相关**：元组用于 `(role, content)` 这种固定结构；集合用于"去重 + 快速判断是否见过"，比如去重文档 ID。

---

## 6. 判断（if / elif / else）

```python
score = 78

if score >= 90:
    print("优秀")
elif score >= 60:          # 注意是 elif，不是 else if
    print("及格")
else:
    print("不及格")
```

**Python 用缩进（4 个空格）表示层级，没有 `{}`。缩进错了程序就错了。**

```python
# 逻辑运算符：and / or / not （不是 && || !）
has_key = True
has_balance = False

if has_key and has_balance:
    print("可以调用 API")
elif has_key or has_balance:
    print("条件不完整")
else:
    print("都不能用")
```

**真值判断**（AI 代码里的常见写法）：

```python
api_key = ""
if not api_key:            # 空字符串、0、None、[]、{} 都算 False
    raise ValueError("请先配置 API Key")
```

---

## 7. 循环（for / while）

### for 循环：遍历

```python
# 遍历列表
for s in [90, 85, 77]:
    print(s)

# 带序号
for i, s in enumerate([90, 85, 77], start=1):
    print(f"第{i}名：{s}")

# 同时遍历两个列表
names = ["小明", "小红"]
ages = [22, 23]
for n, a in zip(names, ages):
    print(n, a)

# 遍历字典
config = {"model": "gpt-4o-mini", "temperature": 0.7}
for k, v in config.items():
    print(k, "→", v)
```

### range

```python
for i in range(5):        # 0,1,2,3,4
    print(i)

for i in range(1, 11):    # 1..10
    print(i)

for i in range(0, 100, 10):   # 0,10,...,90
    print(i)
```

### while + break / continue

```python
count = 0
while True:                     # 死循环，靠 break 退出
    count += 1
    if count == 3:
        continue                # 跳过本次，进入下一轮
    if count > 5:
        break                   # 跳出整个循环
    print(count)
```

### ★ AI 里的头号循环：逐块流式打印模型输出

```python
# 模拟流式返回（真实代码在第 6 天）
chunks = ["大", "语言", "模型", "是", "一种", "AI", "模型"]

full_text = ""
for chunk in chunks:
    full_text += chunk          # 累积全文
    print(chunk, end="", flush=True)   # end="" 不换行，flush 立即输出
print()                          # 收尾换行
print("完整内容：", full_text)
```

> **`end=""` + `flush=True`** 就是"打字机效果"的全部秘密。

---

## 8. 一个完整小练习：迷你对话历史管理器

把今天所有东西串起来，**照着敲一遍，然后改**：

```python
# chat_history.py
history = []          # 对话历史：列表
MAX_TURNS = 3         # 最多保留 3 轮

def add_message(role, content):
    history.append({"role": role, "content": content})
    # 只保留最近 MAX_TURNS*2 条（user+assistant 算一轮）
    while len(history) > MAX_TURNS * 2:
        history.pop(0)          # 删掉最老的一条
    return len(history)

add_message("user", "你好，请介绍一下自己")
add_message("assistant", "我是 AI 助手，很高兴认识你")
add_message("user", "Python 的列表是什么？")
add_message("assistant", "列表是有序可变的序列，用方括号表示")
add_message("user", "那字典呢？")

print(f"当前历史 {len(history)} 条：")
for i, msg in enumerate(history, 1):
    role = msg["role"]
    content = msg["content"]
    print(f"{i}. [{role}] {content}")

# 统计
roles = {m["role"] for m in history}
print("出现过的角色：", roles)
```

---

## 9. 今日作业

1. 建 `student.py`：用列表存 5 个学生的名字和分数（用字符串存名字会简单些），打印平均分、最高分、最低分。
2. 建 `prompt_builder.py`：定义 `system`、`context`、`question` 三个变量，用 f-string 拼出一段完整的提示词并打印。
3. 把第 8 节的 `chat_history.py` 改造成：**超过 3 轮时不是删掉，而是打印一句"（历史已超出限制）"**。
4. 挑战：用 `while` 循环写一个命令行计算器，支持 `+ - * /`，输入 `q` 退出。

---

## 10. 一分钟自测

- [ ] `a = "5"` 和 `b = 5`，`a + b` 会怎样？（答：报 TypeError，需 `int(a) + b`）
- [ ] `lst = [1,2,3]`，`lst[1:]` 是什么？（答：`[2, 3]`）
- [ ] 字典安全取值用哪个方法？（答：`.get(key, 默认值)`）
- [ ] 遍历列表同时拿到序号用什么？（答：`enumerate`）
- [ ] 多轮对话的记忆存在什么结构里？（答：`messages` 列表，每个元素是 `{"role":..., "content":...}`）

---

下一课 → [`02_Python语法速通B_进阶.md`](02_Python语法速通B_进阶.md)
