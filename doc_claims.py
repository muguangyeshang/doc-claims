#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
doc-claims —— 活文档数字核对器

问题：README/手册里写的数字（"共 2987 个技能"、"46 项检查"）会随仓库演化漂移，
没人记得改，读的人被误导。测试拦不住文档，文档自己不会跑。

做法：把每类数字登记成「正则模式 + 真值重算命令」，扫描活文档逐处与重算值比对：
- 一致 → ✓
- 不一致 → ✗（退出码 1，可接 CI）
- 命中豁免模式 → 跳过（历史记录、引用原文不算活声明）

纯标准库。配置外置（JSON），真值来自任意 shell 命令或字面量，可接任何语言的项目。

用法：
  python doc_claims.py --config claims.json
  python doc_claims.py --config claims.json --strict   # 0 处核对也判 FAIL
退出码：0 全一致；1 有不一致（或 --strict 且没核到任何处）。
"""
import argparse
import glob
import json
import re
import subprocess
import sys


def truth_value(spec, cache):
    """取真值：literal 直接用；cmd 跑 shell 命令取输出里第一个整数。
    结果按 spec 缓存——同一类数字不用每处命中都重算一遍。"""
    key = json.dumps(spec, sort_keys=True)
    if key in cache:
        return cache[key]
    if "literal" in spec:
        v = int(spec["literal"])
    elif "cmd" in spec:
        r = subprocess.run(spec["cmd"], shell=True, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"真值命令失败 rc={r.returncode}: {spec['cmd']}\n{r.stderr}")
        m = re.search(r"\d+", r.stdout)
        if not m:
            raise RuntimeError(f"真值命令输出里没有数字: {spec['cmd']} -> {r.stdout[:80]!r}")
        v = int(m.group())
    else:
        raise RuntimeError(f"真值配置缺 literal/cmd: {spec}")
    cache[key] = v
    return v


def main():
    ap = argparse.ArgumentParser(description="活文档数字核对器")
    ap.add_argument("--config", required=True, help="claims 配置 JSON")
    ap.add_argument("--strict", action="store_true",
                    help="一处都没核到也判 FAIL（防止模式写错导致静默 0 核对）")
    a = ap.parse_args()

    cfg = json.load(open(a.config, encoding="utf-8-sig"))
    types = cfg["types"]
    if not types:
        sys.exit("types 为空：没有登记任何数字类型")
    files = sorted({fp for pat in cfg.get("files", []) for fp in glob.glob(pat, recursive=True)})
    if not files:
        sys.exit("没有匹配到任何待扫文件，检查 files 模式")
    exempt = [re.compile(p) for p in cfg.get("exempt_patterns", [])]
    cache = {}

    total = ok = bad = 0
    for fp in files:
        try:
            lines = open(fp, encoding="utf-8").read().splitlines()
        except (OSError, UnicodeDecodeError) as e:
            print(f"  – {fp}: 跳过（{e}）")
            continue
        for i, line in enumerate(lines, 1):
            # 豁免：历史记录、引用旧文不算活声明。豁免按整行判，写在配置里可审计
            if any(e.search(line) for e in exempt):
                continue
            for t in types:
                for m in re.finditer(t["pattern"], line):
                    total += 1
                    written = int(m.group(1))
                    try:
                        actual = truth_value(t["truth"], cache)
                    except RuntimeError as e:
                        print(f"  ✗ {fp}:{i} {t['name']} 真值取不到：{e}")
                        bad += 1
                        continue
                    if written == actual:
                        ok += 1
                        print(f"  ✓ {fp}:{i} {t['name']} 写 {written}")
                    else:
                        bad += 1
                        print(f"  ✗ {fp}:{i} {t['name']} 写 {written}，实际 {actual}｜{line.strip()[:60]}")

    print("-" * 60)
    print(f"核对 {total} 处 · 一致 {ok} · 不一致 {bad} · 豁免模式 {len(exempt)} 个")
    if total == 0 and a.strict:
        print("结论：FAIL（--strict：一处都没核到，模式可能写错了）")
        return 1
    print("结论：PASS" if bad == 0 else "结论：FAIL")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
