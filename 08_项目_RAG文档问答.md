# 第 9 天：项目二 —— RAG 文档问答系统

> **RAG（Retrieval-Augmented Generation，检索增强生成）**
> 一句话：**先从你的文档里查出相关内容，再把内容塞进提示词让模型回答。**
>
> 这是当前企业 AI 落地最主流的形态。学会它，你就能做"公司知识库问答""合同审查""客服机器人"。

---

## 1. 为什么需要 RAG？模型的三个硬伤

| 硬伤 | 表现 | RAG 怎么解决 |
|---|---|---|
| **不知道你的私有数据** | 问"我们公司的报销流程" → 它瞎编 | 把公司文档检索出来喂给它 |
| **知识有截止日期** | 问"昨天的新闻" → 它不知道 | 把最新资料检索出来喂给它 |
| **会一本正经地胡说** | 编造不存在的引用和数字 | 强制"只依据资料回答"，并要求给出处 |

**RAG 不训练模型，不花大钱，当天就能上线。** 这是它最大的价值。

---

## 2. 整体架构（把这张图记住）

```
【离线：建索引】只做一次，文档更新时重做
  文档(PDF/MD/TXT) → 读取 → 切块(chunk) → 算 embedding → 存向量库

【在线：问答】每次提问都跑
  用户问题 → 算 embedding → 向量库检索 top-k → 拿到相关片段
                                                    ↓
                            组装提示词（资料 + 问题 + 约束）→ 大模型 → 答案 + 出处
```

**两阶段、两条流水线。** 90% 的 RAG 问题都出在"切块"和"检索"这两步，不是模型不够强。

---

## 3. 完整项目代码

### 3.1 目录结构

```
rag_app/
├── .env
├── requirements.txt
├── rag.py                # 主程序
├── embedder.py           # embedding 封装（云端 / 本地可切换）→ 可直接用 ../code/embedder.py
├── vector_store.py       # 向量库 → 可直接用 ../code/vector_store.py
├── chunker.py            # 切块 → 可直接用 ../code/chunker.py
└── docs/                 # 你的文档放这里
    ├── 员工手册.md
    ├── 报销制度.md
    └── 产品说明.txt
```

> 💡 **省事做法**：本教程已经写好了下面三个模块，先复制过来，你只需要专注写 `rag.py`：
> ```powershell
> Copy-Item ..\code\vector_store.py, ..\code\chunker.py, ..\code\embedder.py .
> ```
> 复制 `chunker.py` 后，把第 3.3 节的自写版本删掉即可（接口一致：`chunk_text(...) -> list[Chunk]`）。

### 3.2 `embedder.py` —— 让 embedding 后端可切换

```python
# embedder.py
import os
from dotenv import load_dotenv

load_dotenv()


class Embedder:
    """统一接口，屏蔽云端/本地差异。"""

    def __init__(self, backend: str | None = None):
        self.backend = backend or os.getenv("EMBED_BACKEND", "local")
        if self.backend == "local":
            from sentence_transformers import SentenceTransformer
            name = os.getenv("EMBED_MODEL", "BAAI/bge-small-zh-v1.5")
            self.model = SentenceTransformer(name)
        else:
            from openai import OpenAI
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"),
                                 base_url=os.getenv("OPENAI_BASE_URL"))
            self.name = os.getenv("EMBED_MODEL", "text-embedding-3-small")

    def encode(self, texts: list[str]) -> list[list[float]]:
        """文本列表 → 归一化向量列表。"""
        if not texts:
            return []
        if self.backend == "local":
            vecs = self.model.encode(texts, normalize_embeddings=True,
                                     show_progress_bar=len(texts) > 50)
            return vecs.tolist()
        resp = self.client.embeddings.create(model=self.name, input=texts)
        return [d.embedding for d in resp.data]

    def encode_one(self, text: str) -> list[float]:
        return self.encode([text])[0]
```

### 3.3 文本切块（RAG 里最关键的一步）

```python
# chunker.py
import re
from dataclasses import dataclass


@dataclass
class Chunk:
    text: str
    source: str
    index: int


def chunk_text(text: str, size: int = 400, overlap: int = 80,
               source: str = "") -> list[Chunk]:
    """
    把长文本切成带重叠的小块。

    size    : 每块目标字符数
    overlap : 相邻块的重叠字符数（保证跨块的句子不被割裂）

    切块策略：优先在段落/句号/换行处断开，实在不行才硬切。
    """
    text = re.sub(r"\n{3,}", "\n\n", text.strip())
    chunks: list[Chunk] = []
    start = 0
    idx = 0

    while start < len(text):
        end = min(start + size, len(text))

        if end < len(text):
            # 在窗口后半段找一个"自然断点"
            window = text[start:end]
            best = -1
            for pat in ["\n\n", "\n", "。", "！", "？", ". ", "；", ";"]:
                pos = window.rfind(pat)
                if pos > size * 0.5:            # 断点不能太靠前，否则块太小
                    best = max(best, pos + len(pat))
            if best > 0:
                end = start + best

        piece = text[start:end].strip()
        if piece:
            chunks.append(Chunk(text=piece, source=source, index=idx))
            idx += 1

        if end >= len(text):
            break
        start = max(end - overlap, start + 1)   # 回退 overlap 个字符形成重叠

    return chunks


if __name__ == "__main__":
    demo = "第一句话。第二句话。第三句话。" * 50
    cs = chunk_text(demo, size=100, overlap=20, source="demo")
    print(f"切成 {len(cs)} 块")
    for c in cs[:3]:
        print(f"[{c.index}] len={len(c.text)}  {c.text[:40]}...")
```

> **切块的经验值**：
> - `size`：中文 300–800 字符（英文 200–500 token）
> - `overlap`：`size` 的 10%–20%
> - **太小的块**：语义不完整，检索到也不知道在说什么
> - **太大的块**：包含无关信息，稀释相关性，还费 token
> - **更好的做法**：按文档结构切（Markdown 按标题层级切，代码按函数切）

### 3.4 主程序 `rag.py`

```python
# rag.py
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from embedder import Embedder
from vector_store import VectorStore
from chunker import chunk_text

load_dotenv()

DOCS_DIR = Path("docs")
INDEX_PATH = Path("index.json")
LLM_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TOP_K = 4

SYSTEM_PROMPT = """你是一个严谨的文档问答助手。规则：

1. 只依据【参考资料】回答，不要使用你自己的知识补充。
2. 如果资料中没有答案，直接回答"根据现有资料无法回答这个问题"，不要猜测。
3. 回答要简洁，能引用原文就引用。
4. 在回答末尾用 [来源: 文件名] 的形式列出你实际用到的资料。"""


# ---------------- 索引构建 ----------------
def read_file(path: Path) -> str:
    """读取文档。txt/md 直接读，pdf 需要额外库。"""
    if path.suffix.lower() in (".txt", ".md", ".markdown"):
        return path.read_bytes().decode("utf-8", errors="ignore")
    if path.suffix.lower() == ".pdf":
        try:
            import io
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(path.read_bytes()))
            return "\n".join(p.extract_text() or "" for p in reader.pages)
        except ImportError:
            print(f"跳过 {path.name}：读 PDF 需要 pip install pypdf")
            return ""
    print(f"跳过不支持的文件：{path.name}")
    return ""


def build_index(embedder: Embedder) -> VectorStore:
    """离线阶段：读文档 → 切块 → 算向量 → 存库。"""
    files = [p for p in DOCS_DIR.rglob("*")
             if p.is_file() and p.suffix.lower() in (".txt", ".md", ".markdown", ".pdf")]
    if not files:
        print(f"❌ {DOCS_DIR.resolve()} 里没有文档，请先放几个 .md 或 .txt 文件进去。")
        sys.exit(1)

    all_chunks = []
    for f in files:
        text = read_file(f)
        if not text.strip():
            continue
        chunks = chunk_text(text, size=400, overlap=80, source=f.name)
        all_chunks.extend(chunks)
        print(f"  📄 {f.name}: {len(text)} 字 → {len(chunks)} 块")

    print(f"\n共 {len(all_chunks)} 块，正在计算向量...")
    vectors = embedder.encode([c.text for c in all_chunks])

    store = VectorStore()
    store.add_many(
        texts=[c.text for c in all_chunks],
        vectors=vectors,
        metadatas=[{"source": c.source, "index": c.index} for c in all_chunks],
    )
    store.save(INDEX_PATH)
    print(f"✅ 索引已保存到 {INDEX_PATH}（{len(store)} 块，{store.dim} 维）\n")
    return store


# ---------------- 问答 ----------------
class RAG:
    def __init__(self, store: VectorStore, embedder: Embedder,
                 top_k: int = TOP_K, model: str = LLM_MODEL):
        self.store = store
        self.embedder = embedder
        self.top_k = top_k
        self.model = model
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"),
                             base_url=os.getenv("OPENAI_BASE_URL"))
        self.history: list[dict] = []

    def retrieve(self, question: str) -> list[dict]:
        qv = self.embedder.encode_one(question)
        return self.store.search(qv, top_k=self.top_k)

    def build_context(self, hits: list[dict]) -> str:
        parts = []
        for i, h in enumerate(hits, 1):
            src = h["metadata"].get("source", "未知")
            parts.append(f"[资料{i}] 来源：{src}\n{h['text']}")
        return "\n\n---\n\n".join(parts)

    def ask(self, question: str, stream: bool = True, show_sources: bool = True) -> str:
        hits = self.retrieve(question)

        if show_sources:
            print("\n\033[90m检索到的片段：")
            for i, h in enumerate(hits, 1):
                print(f"  {i}. [{h['score']:.3f}] {h['metadata'].get('source')} "
                      f"| {h['text'][:45].replace(chr(10), ' ')}...")
            print("\033[0m")

        context = self.build_context(hits)
        user_msg = f"""【参考资料】
{context}

【问题】
{question}

请依据上述资料回答。"""

        self.history.append({"role": "user", "content": user_msg})
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + self.history[-6:]

        print("\033[36mAI:\033[0m ", end="", flush=True)
        pieces: list[str] = []
        try:
            if stream:
                resp = self.client.chat.completions.create(
                    model=self.model, messages=messages,
                    temperature=0.2, max_tokens=800, stream=True,
                )
                for chunk in resp:
                    if chunk.choices and chunk.choices[0].delta.content:
                        piece = chunk.choices[0].delta.content
                        pieces.append(piece)
                        print(piece, end="", flush=True)
            else:
                resp = self.client.chat.completions.create(
                    model=self.model, messages=messages,
                    temperature=0.2, max_tokens=800,
                )
                answer = resp.choices[0].message.content
                pieces.append(answer)
                print(answer, end="")
        except Exception as e:
            print(f"\n\033[31m[出错] {e}\033[0m")
            self.history.pop()
            return ""

        answer = "".join(pieces)
        self.history.append({"role": "assistant", "content": answer})
        print("\n")
        return answer


# ---------------- 入口 ----------------
def main() -> None:
    embedder = Embedder()

    if INDEX_PATH.exists() and "--rebuild" not in sys.argv:
        store = VectorStore.load(INDEX_PATH)
        print(f"📚 载入已有索引：{len(store)} 块（加 --rebuild 可重建）\n")
    else:
        print("📖 构建索引中...")
        store = build_index(embedder)

    rag = RAG(store, embedder)

    print("=" * 56)
    print("  文档问答助手（RAG）")
    print("  输入问题；/rebuild 重建索引；/quit 退出")
    print("=" * 56 + "\n")

    while True:
        try:
            q = input("\033[32m你:\033[0m ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break
        if not q:
            continue
        if q in ("/quit", "/exit", "/q"):
            break
        if q == "/rebuild":
            store = build_index(embedder)
            rag = RAG(store, embedder)
            continue
        rag.ask(q)


if __name__ == "__main__":
    main()
```

### 3.5 准备文档并运行

```powershell
mkdir docs
# 放几个 .md 或 .txt 进去，比如把你的笔记、产品文档、会议记录拷进去
uv add pypdf          # 想读 PDF 才需要

python rag.py                 # 首次会建索引（会下载 embedding 模型）
python rag.py --rebuild       # 文档改了之后重建
```

### 3.6 换 PDF 支持、加行号引用（可选增强）

```python
# 在 build_context 里带上更精确的定位信息
def build_context(self, hits):
    parts = []
    for i, h in enumerate(hits, 1):
        md = h["metadata"]
        parts.append(f"[资料{i}] 文件：{md.get('source')} 第 {md.get('index', '?')} 块\n{h['text']}")
    return "\n\n---\n\n".join(parts)
```

---

## 4. RAG 效果不好怎么办？按这个顺序排查

**不要一上来就换模型。绝大多数问题在检索环节。**

| 症状 | 大概率原因 | 解决 |
|---|---|---|
| 检索到的片段完全不相关 | embedding 模型不适合中文 / 切块太大 | 换 `bge-m3` 等中文模型；减小 `size` |
| 检索到了但答案不完整 | 切块把一句话切断 | 增大 `overlap`，改按段落/标题切 |
| 答案对但答案里没有的信息也编了 | 提示词约束不够 | 强化 system："资料中没有就说不知道" |
| 明明文档里有，就是搜不到 | 用户用词和文档用词差异大 | 加**查询改写**（见下） |
| 相似度分数都在 0.3 左右，区分不开 | 块太大或者文档同质化 | 切更小；加元数据过滤；用 rerank |
| 多跳问题答不出 | 需要多步推理 | 用 Agent（第 10 天）或查询分解 |

### 三个最有效的优化手段

**① 查询改写（Query Rewriting）**：把口语化问题改成检索友好的表达。

```python
REWRITE_PROMPT = """把用户的问题改写成 3 个适合检索的短查询，每行一个，不要编号。
要求：保留关键实体，去掉口语化表达，可以补充同义词。

用户问题：{q}"""

def rewrite_query(self, question: str) -> list[str]:
    resp = self.client.chat.completions.create(
        model=self.model, temperature=0,
        messages=[{"role": "user", "content": REWRITE_PROMPT.format(q=question)}],
    )
    lines = [l.strip("- 　0123456789.").strip()
             for l in resp.choices[0].message.content.splitlines() if l.strip()]
    return lines[:3] or [question]

def retrieve_multi(self, question: str, k: int = TOP_K):
    """多查询检索 + 去重合并（最实用的提升手段）"""
    queries = [question] + self.rewrite_query(question)
    merged: dict[str, dict] = {}
    for q in queries:
        for h in self.store.search(self.embedder.encode_one(q), top_k=k):
            key = h["metadata"].get("source", "") + str(h["metadata"].get("index"))
            if key not in merged or h["score"] > merged[key]["score"]:
                merged[key] = h
    return sorted(merged.values(), key=lambda x: -x["score"])[:k]
```

**② 加 Rerank（重排）**：先粗排 20 条，再用更强的模型精排取 3 条。

```python
RERANK_PROMPT = """给下面每个片段与问题的相关性打分，0-10 的整数，只输出 JSON 数组。
问题：{q}
片段：
{chunks}
输出格式：[{{"i": 0, "score": 8}}, ...]"""
```

**③ 混合检索（关键词 + 向量）**：专有名词、型号、代码、人名，关键词比向量更准。

```python
def hybrid_score(vector_score: float, keyword_score: float,
                 alpha: float = 0.7) -> float:
    return alpha * vector_score + (1 - alpha) * keyword_score
```

> **实战经验**：查询改写 + 混合检索，通常能把命中率从 60% 提到 85% 以上，成本几乎为零。

---

## 5. RAG 的进阶形态（知道就行，先别急着做）

| 技术 | 一句话说明 | 什么时候用 |
|---|---|---|
| **Parent-Child 检索** | 用小块检索，返回它所属的大块 | 块小检索准但上下文不够 |
| **Sentence-Window** | 返回命中句子的前后 N 句 | 需要上下文连贯 |
| **GraphRAG** | 把实体关系建成图，支持多跳推理 | "A 的上级的部门负责什么" |
| **Agentic RAG** | 让模型自己决定查几次、查什么 | 复杂多步问题 |
| **Self-RAG** | 模型自己评估检索质量，不够就再查 | 高质量要求场景 |
| **上下文压缩** | 用模型把检索片段压缩后再喂 | 省 token |

---

## 6. 今日作业

1. **跑通整个 RAG 系统**，放至少 3 个文档，问 5 个问题，观察检索片段和答案。
2. **做一次失败的实验**：把 `size` 改成 2000（块超大），重新建索引，观察答案质量下降。记下你的发现。
3. 加一个 `/sources` 命令：列出当前索引里所有文档名 + 各自的块数。
4. 实现第 4 节的 `rewrite_query`，比较开启前后同一个问题的检索结果差异。
5. **加"没找到就说不知道"的测试**：问一个文档里绝对没有的问题，确认模型没有编造（这是 RAG 最重要的安全属性）。
6. 挑战：把 `rag.py` 改成 Web 界面（第 10 天有 Gradio 教程），截图发给你自己看。

---

## 7. 一分钟自测

- [ ] RAG 的两个阶段分别是什么？（离线建索引 / 在线检索+生成）
- [ ] 为什么需要 `overlap`？不重叠会怎样？（关键句被切断，两边都搜不全）
- [ ] 提示词里为什么要强调"只依据资料回答"？（防止模型用自己知识瞎编）
- [ ] 检索不准，先优化模型还是先优化切块？（先优化切块和检索）
- [ ] 专有名词（型号、代码）搜不到，用什么办法？（混合检索 / 关键词兜底）
- [ ] 切块太大和太小分别有什么问题？

---

上一课 → [`07_向量检索入门.md`](07_向量检索入门.md) ｜ 下一课 → [`09_Agent工具调用入门.md`](09_Agent工具调用入门.md)
