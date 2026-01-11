#!/usr/bin/env python3
"""
LoRA 微调训练脚本 - 适配 Mac M2 16GB
基于 Qwen2.5-1.5B-Instruct 模型
"""
import os
import json

# 极限省内存设置
os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"  # 不限制 MPS 内存上限
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForSeq2Seq,
)
from peft import LoraConfig, get_peft_model, TaskType
from datasets import Dataset


@dataclass
class ModelConfig:
    """模型配置"""
    model_name: str = "Qwen/Qwen2.5-1.5B-Instruct"  # 1.5B 效果更好
    max_length: int = 256  # 加长序列，学习更完整


@dataclass
class LoRAConfig:
    """LoRA 配置 - 平衡效果和内存"""
    r: int = 8  # 增加rank提升学习能力
    lora_alpha: int = 16
    lora_dropout: float = 0.05
    target_modules: list = field(default_factory=lambda: [
        "q_proj", "k_proj", "v_proj", "o_proj"  # 更多层参与训练
    ])


def load_training_data(data_path: str) -> list[dict]:
    """加载训练数据"""
    with open(data_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def format_prompt(sample: dict) -> str:
    """格式化成 Qwen 的对话格式"""
    instruction = sample.get('instruction', '')
    input_text = sample.get('input', '')
    output = sample.get('output', '')

    # Qwen 对话格式
    if input_text:
        prompt = f"<|im_start|>system\n{instruction}<|im_end|>\n<|im_start|>user\n{input_text}<|im_end|>\n<|im_start|>assistant\n{output}<|im_end|>"
    else:
        prompt = f"<|im_start|>system\n{instruction}<|im_end|>\n<|im_start|>assistant\n{output}<|im_end|>"

    return prompt


def preprocess_dataset(
    samples: list[dict],
    tokenizer,
    max_length: int = 512
) -> Dataset:
    """预处理数据集"""

    def tokenize(examples):
        prompts = [format_prompt(s) for s in examples]

        model_inputs = tokenizer(
            prompts,
            max_length=max_length,
            truncation=True,
            padding=False,
        )

        # 设置 labels
        model_inputs["labels"] = model_inputs["input_ids"].copy()

        return model_inputs

    # 转换为 Dataset
    dataset = Dataset.from_list(samples)

    # 批量处理
    tokenized = []
    for sample in samples:
        prompt = format_prompt(sample)
        tokens = tokenizer(
            prompt,
            max_length=max_length,
            truncation=True,
            padding=False,
            return_tensors=None,
        )
        tokens["labels"] = tokens["input_ids"].copy()
        tokenized.append(tokens)

    return Dataset.from_list(tokenized)


def get_device():
    """获取训练设备"""
    if torch.backends.mps.is_available():
        return "mps"
    elif torch.cuda.is_available():
        return "cuda"
    else:
        return "cpu"


def main():
    # 配置
    model_config = ModelConfig()
    lora_config = LoRAConfig()

    # 路径
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data" / "training_data"
    output_dir = base_dir / "output" / "lora_model"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 设备检测
    device = get_device()
    print(f"训练设备: {device}")

    if device == "mps":
        print("检测到 Apple Silicon，使用 MPS 加速")
    elif device == "cpu":
        print("警告: 使用 CPU 训练会非常慢!")

    # 加载 tokenizer
    print(f"\n加载模型: {model_config.model_name}")
    tokenizer = AutoTokenizer.from_pretrained(
        model_config.model_name,
        trust_remote_code=True,
        padding_side="right",
    )

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # 加载模型 - 极限省内存
    print("加载基座模型...")
    model = AutoModelForCausalLM.from_pretrained(
        model_config.model_name,
        torch_dtype=torch.float16,  # float16 省一半内存
        trust_remote_code=True,
        low_cpu_mem_usage=True,
    )
    # 先不移到 MPS，让 Trainer 自己管理

    # 配置 LoRA
    print("\n配置 LoRA...")
    peft_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=lora_config.r,
        lora_alpha=lora_config.lora_alpha,
        lora_dropout=lora_config.lora_dropout,
        target_modules=lora_config.target_modules,
        bias="none",
    )

    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    # 加载数据
    print("\n加载训练数据...")
    train_data = load_training_data(data_dir / "train.json")
    val_data = load_training_data(data_dir / "val.json")

    print(f"训练集: {len(train_data)} 条")
    print(f"验证集: {len(val_data)} 条")

    # 预处理数据
    train_dataset = preprocess_dataset(train_data, tokenizer, model_config.max_length)
    val_dataset = preprocess_dataset(val_data, tokenizer, model_config.max_length)

    # 数据整理器
    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        padding=True,
        return_tensors="pt",
    )

    # 训练参数 - 优化学习效果
    training_args = TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=5,  # 增加训练轮数
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=8,  # 减少累积，更频繁更新
        learning_rate=5e-4,  # 提高学习率
        warmup_ratio=0.1,
        weight_decay=0.01,
        logging_steps=10,
        save_steps=50,
        eval_strategy="steps",
        eval_steps=50,
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        fp16=False,
        bf16=False,
        dataloader_pin_memory=False,
        report_to="none",
        optim="adamw_torch",  # AdamW效果更好
    )

    # 创建 Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=data_collator,
        tokenizer=tokenizer,
    )

    # 开始训练
    print("\n开始训练...")
    print("=" * 50)
    trainer.train()

    # 保存模型
    print("\n保存 LoRA 权重...")
    model.save_pretrained(output_dir / "lora_weights")
    tokenizer.save_pretrained(output_dir / "lora_weights")

    print(f"\n训练完成! 模型保存在: {output_dir / 'lora_weights'}")


if __name__ == "__main__":
    main()
