# BehaviorOS V4.0 — pytest 测试套件

## 架构

```
tests/
├── conftest.py                  # 共享Fixtures (DB/工厂/Mock/常量)
├── pytest.ini                   # pytest 配置
├── run_tests.sh                 # 运行脚本
├── test_models.py               # 数据模型完整性 (7个测试类, 26个case)
├── test_stage_engine.py         # StageEngine 阶段引擎 (5个类, 18个case)
├── test_dual_track.py           # DualTrackEngine 双轨晋级 (5个类, 13个case)
├── test_anti_cheat.py           # AntiCheatEngine 防刷引擎 (6个类, 14个case)
├── test_safety_pipeline.py      # SafetyPipeline 安全管线 (7个类, 20个case)
├── test_incentive_engine.py     # 积分激励引擎 (6个类, 12个case)
├── test_agency_engine.py        # AgencyEngine 主体性 (5个类, 12个case)
├── test_trust_score.py          # TrustScoreService 信任分 (6个类, 12个case)
└── test_governance.py           # 治理体系 (5个类, 14个case)
```

## 统计

| 维度 | 数量 |
|------|------|
| 测试文件 | 9 |
| 测试类 | 52 |
| 测试用例 | **141** |
| 覆盖服务 | 8 (StageEngine / DualTrack / AntiCheat / Safety / Incentive / Agency / Trust / Governance) |
| 模型工厂 | 7 (User / Journey / DualTrack / AntiCheat / SafetyLog / Profile / Violation) |
| 角色Fixture | 7 (observer / grower / sharer / coach / promoter / master / admin) |
| Mock | 3 (mock_llm / mock_llm_unsafe / mock_llm_crisis) |

## 使用

```bash
# 放置到项目根目录
cp -r tests/ /path/to/behaviros-v4/

# 运行全部测试
cd /path/to/behaviros-v4
python -m pytest tests/ -v

# 只运行特定模块
python -m pytest tests/test_stage_engine.py -v
python -m pytest tests/test_safety_pipeline.py -v

# 按关键字筛选
python -m pytest tests/ -k "dual_track" -v
python -m pytest tests/ -k "anti_cheat and velocity" -v

# 带覆盖率
pip install pytest-cov
python -m pytest tests/ --cov=core --cov-report=term-missing

# 快速冒烟测试 (标记为 @pytest.mark.smoke 的用例)
python -m pytest tests/ -m smoke
```

## 设计原则

1. **宽容导入**: 模型/引擎缺失时 `pytest.mark.skip`，不阻塞其他测试
2. **事务回滚**: 每个测试独立DB会话，结束自动rollback
3. **内存数据库**: SQLite `:memory:` 零依赖运行
4. **工厂模式**: 7个Factory类封装所有测试数据创建
5. **条件断言**: 对引擎返回值先判空再断言，适配不同实现

## 对接后端

conftest.py 假设项目结构：
```
behaviros-v4/
├── core/
│   ├── models.py           # ORM 模型
│   ├── stage_engine.py     # StageEngine
│   ├── dual_track_engine.py
│   ├── anti_cheat_engine.py
│   ├── agency_engine.py
│   ├── trust_score_service.py
│   ├── incentive_phase_engine.py
│   ├── incentive_integration.py
│   ├── rule_registry.py
│   └── safety/
│       ├── pipeline.py
│       ├── input_filter.py
│       └── output_filter.py
├── api/
│   ├── main.py
│   └── dependencies.py
└── tests/                  ← 本套件
```

如果引擎方法签名不同，只需调整测试中的调用参数。
