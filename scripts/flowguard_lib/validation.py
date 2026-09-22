"""产物校验引擎（照 OpenSpec validation：ERROR/WARNING/INFO 三级 + 消息/修复单源）。"""
import re
from pathlib import Path

from . import ids

HINTS = {
    "req_header": "requirement 头必须恰为 `### Requirement: <名称>`",
    "scenario_header": "scenario 头必须恰为 `#### Scenario: <名称>`（三个 # 或列表形式会静默失败）",
    "req_id": "requirement 正文首行须含反引号包裹的 REQ-ID，如 `<feature>/REQ-1`",
    "shall": "requirement 正文须包含 SHALL 或 MUST（关键词应在正文而非标题）",
    "scenario_count": "每条 requirement 至少 1 个 #### Scenario",
    "coverage": "每条 REQ 至少被一条用例覆盖（追溯矩阵）",
    "testfile": "用例须标注 `- 测试文件: <路径>`，且该文件已存在于仓库",
    "conclusion": "每条发现项须有 `- 结论: fix|wontfix|deferred`",
    "tier2": "引用的执行技能未安装",
}


def _issue(level, path, message, fix, line=None):
    out = {"level": level, "path": path, "message": message, "fix": fix}
    if line is not None:
        out["line"] = line
    return out


def _mask_code_fences(lines):
    """围栏内的行标记为不可见（照 OpenSpec code-fence 掩码）。"""
    masked, inside = [], False
    for ln in lines:
        if ln.lstrip().startswith("```"):
            inside = not inside
            masked.append(True)
            continue
        masked.append(inside)
    return masked


def requirement_ids(text):
    """抽取各 requirement 正文首行反引号内的 REQ-ID。"""
    lines = text.splitlines()
    masked = _mask_code_fences(lines)
    found, current_req = [], False
    for ln, hide in zip(lines, masked):
        if hide:
            continue
        if re.match(r"^### Requirement:", ln):
            current_req, body_seen = True, False
            continue
        if current_req:
            if re.match(r"^#### Scenario:", ln):
                current_req = False
                continue
            if not body_seen and ln.strip():
                body_seen = True
                m = re.search(r"`([^`]+)`", ln)
                if m and ids.parse_req_id(m.group(1)):
                    found.append(m.group(1))
    return found


def validate_requirements(text, feature):
    lines = text.splitlines()
    masked = _mask_code_fences(lines)
    issues = []
    seen_names = {}
    in_req, req_name, req_line, body_lines, scenario_count = False, "", 0, [], 0

    def flush():
        nonlocal in_req, req_name, req_line, body_lines, scenario_count
        if not in_req:
            return
        body = "\n".join(body_lines)
        if not re.search(r"\b(SHALL|MUST)\b", body):
            issues.append(_issue("WARNING", "01-requirements.md",
                                 f"requirement「{req_name}」正文缺 SHALL/MUST",
                                 HINTS["shall"], line=req_line))
        if scenario_count < 1:
            issues.append(_issue("WARNING", "01-requirements.md",
                                 f"requirement「{req_name}」无 Scenario",
                                 HINTS["scenario_count"], line=req_line))
        in_req = False

    for no, (ln, hide) in enumerate(zip(lines, masked), 1):
        if hide:
            continue
        stripped = ln.strip()
        m_req = re.match(r"^### Requirement: (.+?)\s*$", ln)
        m_scn = re.match(r"^#### Scenario:", ln)
        if m_req:
            flush()
            req_name = m_req.group(1).strip()
            req_line = no
            in_req, body_lines, scenario_count = True, [], 0
            folded = ids.fold_name(req_name)
            if folded in seen_names:
                issues.append(_issue("WARNING", "01-requirements.md",
                                     f"requirement 名与「{seen_names[folded]}」近似（typo?）",
                                     HINTS["req_header"], line=no))
            else:
                seen_names[folded] = req_name
            continue
        if m_scn:
            scenario_count += 1
            continue
        # stray 头：含关键词但层级/形式不是规范头
        if re.match(r"^#{1,6}\s", ln) and re.search(r"Requirement|Scenario", ln) and not m_req and not m_scn:
            issues.append(_issue("ERROR", "01-requirements.md",
                                 f"疑似层级错误的 Requirement/Scenario 头: {stripped!r}",
                                 HINTS["scenario_header"] if "Scenario" in ln else HINTS["req_header"], line=no))
            continue
        if re.match(r"^[-*]\s+#+\s", ln) and "Scenario" in ln:
            issues.append(_issue("ERROR", "01-requirements.md",
                                 f"Scenario 写成了列表项: {stripped!r}",
                                 HINTS["scenario_header"], line=no))
            continue
        if in_req:
            body_lines.append(ln)
    flush()

    # REQ-ID 校验（依赖抽取结果）
    for rid in requirement_ids(text):
        parsed = ids.parse_req_id(rid)
        if parsed is None or parsed[0] != feature:
            issues.append(_issue("ERROR", "01-requirements.md",
                                 f"REQ-ID「{rid}」不属于功能 {feature}",
                                 HINTS["req_id"]))
    return issues


def validate_testcases(text, req_ids, root):
    """追溯矩阵：每条 REQ 被覆盖；每条用例的测试文件存在。

    含 `<占位符>` 的块视为模板未填写示例，不参与机械检查。
    """
    lines = text.splitlines()
    masked = _mask_code_fences(lines)
    issues = []
    covered, cur_req, cur_file, in_case = set(), None, None, False
    placeholder = False

    def flush_case():
        nonlocal cur_req, cur_file, placeholder
        if in_case and placeholder:
            pass  # 模板示例块
        else:
            if cur_req:
                covered.add(cur_req)
            if cur_req and not cur_file:
                issues.append(_issue("ERROR", "04-testcases.md",
                                     f"用例（REQ {cur_req}）缺 `- 测试文件:` 标注",
                                     HINTS["testfile"]))
        cur_req, cur_file, placeholder = None, None, False

    for ln, hide in zip(lines, masked):
        if hide:
            continue
        if re.match(r"^### 用例", ln):
            flush_case()
            in_case, cur_req, cur_file = True, None, None
            placeholder = "<" in ln
            continue
        if in_case:
            if "<" in ln:
                placeholder = True
            m_req = re.match(r"^-\s*REQ:\s*(\S+)", ln.strip())
            m_file = re.match(r"^-\s*测试文件:\s*(\S+)", ln.strip())
            if m_req:
                cur_req = m_req.group(1)
            elif m_file:
                cur_file = m_file.group(1)
                if "<" not in cur_file and not (Path(root) / cur_file).exists():
                    issues.append(_issue("ERROR", "04-testcases.md",
                                         f"测试文件不存在: {cur_file}",
                                         HINTS["testfile"]))
    flush_case()

    for rid in req_ids:
        if rid not in covered:
            issues.append(_issue("ERROR", "04-testcases.md",
                                 f"需求未被用例覆盖: {rid}",
                                 HINTS["coverage"]))
    return issues


def validate_review(text):
    """每条发现项须有 `- 结论: fix|wontfix|deferred`。含 `<占位符>` 的块视为模板示例，跳过。"""
    lines = text.splitlines()
    masked = _mask_code_fences(lines)
    issues = []
    in_finding = False
    concluded = False
    placeholder = False

    def flush():
        nonlocal in_finding, concluded, placeholder
        if in_finding and not concluded and not placeholder:
            issues.append(_issue("ERROR", "08-review.md",
                                 "发现项缺结论",
                                 HINTS["conclusion"]))
        in_finding = False
        concluded = False
        placeholder = False

    for ln, hide in zip(lines, masked):
        if hide:
            continue
        if re.match(r"^#{2,4}\s*发现", ln):
            flush()
            in_finding = True
            placeholder = "<" in ln
            continue
        if in_finding:
            if "<" in ln:
                placeholder = True
            if re.match(r"^-\s*结论:\s*(fix|wontfix|deferred)\s*$", ln.strip()):
                concluded = True
    flush()
    return issues


def missing_tier2(refs, root=None):
    """refs: (skill, pkg, install_cmd)；已安装判定见 _installed。缺失产出 WARNING。"""
    out = []
    for skill, _pkg, cmd in refs:
        if not _installed(skill, root):
            out.append(_issue("WARNING", "skills",
                              f"执行技能未安装: {skill}",
                              cmd))
    return out


def _installed(skill, root):
    candidates = [
        Path.home() / ".agents" / "skills" / skill / "SKILL.md",
        Path.home() / ".zcode" / "skills" / skill / "SKILL.md",
    ]
    if root is not None:
        candidates.append(Path(root) / ".agents" / "skills" / skill / "SKILL.md")
    return any(p.exists() for p in candidates)
