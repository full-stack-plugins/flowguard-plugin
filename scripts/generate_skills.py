#!/usr/bin/env python3
"""从 scripts/templates/workflows.py 生成 skills/ 下全部 SKILL.md 与产物模板。

SKILL.md 是生成物：改内容请改模板源，再运行本脚本（parity 测试强制一致）。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from templates import artifacts
from templates.workflows import SKILL_SPECS, render_skill


def generate(root=None):
    root = Path(root) if root else ROOT
    skills = root / "skills"
    skills.mkdir(exist_ok=True)
    for spec in SKILL_SPECS:
        d = skills / spec["name"]
        d.mkdir(exist_ok=True)
        (d / "SKILL.md").write_text(render_skill(spec), encoding="utf-8")
        # 产物模板落到对应阶段技能的 references/templates/
        if spec["artifact"]:
            aid = spec["artifact"]
            tdir = d / "references" / "templates"
            tdir.mkdir(parents=True, exist_ok=True)
            ctx = {"feature": "<feature-id>", "title": spec["stage"], "modules": "<modules>",
                   "req_prefix": "<feature-id>/REQ"}
            (tdir / f"{aid}.md").write_text(artifacts.render(aid, ctx), encoding="utf-8")
    return len(SKILL_SPECS)


if __name__ == "__main__":
    n = generate()
    print(f"generated {n} skills")
