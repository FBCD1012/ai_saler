"""
RAG 检索引擎
- 使用 BGE-small-zh 进行中文文本向量化
- 使用 Chroma 作为向量数据库
"""
import json
import chromadb
from sentence_transformers import SentenceTransformer
from pathlib import Path

class RAGEngine:
    def __init__(self, db_path: str = "./chroma_db"):
        # 加载中文 embedding 模型
        print("加载 BGE-small-zh 模型...")
        self.model = SentenceTransformer('BAAI/bge-small-zh-v1.5')

        # 初始化 Chroma
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(
            name="sales_dialogues",
            metadata={"hnsw:space": "cosine"}
        )
        print(f"向量库已加载，当前文档数: {self.collection.count()}")

    def import_dialogues(self, jsonl_path: str):
        """导入对话数据到向量库"""
        path = Path(jsonl_path)
        if not path.exists():
            print(f"文件不存在: {jsonl_path}")
            return

        # 读取所有对话
        dialogues = []
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    dialogues.append(json.loads(line))

        print(f"读取到 {len(dialogues)} 条对话记录")

        # 按对话ID分组，构建完整对话
        conversations = {}
        for d in dialogues:
            conv_id = d['id']
            if conv_id not in conversations:
                conversations[conv_id] = {
                    'product': d.get('product', ''),
                    'messages': []
                }
            conversations[conv_id]['messages'].append({
                'round': d.get('round', 0),
                'role': d.get('role', ''),
                'content': d.get('content', '')
            })

        print(f"共 {len(conversations)} 个独立对话")

        # 为每个对话创建向量
        documents = []
        metadatas = []
        ids = []

        for conv_id, conv in conversations.items():
            # 按轮次排序
            conv['messages'].sort(key=lambda x: (x['round'], 0 if x['role'] == 'buyer' else 1))

            # 构建完整对话文本
            text_parts = [f"产品: {conv['product']}"]
            for msg in conv['messages']:
                role_name = "客户" if msg['role'] == 'buyer' else "客服"
                text_parts.append(f"{role_name}: {msg['content']}")

            full_text = "\n".join(text_parts)

            documents.append(full_text)
            metadatas.append({
                'product': conv['product'],
                'conv_id': conv_id,
                'rounds': len(set(m['round'] for m in conv['messages']))
            })
            ids.append(f"conv_{conv_id}")

        # 批量添加到向量库
        print("正在向量化并存入数据库...")
        batch_size = 50
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i:i+batch_size]
            batch_metas = metadatas[i:i+batch_size]
            batch_ids = ids[i:i+batch_size]

            self.collection.add(
                documents=batch_docs,
                metadatas=batch_metas,
                ids=batch_ids
            )
            print(f"已处理 {min(i+batch_size, len(documents))}/{len(documents)}")

        print(f"导入完成! 当前向量库文档数: {self.collection.count()}")

    def search(self, query: str, n_results: int = 3) -> list:
        """检索相关对话"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )

        # 整理返回结果
        outputs = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                outputs.append({
                    'content': doc,
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'distance': results['distances'][0][i] if results['distances'] else 0
                })

        return outputs

    def clear(self):
        """清空向量库"""
        self.client.delete_collection("sales_dialogues")
        self.collection = self.client.get_or_create_collection(
            name="sales_dialogues",
            metadata={"hnsw:space": "cosine"}
        )
        print("向量库已清空")


# 测试
if __name__ == "__main__":
    rag = RAGEngine()

    # 导入对话数据
    data_path = "/Users/dongqing/standard_model_learning/dialogue_data.jsonl"
    rag.import_dialogues(data_path)

    # 测试检索
    print("\n--- 测试检索 ---")
    results = rag.search("客户说太贵了怎么办")
    for i, r in enumerate(results):
        print(f"\n结果 {i+1} (距离: {r['distance']:.3f}):")
        print(f"产品: {r['metadata'].get('product', 'N/A')}")
        print(r['content'][:200] + "...")
