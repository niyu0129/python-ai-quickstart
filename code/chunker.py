"""
文本切块（chunking）—— RAG 里影响效果最大的一步。

切块的两个关键参数：
    size    : 每块目标字符数（中文建议 300-800）
    overlap : 相邻块重叠字符数（建议 size 的 10%-20%）

为什么需要 overlap：如果一句话正好被切在边界上，两块都不完整，
检索时两边都匹配不上。重叠 10%-20% 能显著缓解这个问题。

用法：
    from chunker import chunk_text
    chunks = chunk_text(long_text, size=400, overlap=80, source="手册.md")
    for c in chunks:
        print(c.index, len(c.text), c.text[:30])
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# 断点优先级：段落 > 换行 > 句末标点 > 分号 > 空格
BREAK_PATTERNS = ["\n\n", "\n", "。", "！", "？", "；", ". ", "! ", "? ", "; ", "，", ", "]


@dataclass
class Chunk:
    text: str
    source: str = ""
    index: int = 0


def chunk_text(
    text: str,
    size: int = 400,
    overlap: int = 80,
    source: str = "",
    min_size: int | None = None,
) -> list[Chunk]:
    """
    把长文本切成带重叠的小块，优先在自然语义边界断开。

    min_size: 最小块长度，太短的块会被合并到前一块（默认 size 的 30%）
    """
    if size <= 0:
        raise ValueError("size 必须大于 0")
    if overlap >= size:
        raise ValueError("overlap 必须小于 size，否则会死循环")
    min_size = min_size or max(int(size * 0.3), 1)

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        return []

    chunks: list[Chunk] = []
    start = 0
    idx = 0

    while start < len(text):
        end = min(start + size, len(text))

        if end < len(text):
            window = text[start:end]
            best = -1
            for pat in BREAK_PATTERNS:
                pos = window.rfind(pat)
                # 断点必须落在窗口后半段，否则块会太短
                if pos > size * 0.5:
                    best = max(best, pos + len(pat))
            if best > 0:
                end = start + best

        piece = text[start:end].strip()

        if piece and len(piece) < min_size and chunks:
            # 太短的尾块：合并进上一块，避免产生"信息不足的碎片"
            chunks[-1].text = (chunks[-1].text + " " + piece).strip()
        elif piece:
            chunks.append(Chunk(text=piece, source=source, index=idx))
            idx += 1

        if end >= len(text):
            break
        start = max(end - overlap, start + 1)

    return chunks


def chunk_by_heading(text: str, source: str = "", max_size: int = 900) -> list[Chunk]:
    """
    按 Markdown 标题切块（比纯字符切更符合文档结构，推荐用于技术文档）。

    先按 `#`/`##`/`###` 分割，超过 max_size 的小节再用 chunk_text 二次切分。
    """
    parts = re.split(r"\n(?=#{1,4}\s)", text)
    chunks: list[Chunk] = []
    idx = 0
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if len(part) <= max_size:
            chunks.append(Chunk(text=part, source=source, index=idx))
            idx += 1
        else:
            for sub in chunk_text(part, size=max_size, overlap=100, source=source):
                sub.index = idx
                chunks.append(sub)
                idx += 1
    return chunks


if __name__ == "__main__":
    demo = (
        "# 员工手册\n\n"
        "## 考勤制度\n"
        "上班时间为 9:00-18:00，中午休息一小时。迟到超过 30 分钟按半天事假处理。\n"
        "每月可申请 2 天远程办公，需提前一天在系统里提交申请并由直属主管审批。\n\n"
        "## 报销流程\n"
        "差旅费报销需在出差结束后 5 个工作日内提交，附发票原件和行程单。\n"
        "单笔超过 5000 元需要部门总监审批。报销款一般在审批通过后 7 个工作日到账。\n\n"
        "## 休假制度\n"
        "年假按工龄计算，入职满一年 5 天，满三年 10 天，满五年 15 天。\n"
        "年假需提前 3 个工作日申请，未经批准擅自休假按旷工处理。\n"
    ) * 3

    print("=== chunk_text（字符切块）===")
    cs = chunk_text(demo, size=200, overlap=40, source="员工手册.md")
    print(f"共 {len(cs)} 块")
    for c in cs[:4]:
        head = c.text[:35].replace("\n", " ")
        print(f"  [{c.index}] {len(c.text):3d} 字  {head}...")

    print("\n=== chunk_by_heading（按标题切块）===")
    hs = chunk_by_heading(demo, source="员工手册.md", max_size=300)
    print(f"共 {len(hs)} 块")
    for c in hs[:4]:
        head = c.text[:35].replace("\n", " ")
        print(f"  [{c.index}] {len(c.text):3d} 字  {head}...")
