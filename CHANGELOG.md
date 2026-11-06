# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循语义化版本。

## [1.1.5] - 2026-11-07

### 修复
- 模式捕获组抓到非整数（如量词"万级"）时裸 traceback 崩掉整个进程 → 显式 ✗（提示检查 pattern 是否把量词包进了捕获组）、跑完其余核对、exit 1。第三轮实战（doc-claims 核对 flow-router README）抓到

### 新增
- 2 例回归测试锁上述行为；claims-self.json 自证配置：README 三条活声明当场重算 3/3 一致

## [1.1.4] - 2026-11-07

### 新增
- 4 例真机缺陷回归测试：千分位数字（不崩 + 漂移可检出双面）、真值命令 UTF-8 输出（GBK locale 下不崩）、非法字节兜底（errors=replace 出数字而非崩）

## [1.1.3] - 2026-11-07

### 新增
- README 首屏双语化：英文 Problem + Quick view + 快速命令段，中文正文保留
- README 加"30 秒受益自检框"：3 条 yes/no，目标用户 30 秒内判断值不值得继续读
- `SECURITY.md`（安全策略：**本工具会执行 claims.json 里的 shell 命令**，把它当 build script 对待——这是唯一需要交代的攻击面）
- `CODE_OF_CONDUCT.md`（Contributor Covenant 2.1）

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
