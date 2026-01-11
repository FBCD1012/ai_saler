#!/usr/bin/env python3
"""
测试微调后的模型效果
"""
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from pathlib import Path


def load_model():
    """加载微调后的模型"""
    base_model_name = "Qwen/Qwen2.5-1.5B-Instruct"
    lora_path = Path(__file__).parent.parent / "output" / "lora_model" / "lora_weights"

    print("加载基座模型...")
    tokenizer = AutoTokenizer.from_pretrained(base_model_name, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        torch_dtype=torch.float16,
        trust_remote_code=True,
    )

    print("加载 LoRA 权重...")
    model = PeftModel.from_pretrained(model, str(lora_path))

    # 使用 MPS 如果可用
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model = model.to(device)
    model.eval()

    return model, tokenizer, device


def chat(model, tokenizer, device, user_input: str) -> str:
    """生成回复"""
    system_prompt = """你是一个经验丰富的跨境电商销售员，做这行已经5年了。

你的沟通风格：
- 说话像真人，不要太官方，可以用"哈"、"嘛"、"呀"这些语气词
- 中英文混着用很自然，毕竟客户都是海外的
- 该热情的时候热情，该坚持的时候坚持，有自己的底线
- 遇到难缠的客户也不卑不亢，有理有据
- 偶尔可以开个小玩笑活跃气氛"""

    prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{user_input}<|im_end|>\n<|im_start|>assistant\n"

    inputs = tokenizer(prompt, return_tensors="pt").to(device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=256,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
            pad_token_id=tokenizer.pad_token_id,
        )

    response = tokenizer.decode(outputs[0], skip_special_tokens=False)
    # 提取 assistant 的回复
    response = response.split("<|im_start|>assistant\n")[-1]
    response = response.split("<|im_end|>")[0]

    return response.strip()


def main():
    print("=" * 50)
    print("跨境电商销售助手 - 微调模型测试")
    print("=" * 50)

    model, tokenizer, device = load_model()
    print(f"\n模型加载完成! 设备: {device}")
    print("输入 'quit' 退出\n")

    # 测试用例
    test_cases = [
        "你好，我想批量采购TWS耳机，500pcs什么价格？",
        "买家: $8.50太贵了，能不能$6？不然我去别家买了",
        "我上周买的充电宝有30个是坏的，怎么处理？",
    ]

    print("--- 自动测试 ---\n")
    for i, test in enumerate(test_cases, 1):
        print(f"测试 {i}: {test}")
        response = chat(model, tokenizer, device, test)
        print(f"回复: {response}\n")
        print("-" * 40)

    print("\n--- 交互模式 ---")
    while True:
        user_input = input("\n你: ").strip()
        if user_input.lower() == 'quit':
            break
        if not user_input:
            continue

        response = chat(model, tokenizer, device, user_input)
        print(f"助手: {response}")


if __name__ == "__main__":
    main()
