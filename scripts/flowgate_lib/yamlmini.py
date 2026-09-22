"""config.yaml 子集解析器（stdlib-only，不引 PyYAML）。

支持的形状（超出即 ValueError）：
- 顶层标量：`key: value`
- 顶层字面块：`key: |` + 两空格缩进行
- 两层嵌套映射：`key:` 空值，随后两空格 `subkey: value`
- 列表：顶层 `key:` + 两空格 `- item`；或 `key:` + `subkey:` + 四空格 `- item`
"""


def load(text):
    root = {}
    cur_top = None      # 当前顶层键
    cur_sub = None      # 当前两层映射的子键
    block_key = None    # 字面块收集中的顶层键
    block_lines = []

    def _end_block():
        nonlocal block_key
        if block_key is not None:
            root[block_key] = "\n".join(block_lines).rstrip("\n")
            block_key = None

    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip("\n")
        stripped = line.strip()
        indent = len(line) - len(line.lstrip(" "))

        if stripped == "" or stripped.startswith("#"):
            if block_key is not None:
                block_lines.append("")
            continue

        if block_key is not None:
            if indent >= 2:
                block_lines.append(line[2:])
                continue
            _end_block()  # 缩进回 0：块结束，本行继续按常规解析

        if stripped.startswith("- "):
            item = stripped[2:].strip().strip('"')
            if indent == 4 and cur_top is not None and cur_sub is not None:
                slot = root[cur_top].get(cur_sub)
                if slot is None or slot == {}:
                    slot = []
                elif not isinstance(slot, list):
                    raise ValueError(f"unsupported yaml shape at line {lineno}: {raw!r}")
                slot.append(item)
                root[cur_top][cur_sub] = slot
            elif indent == 2 and cur_top is not None and cur_sub is None:
                slot = root.get(cur_top)
                if slot is None or slot == {}:
                    slot = []
                elif not isinstance(slot, list):
                    raise ValueError(f"unsupported yaml shape at line {lineno}: {raw!r}")
                slot.append(item)
                root[cur_top] = slot
            else:
                raise ValueError(f"unsupported yaml shape at line {lineno}: {raw!r}")
            continue

        key, sep, val = stripped.partition(":")
        if not sep:
            raise ValueError(f"unsupported yaml shape at line {lineno}: {raw!r}")
        key, val = key.strip(), val.strip()

        if indent == 0:
            cur_top, cur_sub = key, None
            if val == "|":
                block_key, block_lines = key, []
                root[key] = ""  # 块结束时覆盖
            elif val == "":
                root[key] = {}  # 占位：后续按列表/映射实化
            else:
                root[key] = val.strip('"')
        elif indent == 2:
            if not isinstance(root.get(cur_top), dict):
                raise ValueError(f"unsupported yaml shape at line {lineno}: {raw!r}")
            if val == "|":
                raise ValueError(f"unsupported yaml shape at line {lineno}: 字面块仅支持顶层")
            cur_sub = key
            if val == "":
                root[cur_top].setdefault(key, {})
            else:
                root[cur_top][key] = val.strip('"')
        else:
            raise ValueError(f"unsupported yaml shape at line {lineno}: {raw!r}")

    _end_block()
    return root


def dump(data):
    lines = []
    for key, val in data.items():
        if isinstance(val, str) and "\n" in val:
            lines.append(f"{key}: |")
            lines.extend(f"  {ln}" for ln in val.splitlines())
        elif isinstance(val, dict):
            lines.append(f"{key}:")
            for sub, sval in val.items():
                if isinstance(sval, list):
                    lines.append(f"  {sub}:")
                    lines.extend(f"    - {item}" for item in sval)
                else:
                    lines.append(f"  {sub}: {sval}")
        elif isinstance(val, list):
            lines.append(f"{key}:")
            lines.extend(f"  - {item}" for item in val)
        else:
            lines.append(f"{key}: {val}")
    return "\n".join(lines) + "\n"
