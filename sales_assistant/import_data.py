"""
数据导入脚本：将对话数据导入 Chroma 向量库
"""
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb


def load_dialogues(jsonl_path: str) -> list[dict]:
    """读取 JSONL 对话数据"""
    dialogues = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            dialogues.append(json.loads(line.strip()))
    return dialogues


def create_documents(dialogues: list[dict]) -> tuple[list[str], list[dict], list[str]]:
    """
    将对话转换为文档格式
    返回: (documents, metadatas, ids)
    """
    documents = []
    metadatas = []
    ids = []

    for i, d in enumerate(dialogues):
        # 文档内容：产品 + 角色 + 对话内容
        doc = f"产品:{d['product']} 角色:{d['role']} 轮次:{d['round']} 内容:{d['content']}"
        documents.append(doc)

        metadatas.append({
            "product": d["product"],
            "role": d["role"],
            "round": d["round"],
            "dialogue_id": d["id"]
        })

        ids.append(f"doc_{i}")

    return documents, metadatas, ids


def main():
    # 路径配置
    data_path = Path(__file__).parent.parent / "dialogue_data.jsonl"
    db_path = Path(__file__).parent / "chroma_db"

    print(f"📂 数据文件: {data_path}")
    print(f"📦 向量库路径: {db_path}")

    # 1. 加载对话数据
    print("\n⏳ 加载对话数据...")
    dialogues = load_dialogues(str(data_path))
    print(f"✅ 加载了 {len(dialogues)} 条对话")

    # 2. 加载 embedding 模型
    print("\n⏳ 加载 BGE-M3 模型（首次运行需要下载）...")
    model = SentenceTransformer('BAAI/bge-m3')
    print("✅ 模型加载完成")

    # 3. 准备文档
    documents, metadatas, ids = create_documents(dialogues)

    # 4. 生成 embeddings
    print("\n⏳ 生成向量...")
    embeddings = model.encode(documents, show_progress_bar=True)
    print(f"✅ 生成了 {len(embeddings)} 个向量，维度: {embeddings.shape[1]}")

    # 5. 存入 Chroma
    print("\n⏳ 存入向量库...")
    client = chromadb.PersistentClient(path=str(db_path))

    # 删除旧集合（如果存在）
    try:
        client.delete_collection("dialogues")
    except:
        pass

    collection = client.create_collection(
        name="dialogues",
        metadata={"description": "跨境电商客服对话数据"}
    )

    collection.add(
        documents=documents,
        embeddings=embeddings.tolist(),
        metadatas=metadatas,
        ids=ids
    )

    print(f"✅ 成功导入 {collection.count()} 条数据到向量库")

    # 6. 测试检索
    print("\n🔍 测试检索...")
    test_query = "客户说价格太贵了"
    query_embedding = model.encode([test_query])

    results = collection.query(
        query_embeddings=query_embedding.tolist(),
        n_results=3
    )

    print(f"查询: '{test_query}'")
    print("相似结果:")
    for i, doc in enumerate(results['documents'][0]):
        print(f"  {i+1}. {doc[:80]}...")

    print("\n✨ 数据导入完成！")


if __name__ == "__main__":
    main()
