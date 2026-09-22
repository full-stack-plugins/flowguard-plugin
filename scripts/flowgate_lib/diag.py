"""诊断信封：{severity, code, message, fix} —— 门禁/校验/命令输出单源格式。"""
import json, sys


def envelope(severity, code, message, fix):
    assert severity in ("ERROR", "WARNING", "INFO"), f"非法 severity: {severity}"
    return {"severity": severity, "code": code, "message": message, "fix": fix}


def emit(env, as_json=False):
    """人类模式走 stderr 两行（Error/Fix 约定）；JSON 模式走 stdout 单行。"""
    if as_json:
        print(json.dumps(env, ensure_ascii=False))
    else:
        print(f"{env['severity']}: {env['message']}", file=sys.stderr)
        print(f"Fix: {env['fix']}", file=sys.stderr)
