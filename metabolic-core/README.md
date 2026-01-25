# 行为健康决策操作系统内核 · Metabolic Core v1.1

> 行健行为教练 - 代谢慢病行为健康中枢内核

本系统为：
以评估为入口的【代谢慢病 × 行为健康 × 教练训练】决策操作系统内核。

## 核心能力

- **多设备信号标准化**：CGM / BP / HRV / Scale / Watch
- **连续轨迹建模**：代谢 × 行为 × 干预 × 阶段迁移
- **表型识别**：基于信号模式的行为表型匹配
- **行为阶段引擎**：TTM/五层次心理准备度判定
- **干预处方自动组合**：个性化干预方案生成
- **教练训练与病例回放系统**：教练能力提升平台

## 核心原则

```
评估 → 轨迹 → 表型 → 阶段 → 干预 → 行为改变 → 轨迹沉淀
```

## 架构层次

| 层级 | 模块 | 功能 |
|------|------|------|
| Signal | SignalSchema, SignalNormalizationService | 设备数据标准化 |
| Trajectory | TrajectorySchema, TrajectoryService | 生命线轨迹建模 |
| Libraries | 7大知识库 | 表型/干预/行为/内容/商业/教练/评估 |
| Registry | KnowledgeRegistry, LibraryManager | 知识库注册与版本管理 |
| Orchestrator | Orchestrator, InterventionPlanner | 主链编排与干预规划 |
| API | REST Endpoints | 外部接口 |

## 快速开始

```bash
# 安装依赖
npm install

# 开发模式
npm run dev

# 构建
npm run build

# 运行
npm start
```

## API 端点

- `POST /phenotype/match` - 表型匹配
- `POST /intervention/plan` - 干预规划
- `POST /coach/train` - 教练训练评估
- `GET /registry/libraries` - 知识库列表

## 与行健行为教练系统集成

本模块作为行健行为教练系统的核心决策引擎，与以下模块协作：
- BAPS行为评估系统 (端口8001)
- Master Agent中枢 (core/master_agent.py)
- 八爪鱼效能引擎 (OctopusClampingEngine)

---

*行健行为教练 · Metabolic Core v1.1*
