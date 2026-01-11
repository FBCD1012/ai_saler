#!/bin/bash
# Claude Code Memory Hook Script (项目级)
# 当用户输入以 # 开头时，将内容添加到项目记忆文件

PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
MEMORY_FILE="$PROJECT_DIR/CLAUDE.md"
PROMPT="$1"

# 检查是否以 # 开头
if [[ "$PROMPT" == \#* ]]; then
    # 提取 # 后面的内容（去掉开头的 # 和空格）
    CONTENT="${PROMPT#\#}"
    CONTENT="${CONTENT# }"

    # 添加时间戳和内容到记忆日志部分
    TIMESTAMP=$(date "+%Y-%m-%d %H:%M")
    echo "- [$TIMESTAMP] $CONTENT" >> "$MEMORY_FILE"

    # 输出确认信息
    echo "✓ 已添加到项目记忆: $CONTENT"
fi

exit 0
