"""
行为健康数字平台 - LLM Judge 评判执行器
LLM Judge Executor

[v14-NEW] 质量审计模块

特点：
- 异步处理
- 正则清洗防止LLM输出垃圾字符
- 支持多种LLM后端（Dify、Ollama）
- 与v14功能开关集成
"""
import json
import re
import os
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from loguru import logger

from quality.schema import (
    QualityAuditResult, 
    QualityScore, 
    AuditGrade,
    AuditRequest,
    determine_grade
)
from quality.judge_prompt import build_judge_prompt


class LLMJudge:
    """
    LLM 质量评判器
    
    支持多种后端：
    - Ollama (本地)
    - Dify (平台)
    """
    
    def __init__(
        self, 
        llm_client: Optional[Any] = None,
        model_name: str = "qwen2.5:0.5b",
        backend: str = "ollama"
    ):
        """
        初始化评判器
        
        Args:
            llm_client: LLM客户端实例（可选，会自动创建）
            model_name: 模型名称
            backend: 后端类型 (ollama/dify)
        """
        self.llm_client = llm_client
        self.model_name = model_name
        self.backend = backend
        
        # Ollama配置
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        logger.info(f"[Quality] LLMJudge 初始化: backend={backend}, model={model_name}")
    
    async def evaluate(
        self, 
        snapshot_data: Dict[str, Any], 
        response_text: str, 
        trace_id: str,
        user_id: Optional[int] = None
    ) -> QualityAuditResult:
        """
        执行质量评估
        
        Args:
            snapshot_data: 快照数据（包含ttm_stage, trigger_tags等）
            response_text: 待评估的AI响应
            trace_id: 追踪ID
            user_id: 用户ID（可选）
        
        Returns:
            QualityAuditResult: 审计结果
        """
        # 构建Prompt
        prompt = build_judge_prompt(snapshot_data, response_text)
        
        try:
            # 调用LLM
            raw_output = await self._call_llm(prompt)
            
            # 解析结果
            data = self._parse_llm_output(raw_output)
            
            # 构建评分
            scores = QualityScore(
                adherence=self._safe_int(data.get("adherence"), 0, 5),
                safety=self._safe_int(data.get("safety"), 0, 5),
                empathy=self._safe_int(data.get("empathy"), 0, 5),
                consistency=self._safe_int(data.get("consistency"), 0, 5)
            )
            
            # 确定最终等级
            final_grade = determine_grade(scores)
            
            # [v14-NEW] 收集v14上下文
            v14_context = None
            if snapshot_data.get("rhythm_phase") or snapshot_data.get("trigger_events"):
                v14_context = {
                    "rhythm_phase": snapshot_data.get("rhythm_phase"),
                    "trigger_events": snapshot_data.get("trigger_events")
                }
            
            result = QualityAuditResult(
                snapshot_id=snapshot_data.get("snapshot_id", f"snap_{trace_id}"),
                trace_id=trace_id,
                user_id=user_id,
                scores=scores,
                violations=data.get("violations", []),
                reasoning=data.get("reasoning", "No reasoning provided"),
                judge_model=self.model_name,
                final_grade=final_grade,
                v14_context=v14_context
            )
            
            logger.info(f"[Quality] 审计完成: trace={trace_id} grade={final_grade.value} "
                       f"scores={scores.total}/20")
            
            return result
            
        except Exception as e:
            logger.error(f"[Quality] 审计失败: trace={trace_id} error={e}")
            
            # 返回失败结果
            return QualityAuditResult(
                snapshot_id=snapshot_data.get("snapshot_id", f"snap_{trace_id}"),
                trace_id=trace_id,
                user_id=user_id,
                scores=QualityScore(adherence=0, safety=0, empathy=0, consistency=0),
                violations=["系统错误：审计过程异常"],
                reasoning=f"评估失败: {str(e)}",
                judge_model=self.model_name,
                final_grade=AuditGrade.REVIEW
            )
    
    async def evaluate_from_request(self, request: AuditRequest) -> QualityAuditResult:
        """
        从AuditRequest执行评估
        
        Args:
            request: 审计请求对象
        
        Returns:
            QualityAuditResult: 审计结果
        """
        snapshot_data = {
            "snapshot_id": request.snapshot_id or f"snap_{request.trace_id}",
            "ttm_stage": request.ttm_stage,
            "trigger_tags": request.trigger_tags or [],
            "agent_role": request.agent_role or "health_coach",
            "rhythm_phase": request.rhythm_phase,
            "trigger_events": request.trigger_events
        }
        
        return await self.evaluate(
            snapshot_data=snapshot_data,
            response_text=request.response_text,
            trace_id=request.trace_id,
            user_id=request.user_id
        )
    
    async def _call_llm(self, prompt: str) -> str:
        """
        调用LLM获取响应
        
        支持多种后端
        """
        if self.backend == "ollama":
            return await self._call_ollama(prompt)
        elif self.backend == "dify":
            return await self._call_dify(prompt)
        elif self.llm_client:
            # 使用传入的客户端
            return await self._call_custom_client(prompt)
        else:
            raise ValueError(f"不支持的后端: {self.backend}")
    
    async def _call_ollama(self, prompt: str) -> str:
        """调用Ollama"""
        import httpx
        
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
            resp = await client.post(
                f"{self.ollama_base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # 低温度保证一致性
                        "num_predict": 500
                    }
                }
            )
            resp.raise_for_status()
            result = resp.json()
            return result.get("response", "")
    
    async def _call_dify(self, prompt: str) -> str:
        """调用Dify"""
        # 如果有Dify客户端
        if self.llm_client and hasattr(self.llm_client, 'generate_intervention'):
            response = await self.llm_client.generate_intervention(
                user_input=prompt,
                user_id="quality_judge",
                context_data={"mode": "quality_audit"}
            )
            return response.get("answer", "")
        
        # 否则使用HTTP直接调用
        import httpx
        
        dify_base = os.getenv("DIFY_BASE_URL", "http://localhost:8080/v1")
        dify_key = os.getenv("DIFY_API_KEY", "")
        
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
            resp = await client.post(
                f"{dify_base}/chat-messages",
                headers={"Authorization": f"Bearer {dify_key}"},
                json={
                    "inputs": {},
                    "query": prompt,
                    "response_mode": "blocking",
                    "user": "quality_judge"
                }
            )
            resp.raise_for_status()
            result = resp.json()
            return result.get("answer", "")
    
    async def _call_custom_client(self, prompt: str) -> str:
        """调用自定义客户端"""
        if hasattr(self.llm_client, 'acreate'):
            return await self.llm_client.acreate(prompt)
        elif hasattr(self.llm_client, 'generate'):
            return self.llm_client.generate(prompt)
        else:
            raise ValueError("自定义LLM客户端必须有 acreate 或 generate 方法")
    
    def _parse_llm_output(self, raw_output: str) -> Dict[str, Any]:
        """
        解析LLM输出
        
        使用正则提取JSON，防止模型输出Markdown代码块等垃圾字符
        """
        if not raw_output:
            return {}
        
        # 尝试直接解析
        try:
            return json.loads(raw_output.strip())
        except json.JSONDecodeError:
            pass
        
        # 正则提取JSON内容
        # 匹配 {...} 包括嵌套
        json_patterns = [
            r'\{[^{}]*\}',  # 简单JSON
            r'\{(?:[^{}]|\{[^{}]*\})*\}',  # 一层嵌套
            r'```json\s*(\{.*?\})\s*```',  # Markdown代码块
            r'```\s*(\{.*?\})\s*```',  # 无语言标记的代码块
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, raw_output, re.DOTALL)
            for match in matches:
                try:
                    # 如果是元组（捕获组），取第一个
                    json_str = match[0] if isinstance(match, tuple) else match
                    return json.loads(json_str)
                except (json.JSONDecodeError, IndexError):
                    continue
        
        logger.warning(f"[Quality] 无法解析LLM输出: {raw_output[:200]}...")
        return {}
    
    def _safe_int(self, value: Any, min_val: int, max_val: int) -> int:
        """安全转换为整数，并限制范围"""
        try:
            v = int(value) if value is not None else 0
            return max(min_val, min(max_val, v))
        except (ValueError, TypeError):
            return min_val


# ============================================
# 批量审计器
# ============================================

class BatchLLMJudge:
    """批量审计器"""
    
    def __init__(self, judge: LLMJudge, concurrency: int = 3):
        """
        Args:
            judge: LLMJudge实例
            concurrency: 并发数
        """
        self.judge = judge
        self.concurrency = concurrency
        self.semaphore = asyncio.Semaphore(concurrency)
    
    async def evaluate_batch(
        self, 
        requests: List[AuditRequest]
    ) -> List[QualityAuditResult]:
        """
        批量执行审计
        
        Args:
            requests: 审计请求列表
        
        Returns:
            审计结果列表
        """
        async def _eval_with_semaphore(req: AuditRequest) -> QualityAuditResult:
            async with self.semaphore:
                return await self.judge.evaluate_from_request(req)
        
        tasks = [_eval_with_semaphore(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"[Quality] 批量审计异常: index={i} error={result}")
                # 创建错误结果
                req = requests[i]
                final_results.append(QualityAuditResult(
                    snapshot_id=req.snapshot_id or f"snap_{req.trace_id}",
                    trace_id=req.trace_id,
                    scores=QualityScore(adherence=0, safety=0, empathy=0, consistency=0),
                    violations=["批量审计异常"],
                    reasoning=str(result),
                    judge_model=self.judge.model_name,
                    final_grade=AuditGrade.REVIEW
                ))
            else:
                final_results.append(result)
        
        return final_results


# ============================================
# 工厂函数
# ============================================

_default_judge: Optional[LLMJudge] = None


def get_llm_judge(
    model_name: Optional[str] = None,
    backend: Optional[str] = None
) -> LLMJudge:
    """
    获取LLMJudge单例
    
    Args:
        model_name: 模型名称（可选）
        backend: 后端类型（可选）
    
    Returns:
        LLMJudge实例
    """
    global _default_judge
    
    # 检查v14功能开关
    try:
        from core.v14 import is_feature_enabled
        if not is_feature_enabled("ENABLE_QUALITY_AUDIT"):
            logger.debug("[Quality] 质量审计未启用")
            # 仍然返回实例，但调用时会有日志
    except ImportError:
        pass
    
    if _default_judge is None:
        _default_judge = LLMJudge(
            model_name=model_name or os.getenv("QUALITY_JUDGE_MODEL", "qwen2.5:0.5b"),
            backend=backend or os.getenv("QUALITY_JUDGE_BACKEND", "ollama")
        )
    
    return _default_judge
