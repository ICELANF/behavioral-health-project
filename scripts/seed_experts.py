"""
专家白标种子数据脚本

用法:
  cd D:/behavioral-health-project
  python scripts/seed_experts.py
"""
import os
import sys
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal
from core.models import (
    ExpertTenant, TenantAgentMapping, TenantStatus, TenantTier, User
)


# ============================================================
# 5位专家的完整配置
# ============================================================

EXPERT_TENANTS = [
    {
        "id": "dr-chen-endo",
        "brand_name": "陈主任·内分泌代谢工作室",
        "brand_tagline": "科学控糖·精准代谢·远离并发症",
        "brand_avatar": "🔬",
        "brand_logo_url": "",
        "brand_colors": {"primary": "#1E40AF", "accent": "#3B82F6", "bg": "#EFF6FF", "text": "#1E3A5F"},
        "brand_theme_id": "medicalBlue",
        "custom_domain": "",
        "expert_title": "主任医师·内分泌科",
        "expert_self_intro": "三甲医院内分泌科主任医师，25年临床经验。专注糖尿病、甲状腺疾病、代谢综合征的综合管理。倡导'药物+行为'双轨干预，帮助上千位患者实现血糖达标和药物减量。",
        "expert_specialties": ["糖尿病管理", "甲状腺疾病", "代谢综合征", "胰岛素抵抗"],
        "expert_credentials": ["主任医师", "医学博士", "硕士生导师", "中华医学会内分泌分会委员"],
        "enabled_agents": ["glucose", "nutrition", "exercise", "sleep", "weight", "motivation", "crisis"],
        "agent_persona_overrides": {
            "glucose": {"name": "控糖管家", "greeting": "您好，我是陈主任工作室的控糖管家。今天血糖监测情况如何？", "tone": "专业严谨、温暖关怀、数据驱动"},
            "nutrition": {"name": "营养顾问", "greeting": "您好，我是您的营养顾问。让我们一起规划适合您的饮食方案。", "tone": "科学实用、具体可执行"},
            "weight": {"name": "代谢教练", "greeting": "您好，我是代谢管理教练。让我们用科学方法优化您的代谢健康。", "tone": "鼓励支持、循序渐进"},
        },
        "service_packages": [
            {"id": "trial", "name": "7天体验", "price": 0, "duration_days": 7, "features": ["AI控糖问答", "饮食建议"]},
            {"id": "basic", "name": "控糖基础包", "price": 299, "duration_days": 30, "features": ["AI全天候陪伴", "个性化饮食方案", "运动处方"]},
            {"id": "premium", "name": "代谢管理VIP", "price": 1999, "duration_days": 180, "features": ["180天全程管理", "专属教练跟进", "每月报告", "药物调整建议"]},
        ],
        "welcome_message": "欢迎来到陈主任·内分泌代谢工作室！这里有专业的AI助手团队，帮助您科学管理血糖和代谢健康。让我们一起开始您的健康管理之旅。",
        "status": "active",
        "tier": "strategic_partner",
        "max_clients": 500,
        "revenue_share_expert": 0.85,
    },
    {
        "id": "teacher-zhang-tcm",
        "brand_name": "张老师·中医养生工作室",
        "brand_tagline": "辨体施养·节气调摄·治未病",
        "brand_avatar": "🌿",
        "brand_logo_url": "",
        "brand_colors": {"primary": "#2D5A3D", "accent": "#6B8E5A", "bg": "#F0F7F0", "text": "#2D3B2D"},
        "brand_theme_id": "tcmGreen",
        "custom_domain": "",
        "expert_title": "中医副主任医师·养生指导师",
        "expert_self_intro": "中医世家第四代传人，20年临床经验。擅长体质辨识与个性化养生方案设计。融合传统中医智慧与现代健康管理理念，帮助都市人找到适合自己的养生之道。",
        "expert_specialties": ["体质辨识", "节气养生", "药膳食疗", "经络调理", "情志养生"],
        "expert_credentials": ["中医副主任医师", "国家级养生指导师", "中华中医药学会会员"],
        "enabled_agents": ["tcm", "nutrition", "sleep", "stress", "mental", "exercise", "crisis"],
        "agent_persona_overrides": {
            "tcm": {"name": "养生顾问", "greeting": "您好，我是张老师工作室的养生顾问。让我先了解一下您的体质状况。", "tone": "温和亲切、深入浅出、文化底蕴"},
            "nutrition": {"name": "药膳管家", "greeting": "您好，我来帮您根据体质和时令，搭配适合的饮食调理方案。", "tone": "生活化、接地气、讲究时令"},
            "sleep": {"name": "安眠助手", "greeting": "您好，中医讲'阳入于阴则寐'。让我了解您的睡眠状况，为您调理。", "tone": "轻柔舒缓、融合中医理念"},
        },
        "service_packages": [
            {"id": "trial", "name": "体质测评体验", "price": 0, "duration_days": 7, "features": ["九型体质测评", "养生建议"]},
            {"id": "basic", "name": "四季养生包", "price": 199, "duration_days": 90, "features": ["体质调理方案", "节气提醒", "药膳推荐"]},
            {"id": "premium", "name": "全年养生VIP", "price": 1599, "duration_days": 365, "features": ["全年体质跟踪", "个性化调理", "节气养生课", "专家答疑"]},
        ],
        "welcome_message": "欢迎来到张老师·中医养生工作室！中医养生，贵在辨体施养、顺应自然。让我们先从了解您的体质开始。",
        "status": "active",
        "tier": "premium_partner",
        "max_clients": 200,
        "revenue_share_expert": 0.80,
    },
    {
        "id": "dr-wang-emotion",
        "brand_name": "王医生·情绪疗愈工作室",
        "brand_tagline": "看见情绪·理解自己·温柔前行",
        "brand_avatar": "💜",
        "brand_logo_url": "",
        "brand_colors": {"primary": "#6D28D9", "accent": "#A78BFA", "bg": "#F5F3FF", "text": "#3B1F6E"},
        "brand_theme_id": "healingPurple",
        "custom_domain": "",
        "expert_title": "精神科副主任医师·心理治疗师",
        "expert_self_intro": "精神科副主任医师，认知行为治疗师(CBT)，15年临床经验。专注焦虑、抑郁、睡眠障碍的非药物干预。相信每个人都有自我疗愈的力量，我们只需找到合适的路径。",
        "expert_specialties": ["焦虑管理", "情绪调节", "睡眠改善", "正念冥想", "压力管理"],
        "expert_credentials": ["精神科副主任医师", "注册心理治疗师", "CBT认证治疗师", "正念减压(MBSR)导师"],
        "enabled_agents": ["mental", "stress", "sleep", "motivation", "behavior_rx", "crisis"],
        "agent_persona_overrides": {
            "mental": {"name": "暖心小悦", "greeting": "你好呀，我是暖心小悦。今天感觉怎么样？无论什么心情，都可以和我说说。", "tone": "温暖共情、不评判、安全接纳"},
            "stress": {"name": "静心助手", "greeting": "你好，我是静心助手。感到压力的时候，让我陪你做一些放松练习。", "tone": "平静舒缓、引导式"},
            "sleep": {"name": "安眠精灵", "greeting": "晚上好，我是安眠精灵。让我帮你放松身心，为好眠做准备。", "tone": "轻柔、催眠感、低刺激"},
        },
        "service_packages": [
            {"id": "trial", "name": "情绪自测体验", "price": 0, "duration_days": 7, "features": ["情绪评估", "每日正念音频"]},
            {"id": "basic", "name": "情绪管理基础", "price": 349, "duration_days": 30, "features": ["CBT自助工具", "情绪日记", "每周练习"]},
            {"id": "premium", "name": "深度疗愈90天", "price": 2499, "duration_days": 90, "features": ["90天系统训练", "专属心理支持", "危机响应", "月度评估"]},
        ],
        "welcome_message": "欢迎来到一个安全的空间。在这里，你的每一种情绪都值得被看见。让我们一起，找到适合你的疗愈之路。",
        "status": "active",
        "tier": "premium_partner",
        "max_clients": 200,
        "revenue_share_expert": 0.80,
    },
    {
        "id": "prof-liu-cardiac",
        "brand_name": "刘教授·心脏康复工作室",
        "brand_tagline": "心脏康复·运动处方·重返活力生活",
        "brand_avatar": "❤️",
        "brand_logo_url": "",
        "brand_colors": {"primary": "#DC2626", "accent": "#F87171", "bg": "#FEF2F2", "text": "#7F1D1D"},
        "brand_theme_id": "cardiacRed",
        "custom_domain": "",
        "expert_title": "心血管内科教授·运动医学专家",
        "expert_self_intro": "心血管内科教授，运动医学博士，30年临床与科研经验。专注心脏康复的运动处方设计与心血管风险管理。主持多项国家级心脏康复研究项目，推动运动成为心脏病人的'良药'。",
        "expert_specialties": ["心脏康复", "运动处方", "心血管风险管理", "高血压管理", "心衰康复"],
        "expert_credentials": ["心内科教授", "博士生导师", "运动医学博士", "中华心血管病学会委员"],
        "enabled_agents": ["cardiac_rehab", "exercise", "nutrition", "sleep", "stress", "glucose", "motivation", "crisis"],
        "agent_persona_overrides": {
            "cardiac_rehab": {"name": "心康教练", "greeting": "您好，我是刘教授工作室的心康教练。让我帮您制定安全有效的心脏康复方案。", "tone": "权威专业、安全第一、循证医学"},
            "exercise": {"name": "运动处方师", "greeting": "您好，运动是心脏最好的良药，但需要精准的'剂量'。让我为您量身定制运动方案。", "tone": "科学精准、安全警戒、鼓励前行"},
            "nutrition": {"name": "心健营养师", "greeting": "您好，心脏健康离不开科学饮食。让我帮您搭配护心饮食方案。", "tone": "实用具体、数据化、可量化"},
        },
        "service_packages": [
            {"id": "trial", "name": "心脏风险评估", "price": 0, "duration_days": 7, "features": ["心血管风险评估", "基础运动建议"]},
            {"id": "basic", "name": "心康基础包", "price": 499, "duration_days": 30, "features": ["个性化运动处方", "饮食方案", "每日监测提醒"]},
            {"id": "premium", "name": "心脏康复全程", "price": 3999, "duration_days": 180, "features": ["180天康复计划", "运动强度阶梯", "专家远程指导", "紧急响应"]},
        ],
        "welcome_message": "欢迎来到刘教授·心脏康复工作室。心脏康复是一个系统工程，我们将为您提供安全、科学、个性化的康复方案。您的每一步进步，都是心脏的一次胜利。",
        "status": "active",
        "tier": "strategic_partner",
        "max_clients": 300,
        "revenue_share_expert": 0.85,
    },
    {
        "id": "teacher-li-behavior",
        "brand_name": "李老师·行为教练工作室",
        "brand_tagline": "习惯重塑·微行为设计·从知道到做到",
        "brand_avatar": "🎯",
        "brand_logo_url": "",
        "brand_colors": {"primary": "#D97706", "accent": "#F59E0B", "bg": "#FFFBEB", "text": "#78350F"},
        "brand_theme_id": "warmSand",
        "custom_domain": "",
        "expert_title": "行为健康促进师·动机访谈培训师",
        "expert_self_intro": "行为健康促进师，12年专注'从知道到做到'。融合动机访谈(MI)、微习惯设计、正念觉察三大方法论，帮助3000+人建立可持续的健康行为。不讲大道理，只设计小行动。",
        "expert_specialties": ["行为设计", "习惯养成", "动机激发", "微行为处方", "行为改变维持"],
        "expert_credentials": ["L5促进师", "动机访谈(MI)认证培训师", "行为设计师", "正念教练"],
        "enabled_agents": ["behavior_rx", "motivation", "mental", "exercise", "nutrition", "sleep", "stress", "crisis"],
        "agent_persona_overrides": {
            "behavior_rx": {"name": "行为设计师", "greeting": "嗨！我是你的行为设计师。告诉我你想改变什么，我来帮你把大目标拆成今天就能做的小行动。", "tone": "活力亲和、行动导向、具体可执行"},
            "motivation": {"name": "能量教练", "greeting": "嗨！我是能量教练。坚持不下去很正常——关键是找到你的'最小启动量'。聊聊看？", "tone": "正能量、不说教、共情理解"},
            "mental": {"name": "觉察伙伴", "greeting": "你好，我是觉察伙伴。行为改变的第一步是'看见'。让我们一起看看发生了什么。", "tone": "温和好奇、引导觉察、不评判"},
        },
        "service_packages": [
            {"id": "trial", "name": "行为诊断体验", "price": 0, "duration_days": 7, "features": ["行为模式评估", "3个微行为处方"]},
            {"id": "basic", "name": "21天习惯启动", "price": 199, "duration_days": 21, "features": ["每日微行为任务", "打卡追踪", "行为卡点分析"]},
            {"id": "premium", "name": "90天行为重塑", "price": 1299, "duration_days": 90, "features": ["90天系统训练", "个性化行为处方", "动机维持策略", "月度复盘"]},
        ],
        "welcome_message": "欢迎！在这里没有'你应该做到'，只有'你今天可以试试这个'。改变不需要意志力，需要的是好的设计。让我们开始吧。",
        "status": "active",
        "tier": "premium_partner",
        "max_clients": 200,
        "revenue_share_expert": 0.80,
    },
]


# Agent 元数据
AGENT_META = {
    "sleep":         {"default_name": "睡眠管理师", "default_avatar": "🌙"},
    "glucose":       {"default_name": "血糖管理师", "default_avatar": "📊"},
    "stress":        {"default_name": "压力管理师", "default_avatar": "🧘"},
    "mental":        {"default_name": "心理支持师", "default_avatar": "💚"},
    "nutrition":     {"default_name": "营养指导师", "default_avatar": "🥗"},
    "exercise":      {"default_name": "运动指导师", "default_avatar": "🏃"},
    "tcm":           {"default_name": "中医养生师", "default_avatar": "🌿"},
    "crisis":        {"default_name": "安全守护者", "default_avatar": "🛡️"},
    "motivation":    {"default_name": "动机激发师", "default_avatar": "🔥"},
    "behavior_rx":   {"default_name": "行为处方师", "default_avatar": "🎯"},
    "weight":        {"default_name": "体重管理师", "default_avatar": "⚖️"},
    "cardiac_rehab": {"default_name": "心脏康复师", "default_avatar": "❤️"},
}


def build_agent_mappings(tenant_data: dict) -> list:
    """根据租户配置生成 Agent 映射记录"""
    mappings = []
    overrides = tenant_data.get("agent_persona_overrides", {})

    for idx, agent_id in enumerate(tenant_data["enabled_agents"]):
        meta = AGENT_META.get(agent_id, {})
        override = overrides.get(agent_id, {})

        mappings.append({
            "tenant_id": tenant_data["id"],
            "agent_id": agent_id,
            "display_name": override.get("name", meta.get("default_name", agent_id)),
            "display_avatar": meta.get("default_avatar", "🤖"),
            "greeting": override.get("greeting", ""),
            "tone": override.get("tone", ""),
            "bio": "",
            "is_enabled": True,
            "is_primary": idx == 0,
            "sort_order": idx,
        })

    # 确保 crisis 存在
    if "crisis" not in tenant_data["enabled_agents"]:
        crisis_meta = AGENT_META["crisis"]
        mappings.append({
            "tenant_id": tenant_data["id"],
            "agent_id": "crisis",
            "display_name": crisis_meta["default_name"],
            "display_avatar": crisis_meta["default_avatar"],
            "greeting": "",
            "tone": "",
            "bio": "",
            "is_enabled": True,
            "is_primary": False,
            "sort_order": 99,
        })

    return mappings


# 专家角色名 → 用户名 映射 (关联现有 demo 用户)
EXPERT_USER_MAP = {
    "dr-chen-endo": "promoter",
    "teacher-zhang-tcm": "supervisor",
    "dr-wang-emotion": "master",
    "prof-liu-cardiac": "coach",
    "teacher-li-behavior": "sharer",
}


def seed_experts():
    """同步写入5位专家数据"""
    db = SessionLocal()
    try:
        for tenant_data in EXPERT_TENANTS:
            # 检查是否已存在
            existing = db.query(ExpertTenant).filter_by(id=tenant_data["id"]).first()
            if existing:
                print(f"  skip existing: {tenant_data['id']}")
                continue

            # 查找关联的平台用户
            username = EXPERT_USER_MAP.get(tenant_data["id"])
            user = db.query(User).filter_by(username=username).first() if username else None
            if not user:
                print(f"  WARN: user '{username}' not found for {tenant_data['id']}, using admin")
                user = db.query(User).filter_by(username="admin").first()
            if not user:
                print(f"  ERROR: no user found, skipping {tenant_data['id']}")
                continue

            # 构建租户字段 (排除 agent_persona_overrides 因为它需要单独设置)
            tenant_fields = {k: v for k, v in tenant_data.items()
                            if k not in ("agent_persona_overrides",)}
            tenant = ExpertTenant(**tenant_fields)
            tenant.expert_user_id = user.id
            tenant.agent_persona_overrides = tenant_data.get("agent_persona_overrides", {})
            tenant.created_at = datetime.utcnow()
            tenant.updated_at = datetime.utcnow()
            db.add(tenant)

            # 创建 Agent 映射
            mappings = build_agent_mappings(tenant_data)
            for m_data in mappings:
                mapping = TenantAgentMapping(**m_data, created_at=datetime.utcnow())
                db.add(mapping)

            print(f"  OK: {tenant_data['brand_name']} ({tenant_data['id']}) -> user={username}(id={user.id})")

        db.commit()
        print(f"\nDone: {len(EXPERT_TENANTS)} experts seeded")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("  Seed Expert Tenants")
    print("=" * 60)
    seed_experts()
