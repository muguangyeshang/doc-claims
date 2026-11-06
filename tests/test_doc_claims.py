#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
doc-claims 正式测试（纯标准库 unittest）。

每条用例锁一个已验证过的行为或修过的坑：PASS/FAIL 退出码、豁免、
--strict 防静默绿、真值缓存、缺配置引导。
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "doc_claims.py")


def run_claims(config, extra=None, cwd=None):
    return subprocess.run([sys.executable, SCRIPT, "--config", config] + (extra or []),
                          capture_output=True, text=True, cwd=cwd or ROOT, encoding="utf-8")


class TestEndToEnd(unittest.TestCase):
    """走子进程测端到端行为（含退出码），不走 import——CLI 是主要交付面。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def write(self, name, content):
        path = os.path.join(self.tmp, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def test_pass_when_all_match(self):
        docs = self.write("docs/a.md", "本仓库有 3 个测试\n")
        self.write("claims.json", json.dumps({
            "files": [docs.replace("\\", "/")],
            "types": [{"name": "测试数", "pattern": r"(\d+) 个测试",
                       "truth": {"literal": 3}}]}, ensure_ascii=False))
        r = run_claims(os.path.join(self.tmp, "claims.json"))
        self.assertEqual(r.returncode, 0)
        self.assertIn("一致 1", r.stdout)

    def test_drift_fails_exit1(self):
        docs = self.write("docs/a.md", "本仓库有 5 个测试\n")
        self.write("claims.json", json.dumps({
            "files": [docs.replace("\\", "/")],
            "types": [{"name": "测试数", "pattern": r"(\d+) 个测试",
                       "truth": {"literal": 3}}]}, ensure_ascii=False))
        r = run_claims(os.path.join(self.tmp, "claims.json"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("实际 3", r.stdout)

    def test_exempt_line_skipped(self):
        docs = self.write("docs/a.md", "历史记录：当时 99 个测试\n现在 3 个测试\n")
        self.write("claims.json", json.dumps({
            "files": [docs.replace("\\", "/")],
            "exempt_patterns": ["历史记录"],
            "types": [{"name": "测试数", "pattern": r"(\d+) 个测试",
                       "truth": {"literal": 3}}]}, ensure_ascii=False))
        r = run_claims(os.path.join(self.tmp, "claims.json"))
        self.assertEqual(r.returncode, 0)
        self.assertIn("豁免", r.stdout)
        self.assertNotIn("99", r.stdout)

    def test_strict_zero_checked_fails(self):
        docs = self.write("docs/a.md", "没有任何可核对的内容\n")
        self.write("claims.json", json.dumps({
            "files": [docs.replace("\\", "/")],
            "types": [{"name": "测试数", "pattern": r"(\d+) 个测试",
                       "truth": {"literal": 3}}]}, ensure_ascii=False))
        r = run_claims(os.path.join(self.tmp, "claims.json"), ["--strict"])
        self.assertEqual(r.returncode, 1)
        self.assertIn("strict", r.stdout)

    def test_truth_cmd_reads_first_int(self):
        docs = self.write("docs/a.md", "共 7 个测试\n")
        counter = self.write("count.py", "print('tests: 7 collected')\n")
        self.write("claims.json", json.dumps({
            "files": [docs.replace("\\", "/")],
            "types": [{"name": "测试数", "pattern": r"(\d+) 个测试",
                       "truth": {"cmd": f'"{sys.executable}" "{counter}"'}}]},
            ensure_ascii=False))
        r = run_claims(os.path.join(self.tmp, "claims.json"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_missing_config_gives_init_hint(self):
        r = run_claims(os.path.join(self.tmp, "nope.json"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("--init", r.stdout)


class TestDemoRepo(unittest.TestCase):
    def test_demo_passes(self):
        r = run_claims(os.path.join(ROOT, "claims.json"))
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("结论：PASS", r.stdout)


if __name__ == "__main__":
    unittest.main()
