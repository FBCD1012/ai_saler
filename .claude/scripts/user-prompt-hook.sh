#!/bin/bash
# Claude Code UserPromptSubmit Hook
# 处理用户输入：# 开头添加记忆，!context 显示上下文

PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
MEMORY_FILE="$PROJECT_DIR/CLAUDE.md"
CONTEXT_FILE="$PROJECT_DIR/.claude/my-context.md"

# 从 stdin 读取 JSON 输入
json_input=$(cat)

# 用 jq 提取 prompt 字段
PROMPT=$(echo "$json_input" | jq -r '.prompt // ""' 2>/dev/null)

if [ -z "$PROMPT" ]; then
  exit 0
fi

# 处理 ## 开头：草稿模式，让 Claude 润色后确认再写入
if [[ "$PROMPT" == \#\#* ]]; then
    CONTENT="${PROMPT#\#\#}"
    CONTENT="${CONTENT# }"
    cat << EOF
【润色任务】
草稿内容：「$CONTENT」

请执行：
1. 润色为简洁清晰的记忆条目
2. 展示给用户确认
3. 确认后用 Edit 追加到 CLAUDE.md 记忆日志
   格式：- [$(date "+%Y-%m-%d %H:%M")] 润色后内容
EOF
    exit 0
fi

# 处理 # 开头：添加记忆
if [[ "$PROMPT" == \#* ]]; then
    CONTENT="${PROMPT#\#}"
    CONTENT="${CONTENT# }"
    TIMESTAMP=$(date "+%Y-%m-%d %H:%M")
    echo "- [$TIMESTAMP] $CONTENT" >> "$MEMORY_FILE"
    echo "Memory added: $CONTENT"
    exit 0
fi

# 处理 !context：显示上下文
if [[ "$PROMPT" == "!context"* ]]; then
    cat "$CONTEXT_FILE"
    exit 0
fi

# 默认：显示上下文（每次都提醒偏好）
cat "$CONTEXT_FILE"
exit 0
