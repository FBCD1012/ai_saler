#!/usr/bin/env python3
"""
合并 LoRA 权重并导出 GGUF 格式
用于部署到 Ollama
"""
import os
import subprocess
import shutil
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel


def merge_lora_weights(
    base_model_name: str,
    lora_path: str,
    output_path: str,
):
    """合并 LoRA 权重到基座模型"""
    print(f"加载基座模型: {base_model_name}")
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        torch_dtype=torch.float16,
        trust_remote_code=True,
        device_map="auto",
    )

    print(f"加载 LoRA 权重: {lora_path}")
    model = PeftModel.from_pretrained(base_model, lora_path)

    print("合并权重...")
    model = model.merge_and_unload()

    print(f"保存合并后的模型: {output_path}")
    model.save_pretrained(output_path)

    # 保存 tokenizer
    tokenizer = AutoTokenizer.from_pretrained(base_model_name, trust_remote_code=True)
    tokenizer.save_pretrained(output_path)

    print("合并完成!")
    return output_path


def convert_to_gguf(
    model_path: str,
    output_path: str,
    quantization: str = "q4_k_m",
):
    """转换为 GGUF 格式 (需要 llama.cpp)"""
    print(f"\n转换为 GGUF 格式 ({quantization})...")

    # 检查 llama.cpp 是否存在
    llama_cpp_dir = Path.home() / "llama.cpp"

    if not llama_cpp_dir.exists():
        print("\n需要先安装 llama.cpp:")
        print("  git clone https://github.com/ggerganov/llama.cpp.git ~/llama.cpp")
        print("  cd ~/llama.cpp && make")
        print("\n安装完成后重新运行此脚本")
        return None

    convert_script = llama_cpp_dir / "convert_hf_to_gguf.py"
    quantize_bin = llama_cpp_dir / "llama-quantize"

    if not convert_script.exists():
        print(f"找不到转换脚本: {convert_script}")
        return None

    # 先转换为 FP16 GGUF
    fp16_gguf = Path(output_path).parent / "model-fp16.gguf"
    print(f"转换为 FP16 GGUF: {fp16_gguf}")

    cmd = [
        "python3", str(convert_script),
        model_path,
        "--outfile", str(fp16_gguf),
        "--outtype", "f16",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"转换失败: {result.stderr}")
        return None

    # 量化
    if quantize_bin.exists() and quantization != "f16":
        quantized_gguf = Path(output_path)
        print(f"量化为 {quantization}: {quantized_gguf}")

        cmd = [
            str(quantize_bin),
            str(fp16_gguf),
            str(quantized_gguf),
            quantization,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"量化失败: {result.stderr}")
            return str(fp16_gguf)

        # 删除 FP16 中间文件
        fp16_gguf.unlink()
        return str(quantized_gguf)
    else:
        return str(fp16_gguf)


def create_modelfile(gguf_path: str, output_path: str):
    """创建 Ollama Modelfile"""
    modelfile_content = f'''FROM {gguf_path}

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER num_ctx 2048

SYSTEM """你是一个经验丰富的跨境电商销售员，做这行已经5年了。

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
'''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(modelfile_content)

    print(f"Modelfile 已创建: {output_path}")


def main():
    # 配置
    base_model_name = "Qwen/Qwen2.5-1.5B-Instruct"

    # 路径
    base_dir = Path(__file__).parent.parent
    lora_path = base_dir / "output" / "lora_model" / "lora_weights"
    merged_path = base_dir / "output" / "merged_model"
    gguf_path = base_dir / "output" / "sales-assistant.gguf"
    modelfile_path = Path(__file__).parent / "Modelfile"

    # 检查 LoRA 权重是否存在
    if not lora_path.exists():
        print(f"错误: 找不到 LoRA 权重目录: {lora_path}")
        print("请先运行训练脚本: python train_lora.py")
        return

    # Step 1: 合并权重
    print("=" * 50)
    print("Step 1: 合并 LoRA 权重")
    print("=" * 50)
    merge_lora_weights(base_model_name, str(lora_path), str(merged_path))

    # Step 2: 转换 GGUF
    print("\n" + "=" * 50)
    print("Step 2: 转换为 GGUF 格式")
    print("=" * 50)
    result_gguf = convert_to_gguf(str(merged_path), str(gguf_path))

    if result_gguf:
        # Step 3: 创建 Modelfile
        print("\n" + "=" * 50)
        print("Step 3: 创建 Ollama Modelfile")
        print("=" * 50)
        create_modelfile(result_gguf, str(modelfile_path))

        print("\n" + "=" * 50)
        print("导出完成!")
        print("=" * 50)
        print(f"\nGGUF 模型: {result_gguf}")
        print(f"Modelfile: {modelfile_path}")
        print("\n接下来运行以下命令部署到 Ollama:")
        print(f"  ollama create sales-assistant -f {modelfile_path}")
        print("  ollama run sales-assistant")
    else:
        print("\n手动导出说明:")
        print("1. 安装 llama.cpp: git clone https://github.com/ggerganov/llama.cpp.git")
        print("2. 编译: cd llama.cpp && make")
        print("3. 转换: python convert_hf_to_gguf.py <model_path> --outfile model.gguf")


if __name__ == "__main__":
    main()
