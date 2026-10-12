"""
统一的 Embedding 接口 —— 屏蔽"本地模型"和"云端 API"的差异。

为什么需要它：本地模型和云端 API 的调用方式完全不同，
但上层代码（RAG、搜索、聚类）只关心"给我一段文本，返回一个向量"。
把差异封装在这一层，切换后端只改一个环境变量。

.env 配置：
    EMBED_BACKEND=local          # local 或 api
    EMBED_MODEL=BAAI/bge-small-zh-v1.5
    # 用 api 时还需要：
    OPENAI_API_KEY=sk-xxx
    OPENAI_BASE_URL=https://api.openai.com/v1

用法：
    from embedder import Embedder
    emb = Embedder()
    vecs = emb.encode(["第一段", "第二段"])
    v = emb.encode_one("查询文本")
"""

from __future__ import annotations

import os
from functools import lru_cache

import numpy as np
from dotenv import load_dotenv

load_dotenv()

# 中文场景的几个常见选择（本地免费）
LOCAL_MODEL_SUGGESTIONS = {
    "BAAI/bge-small-zh-v1.5": 512,     # 小、快，入门首选
    "BAAI/bge-base-zh-v1.5": 768,      # 平衡
    "BAAI/bge-large-zh-v1.5": 1024,    # 效果好、慢
    "BAAI/bge-m3": 1024,               # 多语言 + 长文本
}


class Embedder:
    """文本 → 归一化向量。encode 返回的向量已经归一化，点积即余弦相似度。"""

    def __init__(
        self,
        backend: str | None = None,
        model_name: str | None = None,
        batch_size: int = 32,
    ) -> None:
        self.backend = (backend or os.getenv("EMBED_BACKEND", "local")).lower()
        self.batch_size = batch_size

        if self.backend == "local":
            from sentence_transformers import SentenceTransformer  # 延迟导入，加快启动

            self.model_name = model_name or os.getenv(
                "EMBED_MODEL", "BAAI/bge-small-zh-v1.5"
            )
            self._model = SentenceTransformer(self.model_name)
            self.dim = self._model.get_sentence_embedding_dimension()
        elif self.backend == "api":
            from openai import OpenAI

            self.model_name = model_name or os.getenv(
                "EMBED_MODEL", "text-embedding-3-small"
            )
            self._client = OpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("OPENAI_BASE_URL"),
                timeout=60.0,
                max_retries=3,
            )
            self.dim = 0        # 第一次调用后才知道
        else:
            raise ValueError(f"不支持的 EMBED_BACKEND：{self.backend}（可选 local / api）")

    # ---------------- 核心接口 ----------------
    def encode(self, texts: list[str], is_query: bool = False) -> list[list[float]]:
        """
        批量编码。空列表返回空列表。

        is_query: 只对"查询"加检索指令前缀（bge 系列模型推荐做法，
                  能明显提升检索效果；文档侧不加前缀）。
        """
        if not texts:
            return []

        if self.backend == "local":
            inputs = list(texts)
            if is_query and "bge" in self.model_name.lower():
                instruction = "为这个句子生成表示以用于检索相关文章："
                inputs = [instruction + t for t in inputs]
            vecs = self._model.encode(
                inputs,
                normalize_embeddings=True,
                batch_size=self.batch_size,
                show_progress_bar=len(texts) > 64,
            )
            self.dim = vecs.shape[1]
            return np.asarray(vecs).tolist()

        # 云端 API：注意有的厂商对单次请求条数有限制，分批发
        out: list[list[float]] = []
        for i in range(0, len(texts), 64):
            batch = texts[i : i + 64]
            resp = self._client.embeddings.create(model=self.model_name, input=batch)
            vecs = [d.embedding for d in resp.data]
            out.extend(vecs)
        self.dim = len(out[0]) if out else 0
        return out

    def encode_one(self, text: str, is_query: bool = True) -> list[float]:
        return self.encode([text], is_query=is_query)[0]

    def similarity(self, a: str, b: str) -> float:
        """算两段文本的余弦相似度（方便做实验对比）。"""
        va, vb = self.encode([a, b])
        return float(np.dot(va, vb))


@lru_cache(maxsize=4)
def get_embedder(backend: str | None = None, model_name: str | None = None) -> Embedder:
    """带缓存的工厂函数：避免重复加载模型（加载一次要好几秒）。"""
    return Embedder(backend=backend, model_name=model_name)


if __name__ == "__main__":
    emb = get_embedder()
    print(f"后端：{emb.backend}  模型：{emb.model_name}  维度：{emb.dim}")

    pairs = [
        ("今天天气真好", "阳光明媚的一天"),
        ("今天天气真好", "股票今天大跌"),
        ("如何重置路由器密码", "忘记 Wi-Fi 密码了"),
    ]
    for a, b in pairs:
        print(f"  {emb.similarity(a, b):.3f}   「{a}」 vs 「{b}」")
