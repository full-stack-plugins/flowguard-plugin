#!/usr/bin/env python3
"""从宿主通用 JSON 命令机械生成 Kimi 所需的 Markdown 命令。"""

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "commands"
TARGET = ROOT / "kimi-commands"


def render_command(data):
    name = data["name"]
    description = json.dumps(data["description"], ensure_ascii=False)
    prompt = data["prompt"].replace("${CLAUDE_PLUGIN_ROOT}", "${KIMI_PLUGIN_ROOT}")
    note = (
        "执行前确认已启用的 FlowGuard 插件根目录。若 Shell 环境未提供 "
        "`KIMI_PLUGIN_ROOT`，通过 `/plugins info flowguard` 定位安装目录并将下方路径改为绝对路径；"
        "不要在目标 Git 项目中猜测或执行同名脚本。\n\n"
    )
    return f"---\nname: {name}\ndescription: {description}\n---\n\n{note}{prompt.rstrip()}\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="写入生成的 Markdown 文件")
    args = parser.parse_args()
    if args.write:
        TARGET.mkdir(parents=True, exist_ok=True)
    errors = []
    for source in sorted(SOURCE.glob("flowguard-*.json")):
        expected = render_command(json.loads(source.read_text(encoding="utf-8")))
        target = TARGET / f"{source.stem}.md"
        if args.write:
            target.write_text(expected, encoding="utf-8")
        elif not target.exists() or target.read_text(encoding="utf-8") != expected:
            errors.append(str(target.relative_to(ROOT)))
    if errors:
        parser.exit(1, "Kimi 命令缺失或与 JSON 源不一致: " + ", ".join(errors) + "\n")


if __name__ == "__main__":
    main()
