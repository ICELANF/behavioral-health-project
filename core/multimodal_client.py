"""
多模态系统客户端
Multimodal System Client

集成多模态处理系统API，提供文本、信号、融合评估功能
"""
import httpx
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from loguru import logger


@dataclass
class MultimodalConfig:
    """多模态系统配置"""
    base_url: str = "http://localhost:8090"
    api_prefix: str = "/api/v1"
    timeout: float = 30.0
    max_retries: int = 3


class MultimodalClient:
    """
    多模态系统客户端

    功能：
    - 文本情感与风险分析
    - 生理信号处理
    - 多模态融合评估
    """

    def __init__(self, config: Optional[MultimodalConfig] = None):
        self.config = config or MultimodalConfig()
        self.base_url = f"{self.config.base_url}{self.config.api_prefix}"
        self.client = httpx.AsyncClient(timeout=self.config.timeout)
        logger.info(f"多模态客户端初始化: {self.base_url}")

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            url = f"{self.config.base_url}/health"
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"多模态系统健康检查失败: {e}")
            return {"status": "unhealthy", "error": str(e)}

    # ============================================
    # 文本处理
    # ============================================

    async def process_text(
        self,
        content: str,
        user_id: int = 0,
        text_type: str = "general"
    ) -> Dict[str, Any]:
        """
        处理文本数据

        Args:
            content: 文本内容
            user_id: 用户ID
            text_type: 文本类型

        Returns:
            {
                "sentiment": "positive/negative/neutral",
                "sentiment_score": float,
                "primary_emotion": str,
                "emotions": dict,
                "keywords": list,
                "risk_signals": list,
                "risk_score": float
            }
        """
        try:
            url = f"{self.base_url}/text/process"
            payload = {
                "user_id": user_id,
                "content": content,
                "text_type": text_type
            }
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()

            if result.get("code") == 0:
                return result.get("data", {})
            else:
                logger.error(f"文本处理失败: {result.get('message')}")
                return {}

        except Exception as e:
            logger.error(f"文本处理异常: {e}")
            return {}

    # ============================================
    # 信号处理
    # ============================================

    async def process_signal(
        self,
        signal_type: str,
        values: List[float],
        user_id: int = 0,
        sample_rate: float = 1.0,
        device_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        处理生理信号

        Args:
            signal_type: 信号类型 (ppg/hr, cgm/glucose, acc, eda)
            values: 信号值数组
            user_id: 用户ID
            sample_rate: 采样率 (Hz)
            device_id: 设备ID

        Returns:
            {
                "signal_type": str,
                "heart_rate": float,  # 心率时返回
                "hrv_sdnn": float,    # HRV指标
                "anomalies": list     # 异常检测
            }
        """
        try:
            url = f"{self.base_url}/signal/process"
            payload = {
                "user_id": user_id,
                "signal_type": signal_type,
                "values": values,
                "sample_rate": sample_rate,
                "device_id": device_id
            }
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()

            if result.get("code") == 0:
                return result.get("data", {})
            else:
                logger.error(f"信号处理失败: {result.get('message')}")
                return {}

        except Exception as e:
            logger.error(f"信号处理异常: {e}")
            return {}

    async def process_heartrate(
        self,
        values: List[float],
        user_id: int = 0
    ) -> Dict[str, Any]:
        """便捷方法：处理心率数据"""
        return await self.process_signal("ppg", values, user_id)

    async def process_glucose(
        self,
        values: List[float],
        user_id: int = 0
    ) -> Dict[str, Any]:
        """便捷方法：处理血糖数据"""
        return await self.process_signal("cgm", values, user_id)

    # ============================================
    # 融合评估
    # ============================================

    async def fuse_meal_assessment(
        self,
        user_id: int,
        text_content: Optional[str] = None,
        glucose_before: Optional[float] = None,
        glucose_after: Optional[float] = None,
        meal_type: str = "unknown"
    ) -> Dict[str, Any]:
        """
        饮食融合评估

        Args:
            user_id: 用户ID
            text_content: 饮食描述文本
            glucose_before: 餐前血糖
            glucose_after: 餐后血糖
            meal_type: 餐次类型 (breakfast/lunch/dinner/snack)

        Returns:
            {
                "overall_score": float,    # 总评分 0-10
                "nutrition_score": float,  # 营养评分
                "glucose_response": str,   # 血糖响应
                "risk_level": str,         # 风险等级
                "recommendations": list    # 建议列表
            }
        """
        try:
            url = f"{self.base_url}/fusion/meal"
            payload = {
                "user_id": user_id,
                "text_content": text_content,
                "glucose_before": glucose_before,
                "glucose_after": glucose_after,
                "meal_type": meal_type
            }
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()

            if result.get("code") == 0:
                return result.get("data", {})
            else:
                logger.error(f"饮食融合评估失败: {result.get('message')}")
                return {}

        except Exception as e:
            logger.error(f"饮食融合评估异常: {e}")
            return {}

    async def fuse_emotion_assessment(
        self,
        user_id: int,
        text_content: Optional[str] = None,
        hrv_values: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        情绪融合评估

        Args:
            user_id: 用户ID
            text_content: 情绪描述文本
            hrv_values: HRV数据

        Returns:
            {
                "overall_emotion": str,    # 综合情绪
                "stress_level": str,       # 压力水平
                "risk_level": str,         # 风险等级
                "recommendations": list    # 建议列表
            }
        """
        try:
            url = f"{self.base_url}/fusion/emotion"
            payload = {
                "user_id": user_id,
                "text_content": text_content,
                "hrv_values": hrv_values
            }
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()

            if result.get("code") == 0:
                return result.get("data", {})
            else:
                logger.error(f"情绪融合评估失败: {result.get('message')}")
                return {}

        except Exception as e:
            logger.error(f"情绪融合评估异常: {e}")
            return {}

    # ============================================
    # 批量处理
    # ============================================

    async def batch_process(
        self,
        user_id: int,
        text_content: Optional[str] = None,
        hrv_values: Optional[List[float]] = None,
        glucose_values: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        批量处理多种数据

        一次性处理文本、心率、血糖数据，返回综合结果
        """
        results = {}

        # 文本处理
        if text_content:
            text_result = await self.process_text(text_content, user_id)
            results["text"] = text_result

        # 心率处理
        if hrv_values:
            hrv_result = await self.process_heartrate(hrv_values, user_id)
            results["hrv"] = hrv_result

        # 血糖处理
        if glucose_values:
            glucose_result = await self.process_glucose(glucose_values, user_id)
            results["glucose"] = glucose_result

        return results

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()


# ============================================
# 全局单例
# ============================================

_multimodal_client: Optional[MultimodalClient] = None


def get_multimodal_client() -> MultimodalClient:
    """获取多模态客户端单例"""
    global _multimodal_client
    if _multimodal_client is None:
        _multimodal_client = MultimodalClient()
    return _multimodal_client


async def close_multimodal_client():
    """关闭多模态客户端"""
    global _multimodal_client
    if _multimodal_client:
        await _multimodal_client.close()
        _multimodal_client = None
