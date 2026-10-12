# 🤖 AI 应用速查（手机版）

> 第 6 天之后每天都要看。
> 提示词模板 + RAG 骨架 + Agent 骨架 + 成本优化，全在这里。

---

## 0️⃣ 一张图记住全部

```
你的程序
   │  POST /v1/chat/completions
   │  Header: Bearer sk-xxx
   │  Body: {model, messages[...]}
   ▼
大模型
   │  返回 JSON
   ▼
你的程序解析 → 使用
```

**一句话：大模型就是一个 HTTP 接口。**
**你要做的事：决定往 messages 里塞什么。**

---

## 1️⃣ 三个必背名词

**messages**
对话历史数组
```python
[{"role": "user", "content": "你好"}]
```

**role 的四种值**
- `system` → 设定人设和规则
- `user` → 用户说的话
- `assistant` → 模型的回复
- `tool` → 工具执行的结果

**token**
计费和处理的最小单位
中文大约 **1 字 ≈ 1–1.5 token**

---

## 2️⃣ 最小可用调用（记住这个骨架）

```python
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
    timeout=90.0,
    max_retries=3,
)

resp = client.chat.completions.create(
    model=os.getenv("OPENAI_MODEL"),
    messages=[
        {"role": "system", "content": "你是技术助教"},
        {"role": "user", "content": "什么是列表"},
    ],
    temperature=0.7,
    max_tokens=800,
)

print(resp.choices[0].message.content)
print(resp.usage.total_tokens)
```

**换厂商只改 `.env` 两行**
```
OPENAI_BASE_URL=...
OPENAI_MODEL=...
```

---

## 3️⃣ 参数怎么调

**temperature**（随机性 0–1）
- `0` → 抽取、分类、代码、JSON
- `0.3` → 事实问答
- `0.7` → 通用对话
- `0.9` → 创意写作

**max_tokens**（输出上限）
**必须设！** 不然模型啰嗦烧钱

**top_p**
一般别动，只调 temperature 就行

**seed**
需要结果可复现时设

---

## 4️⃣ 流式输出（打字机效果）

```python
stream = client.chat.completions.create(
    model=MODEL,
    messages=messages,
    stream=True,
    stream_options={"include_usage": True},
)

pieces = []
for chunk in stream:
    if getattr(chunk, "usage", None):
        # ★ 用量在最后一帧
        print("tokens:", chunk.usage.total_tokens)
    if not chunk.choices:
        continue
    piece = chunk.choices[0].delta.content
    if piece:
        pieces.append(piece)
        print(piece, end="", flush=True)

answer = "".join(pieces)
```

**三个注意点**
1. 有些帧没有 choices，要判断
2. `usage` 在最后一帧，要在循环里累加
3. 流式时**没法对整段做后处理**
   （要解析 JSON 就先收集完）

---

## 5️⃣ 让模型返回 JSON（工程化关键）

**方法一：提示词约束（通用）**
```python
prompt = f"""从评论中抽取信息，只输出 JSON，
不要任何解释文字。

格式：
{{
  "sentiment": "positive/negative/neutral",
  "score": 1 到 5 的整数,
  "pros": ["优点"],
  "cons": ["缺点"]
}}

评论：
{review}
"""
```
配 `temperature=0`

**方法二：官方开关**
```python
response_format={"type": "json_object"}
```

**方法三：Pydantic 校验（生产必备）**
```python
from pydantic import BaseModel, Field

class Review(BaseModel):
    sentiment: str
    score: int = Field(ge=1, le=5)
    pros: list[str] = []
    cons: list[str] = []

review = Review.model_validate(data)   # 自动校验
```

**铁律**
凡是要进数据库/进业务逻辑的模型输出
**必须校验**，模型有 1% 概率给你惊喜

---

## 6️⃣ 提示词模板库 📋

**① 信息抽取**
```
从下面的文本中抽取信息，只输出 JSON。
字段：{字段列表}
找不到的字段填空，不要编造。

文本：
{text}
```

**② 分类**
```
把下面的用户反馈分成这几类之一：
{类别列表}

只输出类别名称，不要解释。

反馈：{text}
```

**③ 摘要**
```
用 {N} 句话总结下面的内容，保留关键数字和结论。

内容：
{text}
```

**④ RAG 问答（★ 最重要）**
```
你是一个严谨的文档问答助手。规则：
1. 只依据【参考资料】回答
2. 资料没有答案就直接说"根据现有资料无法回答"
3. 不要使用你自己的知识补充
4. 末尾用 [来源: 文件名] 标注

【参考资料】
{context}

【问题】
{question}
```

**⑤ 改写查询（提升检索命中率）**
```
把用户问题改写成 3 个适合检索的短查询，
每行一个，不要编号，保留关键实体。

用户问题：{question}
```

**⑥ 评分 / LLM as Judge**
```
给答案打分，1-5 分。
评分标准：准确性、完整性、是否编造。
只输出 JSON：{"score": 4, "reason": "..."}

问题：{q}
参考答案：{ref}
模型答案：{ans}
```

---

## 7️⃣ RAG 完整骨架 ★★

**两条流水线**

离线（文档变时重做）：
```
读文档 → 切块 → 算向量 → 存库
```

在线（每次提问）：
```
问题 → 向量化 → 检索 top-k
→ 组装提示词 → 生成 → 带来源返回
```

**索引构建**
```python
chunks = []
for f in Path("docs").glob("**/*.md"):
    text = f.read_text(encoding="utf-8")
    for c in chunk_text(text, size=400,
                        overlap=80, source=f.name):
        chunks.append(c)

vectors = embedder.encode([c.text for c in chunks])

store = VectorStore()
store.add_many(
    [c.text for c in chunks],
    vectors,
    [{"source": c.source, "index": c.index}
     for c in chunks],
)
store.save("index.json")
```

**检索 + 回答**
```python
qv = embedder.encode_one(question)
hits = store.search(qv, top_k=4)

context = "\n\n".join(
    f"[资料{i}] 来源：{h['metadata']['source']}\n{h['text']}"
    for i, h in enumerate(hits, 1)
)

prompt = RAG_PROMPT.format(
    context=context, question=question)

# 调模型生成...
```

---

## 8️⃣ 切块参数怎么定

**中文**
- 大小：**300–800 字符**
- 重叠：**10%–20%**

**英文**
- 大小：200–500 token

**太大**
- 混入无关信息
- 稀释相关性
- 费 token

**太小**
- 语义不完整
- 检索到也不知道在说什么

**更好**
按文档结构切
Markdown 按标题、代码按函数

---

## 9️⃣ RAG 效果不好排查表 ★

按顺序查，**别一上来就换模型**

**1. 切块太大** → 调小到 300–400

**2. 没归一化** → 加归一化再点积

**3. embedding 不适合中文**
→ 换 `BAAI/bge-small-zh-v1.5`

**4. 索引没重建** → 加 `--rebuild`

**5. 用户用词和文档不同**
→ 加查询改写

**6. 专有名词/型号/代码搜不到**
→ 加混合检索（关键词兜底）

**7. 排序不准** → 加 rerank

**8. 才轮到考虑换生成模型**

---

## 🔟 三个最有效的优化手段

**① 多查询检索**
把问题改写成 3 个查询
各查一次，合并去重

通常命中率 **62% → 85%**

**② 混合检索**
```
最终分 = 0.7 × 向量分 + 0.3 × 关键词分
```

**③ Rerank**
先粗排 20 条
再用更强的模型精排取 3 条

---

## 1️⃣1️⃣ Agent 骨架 ★

**核心认知**
**模型不会真的执行你的函数**
它只返回"我要调用谁、参数是什么"
执行永远在你的代码里

**完整循环**
```python
messages = [
    {"role": "system", "content": "需要计算时必须用工具"},
    {"role": "user", "content": question},
]

for step in range(MAX_STEPS):     # ★ 必须有上限
    resp = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=TOOLS_SCHEMA,
        tool_choice="auto",
        temperature=0,
    )
    msg = resp.choices[0].message

    # 不调工具 → 直接回答，结束
    if not msg.tool_calls:
        return msg.content

    # 要调工具
    messages.append(msg)          # ★ 必须加，不能省

    for call in msg.tool_calls:
        name = call.function.name
        try:
            args = json.loads(
                call.function.arguments or "{}")
        except json.JSONDecodeError:
            args = {}

        fn = REGISTRY.get(name)
        result = fn(**args) if fn else "未注册的工具"

        messages.append({
            "role": "tool",
            "tool_call_id": call.id,   # ★ 必须对应
            "content": str(result),
        })
```

---

## 1️⃣2️⃣ 工具说明书怎么写

```python
{
  "type": "function",
  "function": {
    "name": "get_weather",
    "description": "查询城市天气。当用户问到天气时使用。",
    "parameters": {
      "type": "object",
      "properties": {
        "city": {
          "type": "string",
          "description": "城市名，如 北京、上海"
        }
      },
      "required": ["city"]
    }
  }
}
```

**description 是调优第一杠杆**
要写清：
1. **什么时候用**
2. 参数格式（给例子）
3. 返回什么

> 把 description 写模糊，调用准确率立刻下降
> —— 这是最值得亲手做一次的实验

---

## 1️⃣3️⃣ Agent 四个坑

**1. 没 append 模型的 tool_calls 消息**
→ 报错 "role 'tool' must be a response
   to a preceding message with 'tool_calls'"

**2. tool_call_id 没对应**
→ 一次可能并行多个调用，靠 id 匹配

**3. 没有 max_steps**
→ 模型反复调用同一工具，烧光余额

**4. 参数解析没包 try**
→ 模型偶尔返回不合法 JSON，程序直接崩

---

## 1️⃣4️⃣ 工具安全红线 🔒

**路径穿越**
模型调 `read_file("../../etc/passwd")`
→ 必须限制在项目目录内

**命令注入**
不要暴露 shell

**任意代码执行**
用 Docker / 子进程沙箱 + 超时

**数据外泄**
屏蔽 `.env`、`*.key`、`*.pem`

**费用爆炸**
`max_steps` + 单次会话预算上限

**提示注入**
网页里藏"忽略之前的指令"
→ 工具返回的内容**当数据，绝不当指令**

> 一句话：**模型给你的东西，永远当不可信输入**

---

## 1️⃣5️⃣ 成本优化清单 💰

**1. `max_tokens` 永远设上限**
最便宜的保险

**2. 短任务用小模型**
分类/改写/抽取 → 便宜模型
复杂推理 → 才上大模型

**3. 裁掉没用的历史**
只保留最近 N 轮

**4. 能不用模型就不用**
关键词、正则、业务规则能解决的不问模型

**5. 缓存重复请求**
同一个问题问两次 → 读缓存

**6. 精简 system prompt**
每次请求都重复计费
别写 2000 字人设

**7. 批量请求**
embedding 一次传 64 条

**8. 加成本看板**
用 pandas 统计每次调用的花费

---

## 1️⃣6️⃣ 稳健封装的四个必备件

**① 超时**
```python
OpenAI(..., timeout=90.0)
```
大模型生成慢，超时给足

**② 重试**
```python
OpenAI(..., max_retries=3)
```
或自己写指数退避

**③ 日志**
每次调用记录：
模型 / messages / 回复 /
tokens / 耗时 → 写 jsonl

**④ 成本统计**
```python
cost = (prompt_tokens * price_in
        + completion_tokens * price_out) / 1e6
```

---

## 1️⃣7️⃣ 常见报错一句话解决

**401** 密钥错 → 检查 `.env` 有没有引号、空格

**404** 模型名错 / base_url 不匹配

**429** 限流 → 退避重试，并发降到 2–3

**超时** → `timeout=120`，或设代理

**400 context length exceeded**
→ 裁剪历史、限制检索片段长度

**输出被截断**
→ `finish_reason == "length"`，调大 max_tokens

**模型不遵守 JSON 指令**
→ `temperature=0` + 给完整格式示例
  + `response_format` + 正则兜底

---

## 1️⃣8️⃣ 面试必问 8 问（速答版）

**1. RAG 完整流程？**
离线建索引 + 在线检索生成

**2. 怎么切块？为什么要重叠？**
300–800 字符、10–20% 重叠
防止关键句被切在边界上

**3. 检索不准怎么排查？**
切块 → 归一化 → 模型 → 重建
→ 查询改写 → 混合检索 → rerank

**4. 怎么防编造？**
提示词强约束 + 标注来源
+ 建拒答测试集验证

**5. Function Calling 原理？**
模型只返回调用请求，执行在你代码里

**6. Agent 怎么会死循环？**
工具报错后反复重试
→ max_steps + 成本熔断 + 报错回传

**7. 怎么降成本？**
小模型分流、历史裁剪、缓存
精简提示词、批处理、限制 max_tokens

**8. 怎么评估效果？**
建 golden set
测命中率/准确率/幻觉率/延迟/成本

---

## 1️⃣9️⃣ 关键数字速记

**中文 token 估算**
1 字 ≈ 1–1.5 token

**切块**
300–800 字符，重叠 10–20%

**检索**
top-k 一般取 3–5

**历史**
保留最近 10 轮

**余弦相似度**
范围 -1 到 1，越大越相似

**并发**
批处理 2–4 线程起步

---

## 2️⃣0️⃣ 每天开工前问自己三句

**1. 这个任务真的需要大模型吗？**
规则能解决的别上模型

**2. 我给它足够的上下文了吗？**
模型不知道你的私有数据

**3. 输出怎么校验？**
要进业务逻辑就必须校验

---

配套 → `手机版_Python速查.md`、`手机版_背诵卡.md`
完整版 → `../05_调用大模型API.md`、`../08_项目_RAG文档问答.md`
