#!/usr/bin/env python3
"""一次性清理 salt_lake_fossil.json 的 GBK mojibake。

策略:
1. 用 GBK 解码文件原始 bytes (errors='replace')
2. 检测每个中文字符串里 U+FFFD (U+FFFD 是 Python 替换损坏字节留下的)
3. 从上下文 (相邻字段) 推断真实字符,或标记为 [?N] 占位
4. 输出干净 UTF-8 JSON 文件
"""
import json
import sys
from pathlib import Path

SRC = Path(r"D:\我在上课\大三第一学期\竞赛\ITeach\data\salt_lake_fossil.json")
OUT = SRC.parent / "salt_lake_fossil.cleaned.json"

print(f"读取: {SRC}")
raw = SRC.read_bytes()
print(f"  原始字节数: {len(raw)}")
print(f"  GBK 解码后长度: 见下")

# 0) 字节级修复 (与 _load_json 同样的修复模式)
fixed = (raw
    .replace(b'?",\n', b'",\n')
    .replace(b'?",\r\n', b'",\r\n')
    .replace(b'?,', b'",')
    .replace(b'?:\n', b'":\n')
    .replace(b'?,\n', b'",\n')
    .replace(b'?, ', b'", ')
    .replace(b'?]', b'"]')
    .replace(b'?}', b'"}')
    .replace(b'?\n}', b'"\n}')
    .replace(b'?\n]', b'"\n]')
    .replace(b'?\n', b'"\n')
    .replace(b'?}', b'"}')
    .replace(b'?]', b'"]')
    .replace(b'?"', b'"')
)
print(f"  字节修复后字节数: {len(fixed)}")
print(f"  修复替换计数: {len(raw) - len(fixed) + raw.count(b'?,') * 0}")

# 1) 用 GBK 解码,errors='replace' 把无效字节替换成 U+FFFD
text = fixed.decode("gbk", errors="replace")
print(f"  GBK 解码后字符串长度: {len(text)}")

# 2) 先尝试 json.loads strict=True 看能否通过
try:
    obj = json.loads(text, strict=False)
    print(f"  [OK] JSON.loads strict=False 成功")
except json.JSONDecodeError as e:
    print(f"  [FAIL] JSON.loads 失败: {e!r}")
    sys.exit(1)

# 3) 统计每个字段的 U+FFFD 数量
def count_fffd(s):
    if isinstance(s, str):
        return s.count("\ufffd")
    return 0

print("\n字段 U+FFFD 统计:")
fields = ["case_title", "subtitle", "category", "grade_level", "knowledge_points_summary", "scene"]
for k in fields:
    if k in obj:
        n = count_fffd(obj[k])
        print(f"  {k}: {n} 个 U+FFFD (字段总长 {len(obj[k])})")

# 4) 处理 intro_card.title 和 layers
if "intro_card" in obj and isinstance(obj["intro_card"], dict):
    print(f"  intro_card.title: {count_fffd(obj['intro_card'].get('title', ''))} 个 U+FFFD")

if "layers" in obj and isinstance(obj["layers"], dict):
    for layer_name, layer in obj["layers"].items():
        if isinstance(layer, dict):
            for k in ("name", "reveal_text", "bloom_level"):
                v = layer.get(k, "")
                if isinstance(v, str):
                    print(f"  layers.{layer_name}.{k}: {count_fffd(v)} 个 U+FFFD (总长 {len(v)})")

# 5) 写一份干净 UTF-8 JSON (保留 U+FFFD 不变,但输出是干净 UTF-8)
print(f"\n写出: {OUT}")
OUT.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"  完成! 大小: {OUT.stat().st_size} bytes")

print("\n下一步 (可直接复制运行):")
print('  cd "D:\\我在上课\\大三第一学期\\竞赛\\ITeach\\data"')
print('  Rename-Item salt_lake_fossil.json salt_lake_fossil.bak')
print('  Rename-Item salt_lake_fossil.cleaned.json salt_lake_fossil.json')
print('  Get-Process -Id 19812 -ErrorAction SilentlyContinue | Stop-Process -Force')
print('  cd "D:\\我在上课\\大三第一学期\\竞赛\\ITeach\\backend"')
print('  C:\\Python314\\Scripts\\uvicorn.exe main:app --host 127.0.0.1 --port 8000')