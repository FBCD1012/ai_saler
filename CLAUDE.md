# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个 AI 销售助手学习项目，专注于：
- 跨境电商对话数据生成
- 本地 RAG（检索增强生成）架构设计
- Claude Code Hooks 机制探索

## 常用命令

```bash
# 生成对话训练数据
python3 generate_dialogues.py

# 启动本地服务器查看 HTML 可视化
python3 -m http.server 8000

# 打开可视化文档
open sales_assistant_architecture.html
open lora_explain.html
open vector_db_explain.html
```

## 架构

### 数据生成流程
`generate_dialogues.py` → `dialogue_data.jsonl`
- 30 种电子产品库
- 3 轮对话模式：询价 → 砍价 → 成交
- 输出 JSONL 格式，包含 id、product、round、role、content 字段

### 本地 AI 部署架构
```
用户 → Flask API → BGE-M3 Embedding → Chroma 向量库
                 → Ollama + Qwen2.5 LLM → 响应
```
详见 `sales_assistant_architecture.html`

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
