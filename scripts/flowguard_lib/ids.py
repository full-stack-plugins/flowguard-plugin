"""kebab 与 REQ-ID 文法（错误文案单源）。"""
import re

KEBAB_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REQ_RE = re.compile(r"^([a-z0-9]+(?:-[a-z0-9]+)*)/REQ-(\d+)$")
KEBAB_FIX = "仅小写字母/数字/连字符，不得首尾或连续连字符"


def is_kebab(s):
    return bool(KEBAB_RE.match(s or ""))


def req_id(feature, n):
    return f"{feature}/REQ-{n}"


def parse_req_id(s):
    m = REQ_RE.match((s or "").strip())
    return (m.group(1), int(m.group(2))) if m else None


def fold_name(s):
    """requirement 名归一化（去 ATX 前导/闭合 #、折叠空白、小写），用于 typo 近失检测。"""
    t = (s or "").strip().lstrip("#").strip().rstrip("#").strip()
    return " ".join(t.split()).lower()
