# Claude Code 会话恢复指南

本指南介绍如何在 Claude Code 中恢复和管理会话上下文。

## 一、会话恢复命令

### 1. 恢复最近会话
```bash
# 继续最近的对话
claude --continue

# 或使用简写
claude -c
```

### 2. 恢复特定会话
```bash
# 使用 --resume 标志恢复
claude --resume

# 指定会话 ID 恢复
claude --resume <session-id>
```

### 3. 查看历史会话
```bash
# 列出历史会话
claude --history

# 限制显示数量
claude --history --limit 10
```

## 二、会话管理

### 1. 保存当前会话
会话会自动保存，存储位置：
- Windows: `C:\Users\<用户名>\.claude\projects\`
- macOS/Linux: `~/.claude/projects/`

### 2. 会话文件结构
```
~/.claude/
├── projects/
│   └── <project-path-hash>/
│       ├── <session-id>.jsonl      # 会话记录
│       └── ...
├── plans/
│   └── <plan-name>.md              # 计划文件
└── settings.json                    # 全局设置
```

### 3. 查看会话内容
```bash
# 查看特定会话的完整记录
cat ~/.claude/projects/<path>/<session-id>.jsonl
```

## 三、上下文压缩

当对话过长时，Claude Code 会自动进行上下文压缩：

1. **自动摘要**: 保留关键信息，压缩早期对话
2. **文件引用**: 保留文件路径引用而非完整内容
3. **任务状态**: 保留任务列表和完成状态

### 压缩后恢复
压缩后的会话仍可继续，Claude 会：
- 读取之前的摘要
- 重新读取需要的文件
- 继续未完成的任务

## 四、最佳实践

### 1. 使用任务列表
```
# 在对话中使用任务追踪
# Claude 会记住任务状态
```

### 2. 使用计划模式
计划文件会持久保存：
- 位置: `~/.claude/plans/<plan-name>.md`
- 恢复时自动加载相关计划

### 3. 提供明确的上下文
在新会话开始时，可以提供上下文：
```bash
claude "继续之前的工作，我们正在实现考试系统的防作弊功能"
```

### 4. 使用 Memory 功能
```bash
# 查看记忆
claude memory

# 添加记忆
claude memory add "项目使用 Vue 3 + TypeScript"
```

## 五、常见问题

### Q: 会话丢失怎么办？
A: 检查 `~/.claude/projects/` 目录，会话文件可能仍然存在。

### Q: 如何清理旧会话？
A:
```bash
# 清理特定项目的会话
rm -rf ~/.claude/projects/<path>/*.jsonl

# 或使用内置命令
claude clean --sessions
```

### Q: 会话恢复后上下文不完整？
A: 这是正常的，Claude 会根据需要重新读取文件。可以提供简短的上下文描述来帮助恢复。

## 六、项目特定上下文

本项目（行健行为教练）的关键上下文：

### 技术栈
- 前端: Vue 3 + TypeScript + Ant Design Vue 4 + Pinia
- 后端: Node.js + TypeORM + PostgreSQL
- 构建: Vite

### 关键目录
```
behavioral-health-project/
├── admin-portal/          # 管理后台 (Vue 3)
│   ├── src/
│   │   ├── views/exam/    # 考试相关页面
│   │   ├── composables/   # Vue composables
│   │   └── components/    # 组件
└── metabolic-core/        # 后端服务
    ├── src/
    │   ├── database/      # TypeORM 实体
    │   └── certification/ # 认证服务
```

### 已完成功能
- [x] 数据库持久化 (PostgreSQL + TypeORM)
- [x] 考试系统 (组卷、评分、成绩统计)
- [x] 防作弊机制 (切屏检测、全屏模式、抓拍)
- [x] 断点续考功能
- [x] 状态持久化 composables

### 恢复会话示例
```bash
claude --continue
# 或
claude "继续 behavioral-health-project 的开发，之前完成了防作弊功能"
```
