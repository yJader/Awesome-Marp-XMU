#!/usr/bin/env bash
# 将 themes/assets/xmu_logo_name.b64 的内容注入 themes/am_xmu.scss 中的 __XMU_BASE64__ 占位符
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
B64_FILE="$ROOT_DIR/themes/assets/xmu_logo_name.b64"
SCSS_FILE="$ROOT_DIR/themes/am_xmu.scss"

if [ ! -f "$B64_FILE" ]; then
  echo "Base64 file not found: $B64_FILE"
  exit 1
fi

if [ ! -f "$SCSS_FILE" ]; then
  echo "SCSS file not found: $SCSS_FILE"
  exit 1
fi

# 读取 Base64 内容并去除换行
BASE64_CONTENT=$(tr -d '\n' < "$B64_FILE")

# 做一次安全替换：把占位符替换为 base64 内容，但跳过 /* */ 注释中的内容
# 使用临时文件防止替换出错
TMP_FILE=$(mktemp)

awk -v b64="$BASE64_CONTENT" '
BEGIN { in_comment = 0 }
{
  line = $0
  result = ""
  i = 1
  while (i <= length(line)) {
    # 检查是否进入注释
    if (!in_comment && substr(line, i, 2) == "/*") {
      in_comment = 1
      result = result substr(line, i, 2)
      i += 2
      continue
    }
    # 检查是否离开注释
    if (in_comment && substr(line, i, 2) == "*/") {
      in_comment = 0
      result = result substr(line, i, 2)
      i += 2
      continue
    }
    # 在注释外才替换占位符
    if (!in_comment && substr(line, i, 15) == "__XMU_BASE64__") {
      result = result b64
      i += 15
    } else {
      result = result substr(line, i, 1)
      i += 1
    }
  }
  print result
}
' "$SCSS_FILE" > "$TMP_FILE"

mv "$TMP_FILE" "$SCSS_FILE"
chmod 644 "$SCSS_FILE"

echo "已将 Base64 内容注入到 $SCSS_FILE (跳过注释) "
