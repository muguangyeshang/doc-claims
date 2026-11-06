# 贡献指南

## 开发环境

Python 3.8+，无第三方依赖。克隆即用：

```bash
git clone <repo-url> && cd doc-claims
python -m unittest discover tests -v      # 全部测试
python doc_claims.py --config claims.json  # demo 应 PASS
```

## 提交前必须全绿

| 命令 | 判据 |
|---|---|
| `python -m unittest discover tests` | 全部通过（含端到端退出码用例） |
| `python doc_claims.py --config claims.json` | 结论：PASS，退出码 0 |

## 改动规范

1. **改核对逻辑必加端到端用例**。`tests/test_doc_claims.py` 走子进程测真实退出码——这个工具的核心契约就是退出码（0=一致 1=漂移），mock 掉退出码的测试等于没测。
2. **静默降级比红更危险**：任何新加的"跳过/豁免/降级"路径必须（a）往 stdout 打印被跳过了什么，（b）在测试里锁住"跳过是显式的"。这是本工具存在的理由。
3. **真值必须来自重算**：不接受"从另一份文档读真值"类 feature——文档对文档只会把漂移复制一遍。
4. **纯标准库红线**：runtime（`doc_claims.py`）不引入第三方依赖；测试用 unittest 不用 pytest。
5. **豁免只走配置**：豁免模式加进 `exempt_patterns`（可审计），不在代码里硬编码豁免词。
6. **注释写"为什么"**：沿用仓库习惯，关键行注释来自真实踩坑记录。

## 提交信息

中文一句话讲清"做了什么、为什么"，格式参考 git log。

## 不接受的方向

- 内置更多语言/框架探针：探针归 `--init` 的候选表，核心引擎保持通用（任意 shell 命令都能当真值源），不做硬编码特判。
