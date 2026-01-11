"""
RAG 检索引擎：检索相似对话并组装 Prompt
"""
from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb


class RAGEngine:
    """RAG 检索引擎"""

    SYSTEM_PROMPT = """参考这些真实对话案例来回答问题：

{context}

---

根据以上案例，回答客服的问题。"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = str(Path(__file__).parent / "chroma_db")

        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_collection("dialogues")
        self.model = SentenceTransformer('BAAI/bge-m3')

    def search(self, query: str, k: int = 5) -> list[dict]:
        """
        检索相似对话

        Args:
            query: 用户查询
            k: 返回结果数量

        Returns:
            相似对话列表，每个包含 document, metadata, distance
        """
        query_embedding = self.model.encode([query])

        results = self.collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=k
        )

        similar_dialogues = []
        for i in range(len(results['documents'][0])):
            similar_dialogues.append({
                "document": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "distance": results['distances'][0][i] if results.get('distances') else None
            })

        return similar_dialogues

    def build_prompt(self, query: str, k: int = 5) -> str:
        """
        构建完整的 Prompt

        Args:
            query: 客服遇到的问题
            k: 检索案例数量

        Returns:
            完整的 prompt
        """
        # 检索相似案例
        similar = self.search(query, k)

        # 格式化案例
        context_parts = []
        for i, item in enumerate(similar, 1):
            meta = item['metadata']
            context_parts.append(
                f"案例 {i}:\n"
                f"  产品: {meta['product']}\n"
                f"  角色: {meta['role']}\n"
                f"  轮次: {meta['round']}\n"
                f"  内容: {item['document'].split('内容:')[-1]}"
            )

        context = "\n\n".join(context_parts)

        # 组装 prompt
        system_prompt = self.SYSTEM_PROMPT.format(context=context)

        return system_prompt, query, similar


def main():
    """测试 RAG 引擎"""
    print("⏳ 初始化 RAG 引擎...")
    engine = RAGEngine()
    print("✅ 初始化完成")

    test_queries = [
        "客户说竞争对手只要一半价格，怎么回复？",
        "客户坚持要 50% 折扣，否则取消订单",
        "客户投诉发货太慢要求退款",
    ]

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"🔍 查询: {query}")
        print("="*60)

        system_prompt, user_query, similar = engine.build_prompt(query, k=3)

        print("\n📋 检索到的相似案例:")
        for i, item in enumerate(similar, 1):
            meta = item['metadata']
            print(f"\n{i}. [{meta['product']}] {meta['role']} (轮次 {meta['round']})")
            content = item['document'].split('内容:')[-1][:100]
            print(f"   {content}...")


if __name__ == "__main__":
    main()
