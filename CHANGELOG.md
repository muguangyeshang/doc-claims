# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循语义化版本。

## [1.1.1] - 2026-11-07

### 新增
- `.github/workflows/ci.yml`：demo PASS / --init 可生成 / **漂移必须红**（故意改错文档数字断言 exit 1），Python 3.8 + 3.12 矩阵
- `tests/`：unittest 正式测试（端到端退出码、豁免、--strict、真值命令、缺配置引导）
- `docs/DESIGN.md`、`CONTRIBUTING.md`

## [1.1.0] - 2026-11-06

### 新增
- GitHub Action：`action.yml`（composite action，`config` / `strict` 两个 input），发布 Marketplace 后可用 `uses: <you>/doc-claims@v1.0.0`
- `--init` 脚手架：扫描仓库 md，按常见数字声明场景（测试数/文档数/模块数/版本号）生成 claims.json 初稿
- `--config` 缺文件时改为给"跑 --init"的引导

### 变更
- README 重写：30 秒上手、Action 配置、与 claims-check / docverity / DocDrift 五维对比表

## [1.0.0] - 2026-11-06

### 首个版本
- 文档数字声明核对：正则模式 + 真值重算（shell 命令输出第一个整数 / 字面量）
- 整行豁免（写在配置里可审计）
- 真值按类型缓存（100 处命中只重算 1 次）
- `--strict` 防"模式写错 → 0 处核对 → 静默绿"
- 纯标准库零依赖；从生产系统 eval/doc_claims.py 泛化（拦下过 8 处真实数字漂移）
