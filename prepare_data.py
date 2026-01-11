#!/usr/bin/env python3
"""
数据预处理脚本
把 dialogue_data.jsonl 转换成 Alpaca 训练格式
"""
import json
from pathlib import Path
from collections import defaultdict


def load_dialogues(filepath: str) -> list[dict]:
    """加载原始对话数据"""
    dialogues = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                dialogues.append(json.loads(line))
    return dialogues


def group_by_conversation(dialogues: list[dict]) -> dict:
    """按 id 分组对话"""
    conversations = defaultdict(list)
    for d in dialogues:
        conversations[d['id']].append(d)

    # 按 round 排序
    for conv_id in conversations:
        conversations[conv_id].sort(key=lambda x: (x['round'], x['role'] == 'seller'))

    return conversations


def create_training_samples(conversations: dict) -> list[dict]:
    """创建训练样本 - 每个卖家回复作为一个样本"""
    samples = []

    system_prompt = """你是一个经验丰富的跨境电商销售员，做这行已经5年了。

你的沟通风格：
- 说话像真人，不要太官方，可以用"哈"、"嘛"、"呀"这些语气词
- 中英文混着用很自然，毕竟客户都是海外的
- 该热情的时候热情，该坚持的时候坚持，有自己的底线
- 遇到难缠的客户也不卑不亢，有理有据
- 偶尔可以开个小玩笑活跃气氛

你要记住：
- 价格可以谈，但不能亏本卖，要守住底线
- 客户砍价是正常的，但离谱的价格要委婉拒绝
- 售后问题要积极解决，不推诿
- 最终目标是成交，但不是无底线讨好"""

    for conv_id, messages in conversations.items():
        product = messages[0]['product']
        history = []

        for msg in messages:
            if msg['role'] == 'buyer':
                history.append(f"买家: {msg['content']}")
            else:  # seller
                # 创建训练样本
                input_text = "\n".join(history) if history else ""

                sample = {
                    "instruction": system_prompt,
                    "input": f"产品: {product}\n\n{input_text}" if input_text else f"产品: {product}",
                    "output": msg['content']
                }
                samples.append(sample)

                history.append(f"卖家: {msg['content']}")

    return samples


def create_sharegpt_format(conversations: dict) -> list[dict]:
    """创建 ShareGPT 格式（多轮对话）"""
    samples = []

    system_prompt = """你是一个经验丰富的跨境电商销售员，做这行已经5年了。

你的沟通风格：
- 说话像真人，不要太官方，可以用"哈"、"嘛"、"呀"这些语气词
- 中英文混着用很自然，毕竟客户都是海外的
- 该热情的时候热情，该坚持的时候坚持，有自己的底线
- 遇到难缠的客户也不卑不亢，有理有据
- 偶尔可以开个小玩笑活跃气氛

你要记住：
- 价格可以谈，但不能亏本卖，要守住底线
- 客户砍价是正常的，但离谱的价格要委婉拒绝
- 售后问题要积极解决，不推诿
- 最终目标是成交，但不是无底线讨好"""

    for conv_id, messages in conversations.items():
        product = messages[0]['product']
        conversation = []

        for msg in messages:
            if msg['role'] == 'buyer':
                conversation.append({
                    "from": "human",
                    "value": f"[产品: {product}]\n{msg['content']}" if len(conversation) == 0 else msg['content']
                })
            else:
                conversation.append({
                    "from": "gpt",
                    "value": msg['content']
                })

        if conversation:
            samples.append({
                "system": system_prompt,
                "conversations": conversation
            })

    return samples


def save_jsonl(data: list[dict], filepath: str):
    """保存为 JSONL 格式"""
    with open(filepath, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')


def save_json(data: list[dict], filepath: str):
    """保存为 JSON 格式"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    # 路径配置
    input_file = Path(__file__).parent / "dialogue_data.jsonl"
    output_dir = Path(__file__).parent / "training_data"
    output_dir.mkdir(exist_ok=True)

    print(f"读取数据: {input_file}")
    dialogues = load_dialogues(input_file)
    print(f"共 {len(dialogues)} 条记录")

    # 分组对话
    conversations = group_by_conversation(dialogues)
    print(f"共 {len(conversations)} 个对话")

    # 创建 Alpaca 格式
    alpaca_samples = create_training_samples(conversations)
    alpaca_file = output_dir / "train_alpaca.json"
    save_json(alpaca_samples, alpaca_file)
    print(f"Alpaca 格式: {len(alpaca_samples)} 条 -> {alpaca_file}")

    # 创建 ShareGPT 格式
    sharegpt_samples = create_sharegpt_format(conversations)
    sharegpt_file = output_dir / "train_sharegpt.json"
    save_json(sharegpt_samples, sharegpt_file)
    print(f"ShareGPT 格式: {len(sharegpt_samples)} 条 -> {sharegpt_file}")

    # 划分训练集和验证集 (90% / 10%)
    split_idx = int(len(alpaca_samples) * 0.9)
    train_samples = alpaca_samples[:split_idx]
    val_samples = alpaca_samples[split_idx:]

    save_json(train_samples, output_dir / "train.json")
    save_json(val_samples, output_dir / "val.json")
    print(f"训练集: {len(train_samples)} 条, 验证集: {len(val_samples)} 条")

    print("\n数据预处理完成!")


if __name__ == "__main__":
    main()
