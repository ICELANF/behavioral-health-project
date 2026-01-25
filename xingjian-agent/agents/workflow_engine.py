import enum
from typing import List, Dict, Any

# 1. 定义状态枚举
class OctopusState(enum.Enum):
    AUDIT = "audit"           # 判断：分析数据与意图
    SELECT = "select"         # 选择：路由专家
    DECOMPOSE = "decompose"   # 分解：拆解原子任务
    CONSTRAINT = "constraint" # 限幅：根据效能感裁剪
    ACTION = "action"         # 行动：生成最终指令
    FEEDBACK = "feedback"     # 反馈：记录用户完成情况

# 2. 状态机引擎
class OctopusWorkflowEngine:
    def __init__(self, user_id: str, efficacy_score: int):
        self.user_id = user_id
        self.efficacy_score = efficacy_score
        self.current_state = OctopusState.AUDIT
        self.context = {}

    def run_workflow(self, user_input: str, wearable_data: Dict = None):
        """执行全链路流水线"""
        
        # [判断阶段] Audit
        self.context['raw_input'] = user_input
        self.context['wearable'] = wearable_data
        # 逻辑：如果心率过高，自动降低效能权重
        if wearable_data and wearable_data.get('hr', 0) > 100:
            self.efficacy_score = max(0, self.efficacy_score - 20)
        self.current_state = OctopusState.SELECT

        # [选择阶段] Select (模拟路由)
        # 这里未来对接你的 IntentRouter
        self.context['selected_experts'] = ["mental_health"] 
        self.current_state = OctopusState.DECOMPOSE

        # [分解阶段] Decompose (模拟 Agent 生成)
        # 这里未来对接 LLM 的输出
        raw_tasks = [
            {"id": 1, "content": "深度冥想20分钟", "difficulty": 4, "type": "mental"},
            {"id": 2, "content": "记录一次情绪日志", "difficulty": 2, "type": "mental"},
            {"id": 3, "content": "进行3次深呼吸", "difficulty": 1, "type": "mental"}
        ]
        self.context['raw_tasks'] = raw_tasks
        self.current_state = OctopusState.CONSTRAINT

        # [限幅阶段] Constraint (集成你截图中的逻辑)
        self.context['clamped_tasks'] = self._octopus_clamping(raw_tasks)
        self.current_state = OctopusState.ACTION

        # [行动阶段] Action
        return self._generate_response()

    def _octopus_clamping(self, tasks: List[Dict]) -> List[Dict]:
        """执行限幅算法"""
        score = self.efficacy_score
        if score < 20:
            return [t for t in tasks if t['difficulty'] == 1][:1]
        elif score < 50:
            return [t for t in tasks if t['difficulty'] <= 2][:2]
        else:
            return tasks

    def _generate_response(self) -> Dict:
        """生成最终的业务指令流"""
        return {
            "status": "success",
            "current_state": self.current_state.value,
            "efficacy_score": self.efficacy_score,
            "tasks": self.context['clamped_tasks'],
            "external_hooks": {
                "show_video": True if self.efficacy_score < 30 else False,
                "clinical_alert": True if self.efficacy_score < 10 else False
            }
        }

# 本地测试
if __name__ == "__main__":
    # 模拟一个焦虑（效能低）且心率快的用户
    engine = OctopusWorkflowEngine(user_id="test_001", efficacy_score=15)
    result = engine.run_workflow("我很烦躁", wearable_data={"hr": 110})
    print(f"限幅后的任务: {result['tasks']}")