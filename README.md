# doc-claims

[![CI](https://github.com/AYAN-2026/doc-claims/actions/workflows/ci.yml/badge.svg)](https://github.com/AYAN-2026/doc-claims/actions/workflows/ci.yml)

**Problem:** 你的 README 写着 "46 tests"、"5 workflows"。改了代码没人记得改文档，读的人被误导。单元测试拦不住这个——文档自己不会跑。

**doc-claims 把文档里的数字变成 CI 断言：** 每类数字登记成「正则模式 + 真值重算命令」，扫描活文档逐处与当场重算值比对，漂移即红。

零第三方依赖，真值来自任意 shell 命令（任何语言的项目都能接）。

## 30 秒上手

```bash
python doc_claims.py --init claims.json     # 扫描你的 md，自动生成配置初稿
# 把初稿里的 TODO 换成真值命令（如 pytest --collect-only -q | tail -1）
python doc_claims.py --config claims.json --strict
# ✓ docs/README.md:3 测试数量 写 46
# ✗ README.md:3 流程数 写 5，实际 7｜管理着 5 条流程……
# 结论：FAIL（exit 1 → CI 红）
```

## GitHub Action

```yaml
- uses: actions/checkout@v4
- uses: <you>/doc-claims@main
  with:
    config: claims.json
    strict: true
```

## 设计要点（与同类工具的差异）

| | doc-claims | [claims-check](https://github.com/cosmichackerx/claims-check) | [docverity](https://github.com/deveshagarwal/docverity) / [DocDrift](https://github.com/marketplace/actions/docdrift) |
|---|---|---|---|
| 核对对象 | 文档里的**任意整数声明**，模式可配 | test counts / versions / pinned tags | 文档 vs 代码整体漂移（LLM/启发式） |
| 真值来源 | **当场重算**（任意 shell 命令或字面量） | 内置探针 | 代码 diff 分析 |
| 豁免机制 | 整行豁免写在配置里（历史记录/旧文引用可审计） | 未提 | 未提 |
| 防静默绿 | `--strict`：0 处核对也判 FAIL（模式写错不会漏网） | 无 | 无 |
| 性能 | 真值按类型缓存，100 处命中只重算 1 次 | — | — |

三条原则：

1. **真值必须来自重算**，不来自另一份文档——文档对文档只会把漂移复制一遍
2. **豁免按整行、写在配置里**：可审计，不藏在代码里
3. **静默降级比红更危险**：`--strict` 专防"模式写错 → 0 处核对 → 静默绿"

这套机制在原生产系统里拦下过 8 处真实数字漂移（技能总数、仓库口径数）。

## 配置格式

```jsonc
{
  "files": ["*.md", "docs/**/*.md"],                // 待扫文件（glob）
  "exempt_patterns": ["历史记录", "引用原文"],        // 整行豁免
  "types": [
    { "name": "测试数量",
      "pattern": "(\\d+) 个测试",                    // 第一个捕获组必须是整数
      "truth": { "cmd": "pytest --collect-only -q | tail -1" } },  // 命令输出第一个整数
    { "name": "流程数",
      "pattern": "(\\d+) 条流程",
      "truth": { "literal": 5 } }                    // 也可以直接写字面量
  ]
}
```

demo 自带：`python doc_claims.py --config claims.json` 预期 PASS（3/3 一致，豁免 2 行生效）。

## License

MIT
