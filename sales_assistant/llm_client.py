"""
Ollama 本地 LLM 客户端 - 双模型架构
"""
import requests


class DualModelClient:
    """双模型客户端：qwen2.5 分析 + sales-assistant 话术"""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.analyst_model = "qwen2.5"  # 分析模型
        self.sales_model = "sales-assistant"  # 话术模型

    def _call_model(self, model: str, system_prompt: str, user_message: str) -> str:
        """调用指定模型"""
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "stream": False
            }
        )
        if response.status_code == 200:
            return response.json()["message"]["content"]
        else:
            raise Exception(f"Ollama 调用失败: {response.status_code}")

    def _check_price_keywords(self, message: str) -> bool:
        """检测是否涉及价格关键词"""
        price_keywords = ['价格', '多少钱', 'price', '报价', 'quote', '$/pc',
                          '贵', '便宜', 'expensive', 'cheap', 'discount', '折扣',
                          'MOQ', '批发', 'wholesale', '成本']
        return any(kw.lower() in message.lower() for kw in price_keywords)

    def _extract_price_from_context(self, system_prompt: str) -> str:
        """从 RAG 上下文中提取价格参考（带产品标记）"""
        import re
        # 匹配产品和价格
        product_prices = []
        # 查找 "产品: xxx" 和后面的价格（注意冒号后可能有空格）
        products = re.findall(r'产品:\s*([^\n]+)', system_prompt)
        prices = re.findall(r'\$[\d.]+(?:/pc)?', system_prompt)

        if products and prices:
            # 去重产品
            unique_products = list(dict.fromkeys(products))[:3]
            unique_prices = list(dict.fromkeys(prices))[:5]

            result = f"涉及产品: {', '.join(unique_products)}\n"
            result += f"参考价格: {', '.join(unique_prices)}"
            return result
        return ""

    def _extract_product_from_context(self, system_prompt: str) -> str:
        """从 RAG 上下文中提取主要产品类型"""
        import re
        products = re.findall(r'产品:\s*([^\n]+)', system_prompt)
        if products:
            # 清理产品名称并返回出现最多的
            products = [p.strip() for p in products]
            from collections import Counter
            most_common = Counter(products).most_common(1)
            if most_common:
                return most_common[0][0]
        return "通用产品"

    def generate(self, system_prompt: str, user_message: str) -> str:
        """
        双模型生成：
        1. qwen2.5 分析客户心理、策略和避坑提醒
        2. sales-assistant 生成人味话术
        3. 价格关键词触发时显示价格参考
        4. 显示相关产品标记
        """
        # Step 0: 提取相关产品类型
        product_type = self._extract_product_from_context(system_prompt)

        # Step 1: 用 qwen2.5 分析（包含避坑提醒）
        analysis_prompt = f"""你是跨境电商培训师，分析客户问题并给出策略建议。
当前咨询产品：{product_type}

请按以下格式回复（简洁）：

**客户心理**：一句话说明客户在想什么

**应对思路**：
- 要点1
- 要点2

**底线提醒**：不能让步的是什么

**避坑提醒**：
- 这种情况下新手容易犯什么错误
- 千万不要说什么话"""

        analysis = self._call_model(self.analyst_model, analysis_prompt, user_message)

        # Step 2: 用 sales-assistant 生成话术（带产品信息）
        sales_prompt = f"""你是经验丰富的跨境电商销售员，说话要有人味。
当前产品：{product_type}

客户说：{user_message}

请直接给出回复话术，要求：
- 用"哈"、"嘛"、"呀"等语气词
- 中英文混用自然
- 有底线但不生硬"""

        sales_reply = self._call_model(self.sales_model, sales_prompt, user_message)

        # Step 3: 检测价格关键词，提取价格参考
        price_info = ""
        if self._check_price_keywords(user_message):
            price_ref = self._extract_price_from_context(system_prompt)
            if price_ref:
                price_info = f"\n\n---\n\n## [价格参考]\n\n{price_ref}\n\n> 注：以上价格来自历史成交案例，实际价格请根据数量和当前市场情况调整"

        # 合并输出（无 emoji，带产品标记）
        result = f"""## [相关产品: {product_type}]

---

## [建议回复]

{sales_reply}

---

## [策略分析]

{analysis}{price_info}"""

        return result

    def generate_stream(self, system_prompt: str, user_message: str):
        """流式生成（简化版，先返回完整结果）"""
        result = self.generate(system_prompt, user_message)
        yield result


# 兼容旧代码的别名（直接使用双模型）
QwenClient = DualModelClient


def main():
    """测试双模型客户端"""
    print("⏳ 测试双模型连接...")

    try:
        client = DualModelClient()
        response = client.generate(
            system_prompt="",
            user_message="客户说太贵了"
        )
        print(f"✅ 连接成功")
        print(f"📝 回复:\n{response}")

    except requests.exceptions.ConnectionError:
        print("❌ 无法连接 Ollama，请确保已启动:")
        print("   ollama serve")
    except Exception as e:
        print(f"❌ 错误: {e}")


if __name__ == "__main__":
    main()
