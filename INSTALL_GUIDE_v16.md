# v16 增量文件 - Claude Code 安装指南

## 文件对应关系

| 序号 | 文件名 | 目标路径 | 说明 |
|------|--------|----------|------|
| 01 | `01_rules_definition.py` | `services/logic_engine/schema/rules_definition.py` | Pydantic Schema |
| 02 | `02_behavior_engine.py` | `services/logic_engine/behavior_engine.py` | 逻辑引擎 |
| 03 | `03_state_sync_manager.py` | `services/state_sync/manager.py` | 状态同步 |
| 04 | `04_behavior_rules.json` | `configs/behavior/behavior_rules.json` | 母库配置 |
| 05 | `05_ActionRenderer.js` | `frontend/components/ActionRenderer.js` | 前端组件 |
| 06 | `06_admin_routes.py` | `api/v14/admin_routes.py` | Admin API |
| 07 | `07_CHANGELOG_v16.md` | `CHANGELOG_v16.md` | 变更日志 |

## Claude Code 执行命令

```bash
# 1. 创建目录结构
mkdir -p services/logic_engine/schema
mkdir -p services/state_sync
mkdir -p configs/behavior
mkdir -p frontend/components
mkdir -p api/v14

# 2. 移动文件到正确位置（去掉序号前缀）
mv 01_rules_definition.py services/logic_engine/schema/rules_definition.py
mv 02_behavior_engine.py services/logic_engine/behavior_engine.py
mv 03_state_sync_manager.py services/state_sync/manager.py
mv 04_behavior_rules.json configs/behavior/behavior_rules.json
mv 05_ActionRenderer.js frontend/components/ActionRenderer.js
mv 06_admin_routes.py api/v14/admin_routes.py
mv 07_CHANGELOG_v16.md CHANGELOG_v16.md

# 3. 创建 __init__.py 文件
echo '"""Services Module"""' > services/__init__.py

cat > services/logic_engine/__init__.py << 'EOF'
from services.logic_engine.behavior_engine import (
    BehaviorEngine, get_behavior_engine, start_config_watcher
)
from services.logic_engine.schema.rules_definition import (
    BehaviorLibrary, TriggerRule, ActionPackage
)
EOF

echo 'from services.logic_engine.schema.rules_definition import *' > services/logic_engine/schema/__init__.py

cat > services/state_sync/__init__.py << 'EOF'
from services.state_sync.manager import (
    StateSyncManager, get_state_sync_manager, EventType, ViewRole
)
EOF

# 4. 在 api/v14/routes.py 末尾添加（如果文件存在）
cat >> api/v14/routes.py << 'EOF'

# [v16-NEW] Admin行为配置路由
try:
    from api.v14.admin_routes import router as admin_router
    router.include_router(admin_router)
except ImportError:
    pass
EOF
```

## 验证安装

```bash
# 启动服务后测试
curl http://localhost:8002/api/v2/admin/behavior/rules
curl http://localhost:8002/api/v2/admin/behavior/stats
```
