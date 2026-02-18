"""
R8: user_context — 跨Session记忆 (让Agent"记得你")

功能:
  1. user_context 表: 存储Agent从对话中提取的用户上下文
  2. 上下文提取器: 从对话历史中自动提取关键信息
  3. Agent取用接口: Agent处理请求前先加载用户上下文
  4. 上下文管理API: 查看/更新/删除上下文条目

数据模型:
  user_contexts 表:
    - user_id: 用户ID
    - category: 类别 (health|preference|social|emotion|goal|history)
    - key: 键 (如 "blood_sugar_target", "favorite_exercise")
    - value: 值
    - source_agent: 提取此信息的Agent ID
    - confidence: 置信度 (0-1)
    - extracted_at: 提取时间
    - expires_at: 过期时间 (可选)

部署:
  1. 执行 SQL 创建 user_contexts 表
  2. 复制到 api/ 目录
  3. 在 Agent 处理链中调用 load_user_context()
"""

import logging
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db as get_db
from api.dependencies import get_current_user

logger = logging.getLogger("user_context")

router = APIRouter(prefix="/api/v1", tags=["user-context"])


# ═══════════════════════════════════════════════════
# 数据库迁移 SQL (追加到 V5_0_flywheel_tables.sql)
# ═══════════════════════════════════════════════════
MIGRATION_SQL = """
-- R8: 用户上下文记忆表
CREATE TABLE IF NOT EXISTS user_contexts (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category        VARCHAR(30) NOT NULL,   -- health|preference|social|emotion|goal|history
    key             VARCHAR(100) NOT NULL,
    value           TEXT NOT NULL,
    source_agent    VARCHAR(50),            -- 提取此信息的Agent ID
    confidence      FLOAT DEFAULT 0.8,
    extracted_at    TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at      TIMESTAMP,              -- NULL = 永不过期
    
    UNIQUE(user_id, category, key)          -- 同一用户同一类别同一键 只存一条
);

CREATE INDEX IF NOT EXISTS idx_uctx_user_cat 
    ON user_contexts(user_id, category);
CREATE INDEX IF NOT EXISTS idx_uctx_expires 
    ON user_contexts(expires_at) WHERE expires_at IS NOT NULL;

COMMENT ON TABLE user_contexts IS 'Agent跨Session用户记忆 — 让AI记得上周的事';

-- 通知表 (R7 依赖)
CREATE TABLE IF NOT EXISTS notifications (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title           VARCHAR(200),
    body            TEXT,
    type            VARCHAR(50),
    priority        VARCHAR(20) DEFAULT 'normal',
    is_read         BOOLEAN DEFAULT false,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notif_user_unread 
    ON notifications(user_id, is_read, created_at DESC);

COMMENT ON TABLE notifications IS '用户通知 — R7主动触达';
"""


# ═══════════════════════════════════════════════════
# Schema
# ═══════════════════════════════════════════════════

class ContextEntry(BaseModel):
    category: str
    key: str
    value: str
    source_agent: Optional[str] = None
    confidence: float = 0.8
    extracted_at: Optional[str] = None


class ContextResponse(BaseModel):
    user_id: int
    entries: list[ContextEntry]
    total: int


class SaveContextRequest(BaseModel):
    category: str
    key: str
    value: str
    source_agent: Optional[str] = None
    confidence: float = 0.8
    ttl_days: Optional[int] = None  # 过期天数, None=永不过期


# ═══════════════════════════════════════════════════
# 核心: Agent取用接口
# ═══════════════════════════════════════════════════

async def load_user_context(
    db: AsyncSession,
    user_id: int,
    categories: list[str] = None,
    limit: int = 50,
) -> dict:
    """
    加载用户上下文 — Agent处理请求前调用
    
    用法 (在 Agent 代码中):
        context = await load_user_context(db, user_id)
        # context = {
        #     "health": {"blood_sugar_target": "7.0", "medication": "二甲双胍"},
        #     "preference": {"exercise_time": "下午", "favorite_food": "面食"},
        #     "social": {"family": "和老伴住", "occupation": "退休教师"},
        #     "emotion": {"recent_mood": "积极", "stress_source": "儿子工作"},
        #     "goal": {"weight_goal": "减5kg", "primary_concern": "血糖控制"},
        #     "history": {"last_talked_about": "膝盖疼痛", "mentioned_daughter": "在北京工作"},
        # }
    
    返回: {category: {key: value, ...}, ...}
    """
    where = "user_id = :uid AND (expires_at IS NULL OR expires_at > NOW())"
    params = {"uid": user_id, "lim": limit}

    if categories:
        where += " AND category = ANY(:cats)"
        params["cats"] = categories

    stmt = text(f"""
        SELECT category, key, value, confidence
        FROM user_contexts
        WHERE {where}
        ORDER BY confidence DESC, extracted_at DESC
        LIMIT :lim
    """)

    try:
        result = await db.execute(stmt, params)
        rows = result.mappings().all()
    except Exception:
        return {}

    context = {}
    for r in rows:
        cat = r["category"]
        if cat not in context:
            context[cat] = {}
        context[cat][r["key"]] = r["value"]

    return context


async def build_context_prompt(
    db: AsyncSession, user_id: int
) -> str:
    """
    构建上下文提示词 — 直接注入到Agent的System Prompt
    
    用法 (在 master_agent_v0.py 中):
        context_prompt = await build_context_prompt(db, user_id)
        system_prompt = f"你是行为健康教练。\\n\\n{context_prompt}\\n\\n请基于以上了解回应用户。"
    """
    ctx = await load_user_context(db, user_id)
    if not ctx:
        return ""

    parts = ["# 你对这位用户的了解\n"]

    category_names = {
        "health": "健康状况",
        "preference": "偏好习惯",
        "social": "社交家庭",
        "emotion": "情绪状态",
        "goal": "健康目标",
        "history": "过往交流",
    }

    for cat, items in ctx.items():
        cn = category_names.get(cat, cat)
        parts.append(f"## {cn}")
        for k, v in items.items():
            readable_key = k.replace("_", " ")
            parts.append(f"- {readable_key}: {v}")
        parts.append("")

    return "\n".join(parts)


# ═══════════════════════════════════════════════════
# 核心: 上下文提取 (Agent写入)
# ═══════════════════════════════════════════════════

async def save_user_context(
    db: AsyncSession,
    user_id: int,
    category: str,
    key: str,
    value: str,
    source_agent: str = None,
    confidence: float = 0.8,
    ttl_days: int = None,
):
    """
    保存/更新用户上下文
    
    用法 (在 Agent 代码中):
        # 从对话中提取到用户信息后
        await save_user_context(
            db, user_id,
            category="health",
            key="blood_sugar_morning",
            value="7.2 mmol/L (偏高)",
            source_agent="glucose_agent",
            confidence=0.9,
            ttl_days=30,  # 30天后过期
        )
    """
    expires = None
    if ttl_days:
        expires = datetime.now() + timedelta(days=ttl_days)

    await db.execute(text("""
        INSERT INTO user_contexts 
            (user_id, category, key, value, source_agent, confidence, extracted_at, expires_at)
        VALUES 
            (:uid, :cat, :key, :val, :agent, :conf, NOW(), :expires)
        ON CONFLICT (user_id, category, key) 
        DO UPDATE SET 
            value = EXCLUDED.value,
            source_agent = EXCLUDED.source_agent,
            confidence = EXCLUDED.confidence,
            extracted_at = NOW(),
            expires_at = EXCLUDED.expires_at
    """), {
        "uid": user_id, "cat": category, "key": key,
        "val": value, "agent": source_agent,
        "conf": confidence, "expires": expires,
    })


async def extract_context_from_conversation(
    db: AsyncSession,
    user_id: int,
    user_message: str,
    agent_response: str,
    agent_id: str,
):
    """
    从对话中自动提取上下文信息 (规则引擎版)
    
    Phase 2: 接入LLM进行深度提取
    当前: 关键词匹配提取
    """
    message = user_message.lower()

    # 健康数据提取
    import re
    
    # 血糖值
    bg_match = re.search(r'血糖[是为]?\s*([\d.]+)', user_message)
    if bg_match:
        await save_user_context(
            db, user_id, "health", "last_blood_sugar",
            bg_match.group(1) + " mmol/L",
            agent_id, 0.9, ttl_days=7,
        )

    # 体重
    weight_match = re.search(r'体重[是为]?\s*([\d.]+)', user_message)
    if weight_match:
        await save_user_context(
            db, user_id, "health", "last_weight",
            weight_match.group(1) + " kg",
            agent_id, 0.9, ttl_days=30,
        )

    # 情绪关键词
    emotion_keywords = {
        "开心|高兴|快乐|棒": "积极",
        "难过|伤心|沮丧|低落": "低落",
        "焦虑|担心|紧张|害怕": "焦虑",
        "生气|烦|烦躁|愤怒": "烦躁",
        "累|疲惫|没精神": "疲惫",
    }
    for pattern, mood in emotion_keywords.items():
        if re.search(pattern, user_message):
            await save_user_context(
                db, user_id, "emotion", "recent_mood",
                mood, agent_id, 0.7, ttl_days=3,
            )
            break

    # 家庭/社交信息
    family_keywords = {
        r"老伴|爱人|老公|老婆|丈夫|妻子": "marital_status",
        r"儿子|女儿|孩子": "has_children",
        r"孙子|孙女|外孙": "has_grandchildren",
        r"独居|一个人住": "living_alone",
    }
    for pattern, key in family_keywords.items():
        match = re.search(pattern, user_message)
        if match:
            await save_user_context(
                db, user_id, "social", key,
                f"提及: {match.group()}", agent_id, 0.6, ttl_days=90,
            )

    # 记录最近话题
    await save_user_context(
        db, user_id, "history", "last_topic",
        user_message[:100],  # 截取前100字
        agent_id, 0.5, ttl_days=7,
    )


# ═══════════════════════════════════════════════════
# 定时清理过期上下文
# ═══════════════════════════════════════════════════

async def cleanup_expired_contexts(db: AsyncSession):
    """每日凌晨清理过期的上下文记录"""
    result = await db.execute(text("""
        DELETE FROM user_contexts 
        WHERE expires_at IS NOT NULL AND expires_at < NOW()
        RETURNING id
    """))
    deleted = len(result.fetchall())
    await db.commit()
    logger.info(f"清理过期上下文: {deleted} 条")
    return deleted


# ═══════════════════════════════════════════════════
# API端点
# ═══════════════════════════════════════════════════

@router.get("/user/context", response_model=ContextResponse)
async def get_user_context(
    category: Optional[str] = Query(None),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的上下文记忆"""
    user_id = current_user.id
    cats = [category] if category else None
    ctx = await load_user_context(db, user_id, categories=cats)

    entries = []
    for cat, items in ctx.items():
        for k, v in items.items():
            entries.append(ContextEntry(category=cat, key=k, value=v))

    return ContextResponse(user_id=user_id, entries=entries, total=len(entries))


@router.post("/user/context")
async def save_context(
    body: SaveContextRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """手动保存上下文 (测试/管理用)"""
    await save_user_context(
        db, current_user.id,
        body.category, body.key, body.value,
        body.source_agent, body.confidence, body.ttl_days,
    )
    await db.commit()
    return {"success": True}


@router.delete("/user/context/{category}/{key}")
async def delete_context(
    category: str,
    key: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除指定上下文"""
    await db.execute(text("""
        DELETE FROM user_contexts 
        WHERE user_id = :uid AND category = :cat AND key = :key
    """), {"uid": current_user.id, "cat": category, "key": key})
    await db.commit()
    return {"success": True}


# ═══════════════════════════════════════════════════
# 初始化: 确保表存在
# ═══════════════════════════════════════════════════

async def ensure_tables(db: AsyncSession):
    """启动时调用，确保表存在"""
    try:
        await db.execute(text(MIGRATION_SQL))
        await db.commit()
        logger.info("✅ user_contexts + notifications 表就绪")
    except Exception as e:
        logger.warning(f"表创建跳过 (可能已存在): {e}")
        await db.rollback()
