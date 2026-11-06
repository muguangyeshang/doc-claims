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
import os
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
        # literal 也可能是忘改的 TODO 或写错的量词——显式报错走 ✗ 通路，
        # 不裸 traceback（第四轮实战抓到：--init 生成的 TODO 模板用户忘改即崩）
        try:
            v = int(spec["literal"])
        except (ValueError, TypeError):
            raise RuntimeError(f"literal 不是整数: {spec['literal']!r}——"
                               "把 TODO 换成真值命令或整数字面量") from None
    elif "cmd" in spec:
        # Windows 真机坑：text=True 默认走系统 locale（GBK），子进程输出 UTF-8 会崩。
        # 显式 UTF-8 + errors=replace，CI(ubuntu)/本地(Windows) 行为一致。
        r = subprocess.run(spec["cmd"], shell=True, capture_output=True,
                           text=True, encoding="utf-8", errors="replace")
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


def cmd_init(args):
    """脚手架：扫文档，按常见数字声明场景生成 claims.json 初稿。
    用户 80% 的成本在写配置——init 把从零到第一份可用配置的时间压到一条命令。"""
    # 手工调好的 claims.json 是数据不是脚手架，--init 拒绝覆盖（与 flow-router init 一致）。
    # 第四轮实战抓到：对已有配置重跑 --init 把手工配置静默抹掉了。
    if os.path.exists(args.init):
        print(f"{args.init} 已存在，不动它。要重生成先手工删掉或换文件名。")
        return 1
    md_files = []
    for pat in ["**/*.md", "*.md"]:
        md_files += glob.glob(pat, recursive=True)
    md_files = sorted(set(md_files))
    if not md_files:
        sys.exit("当前目录没有 markdown 文件，--init 无从下手")

    # 常见声明场景 → 模式 + 默认真值（literal 留待用户填；cmd 给了可跑的探针）
    candidates = [
        ("测试数量", r"(\d+) 个测试", {"cmd": "pytest --collect-only -q 2>/dev/null | tail -1"}),
        ("文档文件数", r"(\d+) 篇文档", {"literal": "TODO"}),
        ("模块数", r"(\d+) 个模块", {"literal": "TODO"}),
        ("版本号", r"version (\d+)\.\d+\.\d+", {"literal": "TODO"}),
    ]
    found = []
    for name, pat, truth in candidates:
        rx = re.compile(pat)
        hits = []
        for fp in md_files:
            try:
                text = open(fp, encoding="utf-8").read()
            except (OSError, UnicodeDecodeError):
                continue
            hits += [(fp, m.group(1)) for m in rx.finditer(text)]
        if hits:
            found.append((name, pat, truth, hits[:5]))

    out = {
        "files": ["*.md", "docs/**/*.md"],
        "exempt_patterns": ["历史记录", "引用原文", "例：", "例如"],
        "types": [{"name": n, "pattern": p, "truth": t} for n, p, t, _ in found]
                or [{"name": "示例总数", "pattern": r"(\d+) 个条目", "truth": {"literal": 0}}],
    }
    with open(args.init, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"已生成 {args.init}（扫描 {len(md_files)} 份 md，识别出 {len(found)} 类数字声明）：")
    for n, p, t, hits in found:
        print(f"  {n}: 模式 {p!r}，命中 {len(hits)}+ 处，如 {hits[0] if hits else '-'}")
    print("下一步：把 truth 里的 TODO 换成真值命令或字面量，然后跑 "
          f"python doc_claims.py --config {args.init} --strict")
    return 0


def main():
    ap = argparse.ArgumentParser(description="活文档数字核对器")
    ap.add_argument("--config", help="claims 配置 JSON")
    ap.add_argument("--strict", action="store_true",
                    help="一处都没核到也判 FAIL（防止模式写错导致静默 0 核对）")
    ap.add_argument("--init", metavar="OUT.json",
                    help="脚手架：扫文档生成 claims 初稿（--config 可省）")
    a = ap.parse_args()

    if a.init:
        return cmd_init(a)
    if not a.config:
        ap.error("--init 或 --config 必须给一个")
    if not os.path.exists(a.config):
        print(f"配置文件 {a.config} 不存在——第一次用？跑 python doc_claims.py "
              f"--init {a.config} 生成初稿")
        return 1

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
                    # 千分位逗号：文档常写 "11,700"，JSON/真值侧是 11700，比对前归一
                    # 捕获组必须是整数：抓到非数字（如"万级"）= 模式写错，
                    # 显式报 ✗ 并继续跑完其余核对，不裸 traceback 崩掉整个进程
                    # （2026-11-07 实战第三轮抓到：README 改成"万级 routes/s"
                    #  量级表述后，旧模式 ([\d,]+) 之外的写法会抓到非数字）
                    try:
                        written = int(m.group(1).replace(",", ""))
                    except ValueError:
                        total += 1
                        bad += 1
                        print(f"  ✗ {fp}:{i} {t['name']} 模式捕获组不是整数（'{m.group(1)}'），检查 pattern "
                              f"是否把量词也包进了捕获组｜{line.strip()[:60]}")
                        continue
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
