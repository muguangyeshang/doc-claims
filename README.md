# doc-claims

活文档数字核对器：README、手册、地图里写的数字（"共 2987 个技能"、"46 项检查"）
会随仓库演化漂移，没人记得改。测试拦不住文档——文档自己不会跑。

把每类数字登记成「正则模式 + 真值重算命令」，扫描活文档逐处与**当场重算值**比对，
漂移即红，退出码 1 可直接接 CI。

从一套生产系统的 `eval/doc_claims.py` 泛化而来（在那套系统里它拦下过 8 处数字漂移）。

## 用法

```bash
python doc_claims.py --config claims.json           # 退出码 0=全一致 1=有漂移
python doc_claims.py --config claims.json --strict  # 一处都没核到也判 FAIL（防模式写错静默通过）
```

要求：Python 3.8+，无第三方依赖。真值命令用什么 shell 就跑什么 shell，任意语言的项目都能接。

## 配置格式

```jsonc
{
  "files": ["docs/*.md", "README.md"],              // 待扫文件（glob）
  "exempt_patterns": ["历史记录", "引用原文"],        // 整行豁免：历史/旧文引用不算活声明
  "types": [
    {
      "name": "技能总数",
      "pattern": "(\\d+) 个技能",                    // 第一个捕获组必须是整数
      "truth": { "cmd": "python count_skills.py" }  // 真值：命令输出里的第一个整数
    },
    {
      "name": "流程数",
      "pattern": "(\\d+) 条流程",
      "truth": { "literal": 5 }                     // 真值也可以直接写字面量
    }
  ]
}
```

## 判定输出

```
  ✓ docs/README.md:3 技能总数 写 12
  ✗ docs/README.md:3 技能总数 写 13，实际 12｜本仓库管着 13 个技能……
------------------------------------------------------------
  核对 3 处 · 一致 2 · 不一致 1 · 豁免模式 2 个
  结论：FAIL
```

## 设计要点

- **真值必须来自重算**，不来自另一份文档——文档对文档只会把漂移复制一遍
- **豁免按整行、写在配置里**：可审计，不藏在代码里
- **真值结果按类型缓存**：一处类型 100 处命中只重算一次
- `--strict` 防"模式写错 → 0 处核对 → 静默绿"：静默降级比红更危险

## demo

```bash
python doc_claims.py --config claims.json   # example/ 下自带，预期 PASS（3/3 一致）
```

## License

MIT
