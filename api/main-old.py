# -*- coding: utf-8 -*-
import sys
import os
import json
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# 1. 路径注入：确保识别项目根目录
ROOT_DIR = r"D:\behavioral-health-project"
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# 2. 专家协调器：从 experts.json 动态加载配置
class AgentOrchestrator:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.registry = {}
        self.load_experts()

    def load_experts(self):
        """从 JSON 文件加载专家库，显式使用 UTF-8 编码"""
        try:
            if not os.path.exists(self.config_path):
                print(f"❌ [ERROR] 找不到配置文件: {self.config_path}")
                return
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.registry = json.load(f)
            print(f"🚀 [OK] 成功从文件加载专家: {list(self.registry.keys())}")
        except Exception as e:
            print(f"❌ [ERROR] 加载专家库失败: {e}")

    async def process_query(self, message: str):
        """模拟 Qwen2.5 14B 模型处理逻辑"""
        # 验证专家是否存在
        expert = self.registry.get("xingjian_coach", {})
        expert_name = expert.get("name", "行健教练")

        # 构建符合行为科学的回复结构
        return {
            "status": "success",
            "expert": expert_name,
            "final_response": (
                f"【{expert_name} - 程序员颈椎康复处方】\n"
                "针对您的酸痛，基于行为科学建议如下：\n"
                "1. 物理动作：执行麦肯基伸展法。缓慢后仰头至极限保持2秒，重复10次。\n"
                "2. 行为诱导：在显示器顶端贴一个绿点。看到绿点即执行一次收下颌动作。\n"
                "3. 生物力学：此方案旨在通过反向位移抵消长期低头对椎间盘的静力负荷。"
            )
        }

# 3. 初始化全局协调器
experts_json_path = os.path.join(ROOT_DIR, "experts.json")
orchestrator = AgentOrchestrator(experts_json_path)

# 4. 生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "=" * 60)
    print("  行健行为教练 [工程化配置版] 启动中...")
    print(f"  配置文件: {experts_json_path}")
    print("=" * 60)
    yield
    print("\n[INFO] 服务安全关闭")

# 5. FastAPI 应用配置
app = FastAPI(title="行健行为教练 API", lifespan=lifespan)

from core.middleware import get_cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/v1/chat")
async def chat_endpoint(message: str = Body(..., embed=True)):
    try:
        # 核心修复：显式 await 异步协程，并返回字典格式
        response_data = await orchestrator.process_query(message)
        return response_data
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"处理请求时发生错误: {str(e)}"}
        )

@app.get("/health")
async def health_check():
    return {"status": "healthy", "experts": list(orchestrator.registry.keys())}

if __name__ == "__main__":
    import uvicorn
    # 强制在 127.0.0.1 启动，确保 test 脚本能连上
    uvicorn.run(app, host="127.0.0.1", port=8000)