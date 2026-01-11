"""
Flask API 服务
"""
from flask import Flask, request, jsonify, Response, send_from_directory
from pathlib import Path
import json

from rag_engine import RAGEngine
from llm_client import QwenClient

app = Flask(__name__)

# 全局实例（延迟初始化）
rag_engine = None
llm_client = None


def get_rag_engine():
    global rag_engine
    if rag_engine is None:
        rag_engine = RAGEngine()
    return rag_engine


def get_llm_client():
    global llm_client
    if llm_client is None:
        llm_client = QwenClient()
    return llm_client


@app.route('/')
def index():
    """返回前端页面"""
    return send_from_directory('.', 'index.html')


@app.route('/chat', methods=['POST'])
def chat():
    """
    聊天接口

    请求体:
        {"message": "客户说价格太贵了怎么办"}

    返回:
        {"reply": "...", "similar_cases": [...]}
    """
    data = request.json
    message = data.get('message', '')

    if not message:
        return jsonify({"error": "消息不能为空"}), 400

    try:
        # 1. RAG 检索
        engine = get_rag_engine()
        system_prompt, user_query, similar = engine.build_prompt(message, k=5)

        # 2. LLM 生成
        client = get_llm_client()
        reply = client.generate(system_prompt, user_query)

        # 3. 格式化相似案例（带分析）
        similar_cases = []
        for item in similar[:3]:  # 只返回前3个
            meta = item['metadata']
            content = item['document'].split('内容:')[-1][:200]
            role = meta['role']
            analysis = analyze_case(role, content)
            similar_cases.append({
                "product": meta['product'],
                "role": role,
                "content": content,
                "analysis": analysis
            })

        return jsonify({
            "reply": reply,
            "similar_cases": similar_cases
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def analyze_case(role, content):
    """根据角色和内容生成简短分析"""
    content_lower = content.lower()

    if role == 'buyer' or role == '买家':
        # 分析买家意图
        if 'discount' in content_lower or '折扣' in content or '优惠' in content or '便宜' in content:
            return "买家策略: 价格谈判，试探底价空间"
        elif 'quality' in content_lower or '质量' in content or '品质' in content:
            return "买家关注: 产品质量，需要建立信任"
        elif 'competitor' in content_lower or '竞争' in content or '别家' in content or '其他' in content:
            return "买家策略: 用竞品压价，需强调差异化"
        elif 'long-term' in content_lower or '长期' in content or '合作' in content:
            return "买家意图: 以长期合作换取优惠"
        elif 'urgent' in content_lower or '急' in content or '马上' in content:
            return "买家状态: 有紧迫需求，成交意向高"
        else:
            return "买家诉求: 了解产品/价格信息"
    else:
        # 分析卖家策略
        if 'best offer' in content_lower or '最低' in content or '底价' in content:
            return "卖家策略: 表明底线，促成成交"
        elif 'discount' in content_lower or '折扣' in content or '%' in content:
            return "卖家策略: 适度让步，给出优惠方案"
        elif 'quality' in content_lower or '质量' in content or '品质' in content:
            return "卖家策略: 强调价值，转移价格焦点"
        elif 'long-term' in content_lower or '长期' in content:
            return "卖家策略: 用长期合作换取当前让步"
        elif 'confirm' in content_lower or '确认' in content or '下单' in content:
            return "卖家策略: 推动成交，锁定订单"
        else:
            return "卖家策略: 维护关系，保持沟通"


@app.route('/chat/stream', methods=['POST'])
def chat_stream():
    """
    流式聊天接口

    请求体:
        {"message": "客户说价格太贵了怎么办"}

    返回:
        Server-Sent Events 流
    """
    data = request.json
    message = data.get('message', '')

    if not message:
        return jsonify({"error": "消息不能为空"}), 400

    def generate():
        try:
            # 1. RAG 检索
            engine = get_rag_engine()
            system_prompt, user_query, similar = engine.build_prompt(message, k=5)

            # 2. 先发送相似案例（带分析）
            similar_cases = []
            for item in similar[:3]:
                meta = item['metadata']
                content = item['document'].split('内容:')[-1][:200]
                role = meta['role']
                analysis = analyze_case(role, content)

                similar_cases.append({
                    "product": meta['product'],
                    "role": role,
                    "content": content,
                    "analysis": analysis
                })

            yield f"data: {json.dumps({'type': 'cases', 'data': similar_cases})}\n\n"

            # 3. 流式生成回复
            client = get_llm_client()
            for chunk in client.generate_stream(system_prompt, user_query):
                yield f"data: {json.dumps({'type': 'chunk', 'data': chunk})}\n\n"

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"

    return Response(generate(), mimetype='text/event-stream')


@app.route('/search', methods=['POST'])
def search():
    """
    仅检索接口（不调用 LLM）

    请求体:
        {"query": "价格", "k": 5}

    返回:
        {"results": [...]}
    """
    data = request.json
    query = data.get('query', '')
    k = data.get('k', 5)

    if not query:
        return jsonify({"error": "查询不能为空"}), 400

    try:
        engine = get_rag_engine()
        results = engine.search(query, k)

        formatted = []
        for item in results:
            meta = item['metadata']
            formatted.append({
                "product": meta['product'],
                "role": meta['role'],
                "round": meta['round'],
                "content": item['document'].split('内容:')[-1],
                "distance": item['distance']
            })

        return jsonify({"results": formatted})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("启动客服辅助系统...")
    print("访问 http://localhost:5001")
    app.run(host='0.0.0.0', port=5001, debug=True)
