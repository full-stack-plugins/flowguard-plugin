"""instructions 命令面：给编排技能的机读指令（context/rules 来自 config.yaml，照 OpenSpec）。"""
from pathlib import Path

from . import registry, yamlmini

_DEFAULT_CONFIG = {"context": "", "rules": {}}


def load_config(root):
    p = Path(root) / ".flowgate" / "config.yaml"
    if not p.exists():
        return dict(_DEFAULT_CONFIG)
    data = yamlmini.load(p.read_text(encoding="utf-8"))
    return {"context": data.get("context", ""), "rules": data.get("rules", {})}


def build(root, artifact_id, feature=None):
    art = registry.ARTIFACTS.get(artifact_id)
    if art is None:
        raise KeyError(f"未知 artifact: {artifact_id}")
    cfg = load_config(root)
    stage = art["stage"]
    template = f"skills/flowgate-{stage}/references/templates/{_TEMPLATE_NAMES[artifact_id]}"
    tier2 = [(skill, pkg, registry.install_cmd(skill, pkg))
             for skill, pkg in registry.TIER2_REFS.get(stage, [])]
    return {
        "artifact": artifact_id,
        "scope": art["scope"],
        "stage": stage,
        "context": cfg["context"],
        "rules": cfg["rules"],
        "template": template,
        "requires": list(art["requires"]),
        "unlocks": [nid for nid, a in registry.ARTIFACTS.items() if artifact_id in a["requires"]],
        "tier2": tier2,
    }


# artifact id → 产物文件名（模板文件与产物同名，便于机械定位）
_TEMPLATE_NAMES = {
    "01-requirements": "01-requirements.md",
    "02-architecture": "02-architecture.md",
    "03-solution": "03-solution.md",
    "04-testcases": "04-testcases.md",
    "05-hld": "05-hld.md",
    "06-lld": "06-lld.md",
    "07-standards": "07-standards.md",
    "08-review": "08-review.md",
    "09-docs": "09-docs.md",
    "10-release": "10-release.md",
}
