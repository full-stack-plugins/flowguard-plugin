"""Lifecycle commands for a Guard plugin whose domain runtime is not implemented."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = os.environ.get("GUARD_TOOL") or json.loads((ROOT / "plugin.json").read_text())["name"]


def result(command, decision, **extra):
    code = {"allow": 0, "deny": 1, "error": 2, "unverified": 3}.get(decision, 4)
    return {"schemaVersion": "partme.guard/v1", "tool": TOOL, "command": f"{TOOL}.{command}",
            "decision": decision, "exitCode": code, "findings": [], "evidence": {}, **extra}


def main(argv):
    command = argv[0] if argv else "status"
    if command == "version":
        data = json.loads((ROOT / "plugin.json").read_text())
        payload = result("version", "allow", version=data["version"])
    elif command in ("doctor", "status"):
        payload = result(command, "unverified", capability="DESIGN_ONLY",
                         nextActions=["implement the domain runtime before claiming a gate result"])
    elif command == "discover":
        payload = result("discover", "allow", project={"root": str(Path.cwd())}, capability="DESIGN_ONLY")
    elif command == "check":
        payload = result("check", "unverified", findings=[{"code": "DESIGN_ONLY", "severity": "warning"}],
                         capability="DESIGN_ONLY")
    elif command == "init":
        target = Path.cwd() / ".guard" / f"{TOOL}.json"
        if "--dry-run" in argv:
            payload = result("init", "allow", dryRun=True, path=str(target))
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps({"tool": TOOL, "mode": "DESIGN_ONLY"}, indent=2) + "\n")
            payload = result("init", "allow", created=str(target))
    else:
        print(f"usage: {TOOL} version|doctor|status|discover|check|init [--dry-run]", file=sys.stderr)
        return 2
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return payload["exitCode"]


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
