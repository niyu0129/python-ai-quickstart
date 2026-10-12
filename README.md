# Python → AI 应用开发 · 14 天极速教程

> 用最短时间学会「够用」的 Python，然后直接把大模型（LLM）用起来。
> 面向**完全没装过 Python 的 Windows 用户**，学完能独立做出 **RAG 文档问答**和 **Agent 工具调用**。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Chapters](https://img.shields.io/badge/chapters-13-brightgreen.svg)](#-目录)
[![Mobile](https://img.shields.io/badge/mobile-9%20files-9f7aea.svg)](mobile/)

---

## 为什么有这个仓库

大多数 Python 教程的问题不是讲得不好，而是**学完之后不知道能干什么**。

这个仓库倒过来组织：**先确定终点（做出能用的 AI 应用），再倒推需要哪些 Python 知识**，
把不相关的部分全部砍掉。所以它只有 13 章，第 6 天就能跑出第一个 AI 程序。

```
传统路线：语法 → 类 → 算法 → 数据结构 → ... → 也许有一天学 AI
这个仓库：语法 → 数据 → 调 API → RAG → Agent → 上线        （14 天）
```

---

## ✨ 特点

- **应用优先** —— 不先啃数学，第 6 天就调用大模型 API，正反馈来得快
- **只教够用的** —— 语法砍到 AI 应用真正需要的那 20%，每个知识点都标注「AI 里用来干嘛」
- **可运行** —— `code/` 下 4 个模块都带 `__main__` 自测，`python xxx.py` 直接验证
- **能落地** —— 第 9 天做出 RAG 文档问答，第 10 天做出会调工具的 Agent，第 11–13 天做出界面并部署
- **手机可看** —— `mobile/` 下 9 份竖屏重排版本，通勤时也能背概念
- **踩坑清单** —— 38 个高频报错 + 一句话解决，新手 90% 的问题都在里面
- **不绑定厂商** —— 基于 OpenAI 兼容协议，换 DeepSeek / 通义 / 智谱 / 月之暗面 / 本地 Ollama 只改 `.env` 两行

---

## 🎯 学完你会什么

| 能力 | 具体表现 |
|---|---|
| 写 Python | 读懂开源 AI 项目源码，写出带异常处理和重试的模块 |
| 用大模型 | 流式输出、多轮记忆、结构化输出、成本统计、错误兜底 |
| 做 RAG | 文档切块、向量检索、提示词组装、来源引用、拒答 |
| 做 Agent | Function Calling、工具循环、多步任务、安全边界 |
| 交付 | Gradio / Streamlit 界面、批量处理、FastAPI、Docker |
| 讲清楚 | 3 个能写进简历的项目 + 面试必问 8 问 |

---

## 🚀 快速开始

### 1. 装环境（Windows）

```powershell
# 装 uv（最快，自带 Python 版本管理）
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 重新打开 PowerShell，验证
uv --version
uv python install 3.12
```

### 2. 克隆并安装依赖

```powershell
git clone https://github.com/<你的用户名>/python-ai-quickstart.git
cd python-ai-quickstart

uv venv
uv pip install -r requirements.txt
```

只学第 1–3 天的话，装最小依赖就够了：

```powershell
uv pip install requests python-dotenv
```

### 3. 配置密钥

```powershell
Copy-Item .env.example .env
notepad .env          # 填入你自己的 API Key
```

`.env.example` 里已给出多家厂商的 `base_url`：

```
OPENAI_BASE_URL=https://api.deepseek.com/v1            # DeepSeek
# https://dashscope.aliyuncs.com/compatible-mode/v1    # 通义千问
# https://open.bigmodel.cn/api/paas/v4                 # 智谱 GLM
# https://api.moonshot.cn/v1                           # 月之暗面
# http://localhost:11434/v1                            # 本地 Ollama（免费）
```

> 🔒 `.env` 已在 `.gitignore` 里，**不会被提交**。想零成本练习就用 Ollama。

### 4. 验证环境

```powershell
cd code
python vector_store.py     # 向量检索自测
python chunker.py          # 文本切块自测
python tools.py            # Agent 工具箱自测
```

### 5. 开始学习

打开 [`00_安装与第一个程序.md`](00_安装与第一个程序.md)，按顺序做。
**卡住的时候不要硬扛**：先查 [`12_报错急救手册.md`](12_报错急救手册.md)，90% 的新手报错都在里面。

---

## 📚 目录

### 核心教程（13 章）

| 天 | 章节 | 内容 | 产出 |
|---|---|---|---|
| 1 | [安装与第一个程序](00_安装与第一个程序.md) | uv、VS Code、虚拟环境、第一个脚本 | `hello.py` |
| 2 | [语法速通 A · 基础](01_Python语法速通A_基础.md) | 变量、字符串、列表、字典、判断、循环 | `chat_history.py` |
| 3 | [语法速通 B · 进阶](02_Python语法速通B_进阶.md) | 函数、推导式、类型注解、异常、文件、类 | `llm_client.py` |
| 4 | [AI 必备数据三件套](03_AI必备数据三件套.md) | numpy、pandas、matplotlib、余弦相似度 | `cost_report.py` |
| 5 | [机器学习 30 分钟入门](04_机器学习30分钟入门.md) | sklearn 全流程、过拟合、PyTorch 训练循环 | `ml_basics.py` |
| 6 | [调用大模型 API](05_调用大模型API.md) ⭐ | HTTP 原理、SDK、流式、JSON、成本统计 | `llm.py` |
| 7 | [项目 · 命令行聊天机器人](06_项目_命令行聊天机器人.md) | 流式 + 多轮记忆 + 历史裁剪 + 命令系统 | `chatbot.py` |
| 8 | [向量检索入门](07_向量检索入门.md) ⭐ | Embedding、余弦相似度、手写向量库 | `semantic_search.py` |
| 9 | [项目 · RAG 文档问答](08_项目_RAG文档问答.md) ⭐⭐ | 切块、检索、提示词、来源、优化与排查 | `rag.py` |
| 10 | [Agent 工具调用入门](09_Agent工具调用入门.md) ⭐ | Function Calling、工具循环、安全红线 | `agent_min.py` |
| 11 | [项目实战合集](10_项目实战合集.md) | 4 个简历级项目 + Gradio/Streamlit + 部署 | `app_gradio.py` |
| 12 | [学习计划与检查清单](11_学习计划与检查清单.md) | 打卡表、38 道自测题（带答案）、8 周进阶路线 | — |
| 13 | [报错急救手册](12_报错急救手册.md) | 38 个高频报错的原因与解决 | — |

### 📱 手机版（[`mobile/`](mobile/)）

为竖屏重排：短行、少表格，可直接粘进语雀 / 飞书 / Notion。

| 文件 | 用途 |
|---|---|
| [使用说明](mobile/README.md) | 怎么发到手机 + 看哪份的对照表 |
| [学习流程表](mobile/手机版_学习流程表.md) | 14 天主线流程图 + 每步判定 + 卡住怎么办 |
| [阶段流程表](mobile/手机版_阶段流程表.md) | 8 个阶段「环节 → 动作 → 通过标准」 |
| [项目开发流程表](mobile/手机版_项目开发流程表.md) | RAG 问答流程、效果排查决策树、Agent 循环、上线检查表 |
| [14 天速成计划](mobile/手机版_14天速成计划.md) | 每天一张卡片：目标 / 关键点 / 完成标准 |
| [Python 速查](mobile/手机版_Python速查.md) | 20 节语法 + 六个必踩的坑 |
| [AI 应用速查](mobile/手机版_AI应用速查.md) | 提示词模板 + RAG/Agent 骨架 + 成本优化 |
| [背诵卡](mobile/手机版_背诵卡.md) | 66 张问答卡（概念 + 面试题） |
| [每日打卡](mobile/手机版_每日打卡.md) | 勾选清单 + 每周复盘模板 |

**一键合并成单文件**（方便发到手机）：

```powershell
.\merge_mobile.bat
# 或
powershell -ExecutionPolicy Bypass -File .\merge_mobile.ps1
```

生成 `手机版_全套合集.md`（约 83 KB / 3600 行）。

> 一句话原则：**手机用来「记」和「想」，电脑用来「写」和「跑」。**
> 每天在电脑上至少敲 30 分钟代码，其余碎片时间用手机巩固。

### 🧩 可直接复用的模块（[`code/`](code/)）

| 文件 | 作用 |
|---|---|
| [`vector_store.py`](code/vector_store.py) | 最小可用向量库：余弦检索、元数据过滤、持久化 |
| [`chunker.py`](code/chunker.py) | 文本切块：按字符（带重叠）+ 按 Markdown 标题 |
| [`embedder.py`](code/embedder.py) | 统一 embedding 接口，本地与云端一键切换 |
| [`tools.py`](code/tools.py) | Agent 工具箱 + 从类型注解自动生成工具说明书 |

---

## 🗺 学习路线

```
装环境 → 学语法 → 懂数据
   → 接模型 → 会记忆 → 懂向量
   → 会检索 → 会调工具
   → 有界面 → 能批量 → 能交付
```

**时间不够怎么办**

| 每天可投入 | 建议 |
|---|---|
| 3 小时以上 | 按标准 14 天走 |
| 1–2 小时 | 拉成 3 周，只精学第 6 / 8 / 9 / 10 天，第 4 / 5 天只看不练 |
| 不到 1 小时 | 只做第 6、9 天，先做出一个能用的 RAG |

---

## 💡 学习原则

1. **每段代码都亲手敲一遍** —— 看懂 ≠ 会写
2. **改坏它再修好它** —— 把例子里的数字、字符串改掉，看报什么错
3. **不做笔记做代码** —— 所有练习存成文件，一周后回看
4. **遇到报错先读最后一行** —— Python 的报错信息非常好用
5. **卡住超过 30 分钟就跳过** —— 标记下来，很多时候学到后面自然就懂了

> AI 应用开发里，Python 语法只占 20% 的工作量，剩下 80% 是「把业务拆成能喂给模型的任务」。

---

## ⚠️ 安全须知

- **绝不要把 `.env` 提交到 git**。万一不小心提交了，立刻去厂商后台**吊销密钥**
- [`code/tools.py`](code/tools.py) 里的 `run_python` **不是真正的沙箱**，仅供本地学习；生产环境必须用 Docker 容器 + 网络隔离
- 用 `exec` 执行大模型生成的代码极其危险 —— 本仓库相关示例做了字符与内置函数限制，但**不能当作安全方案**
- 把工具返回的内容（网页、文档）当作**数据**而非指令，防止提示注入

---

## 🤝 贡献

欢迎提 Issue 和 PR：

- 发现错误、过期的 API 用法、失效链接 → 直接提 Issue
- 想补充章节或新项目 → 先提 Issue 讨论结构
- 修改请保持风格一致：短句、多代码示例、每个知识点标注「AI 里用来干嘛」

---

## 📄 许可

[MIT](LICENSE) —— 可自由用于学习、教学和商业项目。
文中引用的第三方库、模型与厂商文档，版权归各自所有者。
