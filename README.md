# AI 销售助手

基于本地 LLM + RAG 的跨境电商智能销售助手。

## 项目结构

```
├── model/                # 模型训练相关
│   ├── generate_dialogues.py   # 生成训练对话数据
│   ├── prepare_data.py         # 数据预处理
│   ├── train_lora.py           # LoRA 微调训练
│   ├── merge_and_export.py     # 模型合并导出
│   └── test_model.py           # 模型测试
├── sales_assistant/      # RAG 销售助手服务
│   ├── app.py                  # Flask API 服务
│   ├── rag_engine.py           # RAG 检索引擎
│   ├── llm_client.py           # LLM 客户端
│   └── knowledge/              # 知识库文档
├── docs/                 # 可视化文档
│   ├── sales_assistant_architecture.html
│   ├── lora_explain.html
│   └── vector_db_explain.html
└── styles/               # 公共样式
```

## 技术栈

- **LLM**: Qwen2.5 + LoRA 微调
- **Embedding**: BGE-M3
- **向量库**: ChromaDB
- **服务**: Flask + Ollama

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 生成训练数据
python model/generate_dialogues.py

# 3. 启动销售助手
cd sales_assistant
python app.py

# 4. 查看架构文档
open docs/sales_assistant_architecture.html
```

## 架构

```
用户请求 → Flask API → BGE-M3 Embedding → ChromaDB 检索
                     → Ollama + Qwen2.5 → 生成回复
```

## License

MIT
