# BehaviorOS 全自动稳定化工具包

## 一句话说明

把 `run.ps1` 复制到小程序项目目录，双击执行，去喝茶。
回来看报告。

## 执行方式

```powershell
# 1. 把 run.ps1 复制到项目目录
Copy-Item run.ps1 D:\behavioral-health-project\coach-miniprogram\

# 2. 打开管理员PowerShell，进入目录
cd D:\behavioral-health-project\coach-miniprogram

# 3. 一键执行
.\run.ps1
```

## 它做什么

| Phase | 内容 | 自动? |
|-------|------|-------|
| P0 | 环境预检(分支/Docker/API/登录) | ✅ 全自动 |
| P1 | 端口统一(8002→8000)+编译脚本修复+.env创建 | ✅ 自动修复 |
| P2 | npm install + 编译(build→dev fallback) | ✅ 全自动 |
| P3 | API全量烟测(Coach 13端点+Grower 6端点+Public 3端点) | ✅ 全自动 |
| P4 | Coach目录重构(平铺→子目录) | ✅ 全自动 |
| P5 | BOS UI集成(从backup分支提取11个美化页面) | ✅ 全自动 |
| P6 | pages.json路由对齐 | ⚠️ 检测+报告 |
| P7 | 最终编译+每个页面静态分析(模拟点击) | ✅ 全自动 |
| P8 | 微信开发者工具自动打开(如CLI可用) | ⚠️ 尽力而为 |

## 输出

执行完成后在 `_auto-stabilize/` 目录下生成:

```
_auto-stabilize/
├── REPORT-20260301_2330.md   ← 综合报告(自动用记事本打开)
└── log-20260301_2330.txt     ← 完整执行日志
```

## 报告内容

- ✅/🔧/❌ 每个检查项的结果
- 自动修复了什么
- 还有什么问题没解决
- 需要手动做什么
- 下一步操作命令

## 参数

```powershell
.\run.ps1                     # 默认：全部执行
.\run.ps1 -SkipNpmInstall     # 跳过npm install(已装过)
.\run.ps1 -SkipUIIntegration  # 跳过BOS UI集成
.\run.ps1 -Verbose            # 详细输出
```

## 如果出问题

| 症状 | 解决 |
|------|------|
| "无法加载脚本" | `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| Docker连不上 | 先启动Docker Desktop |
| 编译超时 | 手动运行 `npx uni -p mp-weixin` 确认能编译 |
| 报告全红 | 把报告内容发给Claude，会帮你逐项解决 |
