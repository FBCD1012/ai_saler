# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个 AI 销售助手学习项目，专注于：
- 跨境电商对话数据生成
- 本地 RAG（检索增强生成）架构设计
- Claude Code Hooks 机制探索

## 项目结构

```
ai_saler_backend/
├── model/                  # 模型训练相关
│   ├── generate_dialogues.py
│   ├── prepare_data.py
│   ├── train_lora.py
│   ├── test_model.py
│   ├── merge_and_export.py
│   └── Modelfile
├── data/                   # 数据文件
│   ├── dialogue_data.jsonl
│   └── training_data/
├── docs/                   # 可视化文档
├── sales_assistant/        # RAG 应用
└── output/                 # 训练输出（自动生成）
```

## 常用命令

```bash
# 生成对话训练数据
python3 model/generate_dialogues.py

# 数据预处理
python3 model/prepare_data.py

# 启动本地服务器查看 HTML 可视化
python3 -m http.server 8000

# 打开可视化文档
open docs/sales_assistant_architecture.html
open docs/lora_explain.html
open docs/vector_db_explain.html
```

## 架构

### 数据生成流程
`model/generate_dialogues.py` → `data/dialogue_data.jsonl`
- 30 种电子产品库
- 3 轮对话模式：询价 → 砍价 → 成交
- 输出 JSONL 格式，包含 id、product、round、role、content 字段

### 本地 AI 部署架构
```
用户 → Flask API → BGE-M3 Embedding → Chroma 向量库
                 → Ollama + Qwen2.5 LLM → 响应
```
详见 `docs/sales_assistant_architecture.html`

## Claude Code 配置

### Hook 系统 (.claude/scripts/)
- `user-prompt-hook.sh`: 用户输入预处理
  - `##` 前缀：草稿模式
  - `#` 前缀：快速记忆
  - `!context`：显示上下文

### 权限配置 (.claude/settings.local.json)
已授权：Playwright 浏览器自动化、WebSearch

## 开发偏好

- 中文回复
- 函数式编程风格
- 修改代码前先确认
