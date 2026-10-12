"""
可复用的最小向量库 —— 配套第 8 天（08_项目... 实为 07_向量检索入门）和第 9 天（RAG）。

设计原则：零依赖（只用 numpy），完全可读，方便你理解向量检索的原理。
生产环境请换 Chroma / Qdrant / FAISS。

用法：
    from vector_store import VectorStore

    store = VectorStore()
    store.add_many(texts=["文档1", "文档2"],
                   vectors=[[0.1, 0.2], [0.3, 0.4]],
                   metadatas=[{"source": "a.md"}, {"source": "b.md"}])
    store.save("index.json")

    store = VectorStore.load("index.json")
    for hit in store.search([0.1, 0.2], top_k=2):
        print(hit["score"], hit["text"], hit["metadata"])
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np


@dataclass
class VectorStore:
    """向量 + 原文 + 元数据，支持本地文件持久化。"""

    dim: int = 0
    vectors: list[list[float]] = field(default_factory=list)
    texts: list[str] = field(default_factory=list)
    metadatas: list[dict] = field(default_factory=list)

    # ---------------- 写入 ----------------
    def add(self, text: str, vector: list[float], metadata: dict | None = None) -> None:
        if self.dim == 0:
            self.dim = len(vector)
        if len(vector) != self.dim:
            raise ValueError(
                f"向量维度不一致：库是 {self.dim} 维，新向量是 {len(vector)} 维。"
                "换 embedding 模型后必须重建整个索引。"
            )
        self.vectors.append(list(vector))
        self.texts.append(text)
        self.metadatas.append(metadata or {})

    def add_many(
        self,
        texts: list[str],
        vectors: list[list[float]],
        metadatas: list[dict] | None = None,
    ) -> None:
        if len(texts) != len(vectors):
            raise ValueError(f"texts 和 vectors 数量不一致：{len(texts)} vs {len(vectors)}")
        if metadatas is not None and len(metadatas) != len(texts):
            raise ValueError("metadatas 数量必须和 texts 一致")
        for i, (t, v) in enumerate(zip(texts, vectors)):
            self.add(t, v, metadatas[i] if metadatas else None)

    # ---------------- 检索 ----------------
    def search(
        self,
        query_vector: list[float],
        top_k: int = 3,
        where: dict | None = None,
        min_score: float | None = None,
    ) -> list[dict]:
        """
        返回最相似的 top_k 条。

        where    : 元数据过滤，如 {"source": "手册.md"}，只在这个子集里检索
        min_score: 相似度下限，低于此分数的结果直接丢弃（防止"矮子里拔将军"）
        """
        if not self.vectors:
            return []

        M = np.asarray(self.vectors, dtype=np.float32)      # (N, d)
        q = np.asarray(query_vector, dtype=np.float32)      # (d,)

        if q.shape[0] != M.shape[1]:
            raise ValueError(
                f"查询向量维度 {q.shape[0]} 与库维度 {M.shape[1]} 不匹配。"
                "请确认查询和建库用的是同一个 embedding 模型。"
            )

        # 元数据过滤：先筛出候选索引，再算相似度（省算力）
        if where:
            idx_pool = np.array(
                [i for i, md in enumerate(self.metadatas)
                 if all(md.get(k) == v for k, v in where.items())],
                dtype=np.int64,
            )
            if idx_pool.size == 0:
                return []
        else:
            idx_pool = np.arange(len(self.texts), dtype=np.int64)

        sub = M[idx_pool]

        # 余弦相似度 = 归一化后的点积（每次调用都归一化，调用方不必操心）
        sub = sub / (np.linalg.norm(sub, axis=1, keepdims=True) + 1e-10)
        qn = q / (np.linalg.norm(q) + 1e-10)
        scores = sub @ qn                                   # (len(idx_pool),)

        order = np.argsort(-scores)
        results: list[dict] = []
        for pos in order:
            score = float(scores[pos])
            if min_score is not None and score < min_score:
                break
            real_i = int(idx_pool[pos])
            results.append(
                {
                    "text": self.texts[real_i],
                    "score": score,
                    "metadata": self.metadatas[real_i],
                }
            )
            if len(results) >= top_k:
                break
        return results

    # ---------------- 持久化 ----------------
    def save(self, path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            json.dumps(
                {
                    "dim": self.dim,
                    "vectors": self.vectors,
                    "texts": self.texts,
                    "metadatas": self.metadatas,
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: str | Path) -> "VectorStore":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(
            dim=data.get("dim", 0),
            vectors=data.get("vectors", []),
            texts=data.get("texts", []),
            metadatas=data.get("metadatas", []),
        )

    # ---------------- 其他 ----------------
    def __len__(self) -> int:
        return len(self.texts)

    def sources(self) -> dict[str, int]:
        """统计每个来源文档有多少块。"""
        counts: dict[str, int] = {}
        for md in self.metadatas:
            key = str(md.get("source", "未知"))
            counts[key] = counts.get(key, 0) + 1
        return counts


if __name__ == "__main__":
    # 自测：造几个二维向量，验证检索是否正确
    store = VectorStore()
    store.add_many(
        texts=["我喜欢猫", "猫咪很可爱", "股票今天大跌"],
        vectors=[[0.9, 0.1], [0.85, 0.15], [0.0, 1.0]],
        metadatas=[{"source": "a.md"}, {"source": "a.md"}, {"source": "b.md"}],
    )
    print("库中条数：", len(store), "维度：", store.dim)

    hits = store.search([0.88, 0.12], top_k=2)
    for h in hits:
        print(f"  {h['score']:.4f}  {h['text']}  {h['metadata']}")

    print("只搜 a.md：", [h["text"] for h in store.search([0.9, 0.1], where={"source": "a.md"})])
    print("来源统计：", store.sources())

    store.save("_selftest_index.json")
    reloaded = VectorStore.load("_selftest_index.json")
    print("重新载入后条数：", len(reloaded))
    Path("_selftest_index.json").unlink(missing_ok=True)
