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


class TestRealMachineFixes(unittest.TestCase):
    """两个 Windows 真机实测抓到的缺陷，锁回归（CI ubuntu 上测不出，见 CHANGELOG 1.1.3 后补）。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def write(self, name, content):
        path = os.path.join(self.tmp, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def test_thousand_separator_claim(self):
        """文档写 11,700（带千分位逗号）不得崩溃，应与真值 11700 归一比对。"""
        docs = self.write("docs/a.md", "吞吐约 11,700 routes/s\n")
        self.write("claims.json", json.dumps({
            "files": [docs.replace("\\", "/")],
            "types": [{"name": "吞吐", "pattern": r"([\d,]+) routes/s",
                       "truth": {"literal": 11700}}]}, ensure_ascii=False))
        r = run_claims(os.path.join(self.tmp, "claims.json"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("一致 1", r.stdout)

    def test_thousand_separator_drift_detected(self):
        """千分位不仅要不崩，漂移也要抓得出：写 11,700 实际 9,000 → 红。"""
        docs = self.write("docs/a.md", "吞吐约 11,700 routes/s\n")
        self.write("claims.json", json.dumps({
            "files": [docs.replace("\\", "/")],
            "types": [{"name": "吞吐", "pattern": r"([\d,]+) routes/s",
                       "truth": {"literal": 9000}}]}, ensure_ascii=False))
        r = run_claims(os.path.join(self.tmp, "claims.json"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("实际 9000", r.stdout)

    def test_truth_cmd_utf8_output(self):
        """真值命令输出含中文/UTF-8 时，不得因系统 locale（Windows GBK）解码崩溃。"""
        docs = self.write("docs/a.md", "留出集 9/9\n")
        counter = self.write("count.py", "print('留出集 9/9')\n")
        self.write("claims.json", json.dumps({
            "files": [docs.replace("\\", "/")],
            "types": [{"name": "成绩", "pattern": r"留出集 (\d+)/9",
                       "truth": {"cmd": f'"{sys.executable}" "{counter}"'}}]},
            ensure_ascii=False))
        r = run_claims(os.path.join(self.tmp, "claims.json"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("一致 1", r.stdout)

    def test_truth_cmd_binary_junk_replaced_not_crash(self):
        """真值命令输出混入非法字节时，errors=replace 兜底出首个数字而不是崩。"""
        docs = self.write("docs/a.md", "共 5 个测试\n")
        # utf-8 非法字节序列 + 合法数字
        counter = self.write("count.py",
                             "import sys; sys.stdout.buffer.write(b'\\xff\\xfe 5 tests')\n")
        self.write("claims.json", json.dumps({
            "files": [docs.replace("\\", "/")],
            "types": [{"name": "测试", "pattern": r"共 (\d+) 个测试",
                       "truth": {"cmd": f'"{sys.executable}" "{counter}"'}}]},
            ensure_ascii=False))
        r = run_claims(os.path.join(self.tmp, "claims.json"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class TestNonIntegerCapture(unittest.TestCase):
    """第三轮实战抓到：模式捕获组抓到非数字（如量词"万级"）时，
    不得裸 traceback 崩掉整个进程——显式 ✗、跑完其余核对、exit 1。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def write(self, name, content):
        path = os.path.join(self.tmp, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def test_non_integer_capture_explicit_error(self):
        docs = self.write("docs/a.md", "单线程万级 routes/s" + chr(10))
        self.write("claims.json", json.dumps({
            "files": [docs.replace("\\", "/")],
            "types": [{"name": "吞吐", "pattern": r"单线程(万级) routes/s",
                       "truth": {"literal": 10000}}]}, ensure_ascii=False))
        r = run_claims(os.path.join(self.tmp, "claims.json"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("不是整数", r.stdout)
        self.assertNotIn("Traceback", r.stdout + r.stderr)

    def test_integer_capture_still_works(self):
        docs = self.write("docs/a.md", "共 7 个测试" + chr(10))
        self.write("claims.json", json.dumps({
            "files": [docs.replace("\\", "/")],
            "types": [{"name": "测试", "pattern": r"共 (\d+) 个测试",
                       "truth": {"literal": 7}}]}, ensure_ascii=False))
        r = run_claims(os.path.join(self.tmp, "claims.json"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class TestRound4Fixes(unittest.TestCase):
    """第四轮实战抓到的两个缺陷：TODO 字面量裸崩 + --init 静默覆盖手工配置。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def write(self, name, content):
        path = os.path.join(self.tmp, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def test_todo_literal_explicit_error_not_crash(self):
        """--init 生成的 TODO 模板用户忘改 → 显式 ✗ 带改进提示，不裸 traceback。"""
        docs = self.write("docs/a.md", "本仓库有 2 篇文档" + chr(10))
        self.write("claims.json", json.dumps({
            "files": [docs.replace("\\", "/")],
            "types": [{"name": "文档数", "pattern": r"(\d+) 篇文档",
                       "truth": {"literal": "TODO"}}]}, ensure_ascii=False))
        r = run_claims(os.path.join(self.tmp, "claims.json"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("TODO", r.stdout)
        self.assertNotIn("Traceback", r.stdout + r.stderr)

    def test_init_refuses_overwrite(self):
        """--init 对已有配置必须拒绝——手工调好的 claims.json 是数据。"""
        keep = self.write("keep.json", '{"手工": "保留"}')
        r = subprocess.run(
            [sys.executable, SCRIPT, "--init", keep],
            capture_output=True, text=True, cwd=ROOT, encoding="utf-8")
        self.assertEqual(r.returncode, 1)
        self.assertIn("已存在", r.stdout)
        self.assertEqual(json.load(open(keep, encoding="utf-8")), {"手工": "保留"})


class TestDemoRepo(unittest.TestCase):
    def test_demo_passes(self):
        r = run_claims(os.path.join(ROOT, "claims.json"))
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("结论：PASS", r.stdout)


if __name__ == "__main__":
    unittest.main()
