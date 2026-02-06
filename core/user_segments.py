"""
用户分层与权限管理系统
User Segmentation and Permission Management System

v18 版本 - 多来源用户分层管理

用户来源类型：
1. organic - 自然流量（观察者转化）：C端公众用户
2. coach_referred - 教练引荐：健康教练带来的客户
3. institution - 机构服务：医疗机构/功能社区服务群体
4. enterprise - 企业客户：企业健康管理计划

服务等级：
1. free - 免费体验：基础功能
2. basic - 基础会员：标准服务
3. premium - 高级会员：完整服务 + 专家支持
4. vip - VIP会员：180天系统课程 + 专属服务
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from dataclasses import dataclass


# ========================================
# 枚举定义
# ========================================

class UserSource(str, Enum):
    """用户来源"""
    ORGANIC = "organic"              # 自然流量（C端公众）
    COACH_REFERRED = "coach_referred"  # 教练引荐
    INSTITUTION = "institution"      # 机构服务
    ENTERPRISE = "enterprise"        # 企业客户


class ServiceTier(str, Enum):
    """服务等级"""
    FREE = "free"         # 免费体验
    BASIC = "basic"       # 基础会员
    PREMIUM = "premium"   # 高级会员
    VIP = "vip"          # VIP会员


class FeatureModule(str, Enum):
    """功能模块"""
    # 基础功能
    NEEDS_SURVEY = "needs_survey"
    CONTENT_FEED = "content_feed"
    COMMUNITY_READ = "community_read"

    # 成长功能
    SELF_ASSESSMENT = "self_assessment"
    LEARNING_BASIC = "learning_basic"
    TOOL_LIBRARY = "tool_library"
    PROGRESS_TRACKING = "progress_tracking"

    # 高级功能
    LEARNING_FULL = "learning_full"
    EXPERT_CONSULT = "expert_consult"
    GROUP_SESSION = "group_session"
    COMMUNITY_INTERACT = "community_interact"
    AI_COMPANION = "ai_companion"

    # VIP专属
    COURSE_180DAY = "course_180day"
    PRIVATE_COACH = "private_coach"
    CRISIS_SUPPORT = "crisis_support"
    FAMILY_SUPPORT = "family_support"

    # 专家端功能
    CLIENT_MANAGEMENT = "client_management"
    SESSION_CONDUCT = "session_conduct"
    SUPERVISION = "supervision"

    # 管理端功能
    SYSTEM_CONFIG = "system_config"
    USER_MANAGEMENT = "user_management"
    DATA_ANALYTICS = "data_analytics"


class GrowthPath(str, Enum):
    """成长路径"""
    INTERVENTION = "intervention"   # 3见6段5层180天生命重塑路径
    EXPERT = "expert"               # 术业有专攻-专业高效路径
    KNOWLEDGE = "knowledge"         # 行为养成的科学认知路径
    PRACTICE = "practice"           # 做中学·做中觉-良性循环的健康之路
    COMMUNITY = "community"         # 同成长·共健康路径
    COACH = "coach"                 # 自我成长和赋能生命的行为教练之路


# ========================================
# 角色层级（与前端 roles.ts 同步）
# ========================================

ROLE_LEVELS: Dict[str, int] = {
    "observer": 1,
    "grower": 2,
    "sharer": 3,
    "coach": 4,
    "promoter": 5,
    "supervisor": 5,  # 与促进师同级
    "master": 6,
    "admin": 99,
    "system": 100,
}

ROLE_DISPLAY_NAMES: Dict[str, str] = {
    "observer": "行为健康观察员",
    "grower": "成长者",
    "sharer": "分享者",
    "coach": "健康教练",
    "promoter": "行为健康促进师",
    "supervisor": "督导专家",
    "master": "行为健康促进大师",
    "admin": "系统管理员",
    "system": "系统账号",
}


# ========================================
# 显示名称
# ========================================

USER_SOURCE_DISPLAY: Dict[str, str] = {
    UserSource.ORGANIC: "自然注册",
    UserSource.COACH_REFERRED: "教练引荐",
    UserSource.INSTITUTION: "机构服务",
    UserSource.ENTERPRISE: "企业客户",
}

SERVICE_TIER_DISPLAY: Dict[str, str] = {
    ServiceTier.FREE: "免费体验",
    ServiceTier.BASIC: "基础会员",
    ServiceTier.PREMIUM: "高级会员",
    ServiceTier.VIP: "VIP会员",
}

SERVICE_TIER_LEVELS: Dict[str, int] = {
    ServiceTier.FREE: 0,
    ServiceTier.BASIC: 1,
    ServiceTier.PREMIUM: 2,
    ServiceTier.VIP: 3,
}

FEATURE_MODULE_DISPLAY: Dict[str, str] = {
    FeatureModule.NEEDS_SURVEY: "需求调查",
    FeatureModule.CONTENT_FEED: "内容发现",
    FeatureModule.COMMUNITY_READ: "社区浏览",
    FeatureModule.SELF_ASSESSMENT: "自我评估",
    FeatureModule.LEARNING_BASIC: "基础学习",
    FeatureModule.TOOL_LIBRARY: "工具库",
    FeatureModule.PROGRESS_TRACKING: "进度追踪",
    FeatureModule.LEARNING_FULL: "完整学习",
    FeatureModule.EXPERT_CONSULT: "专家咨询",
    FeatureModule.GROUP_SESSION: "团体工坊",
    FeatureModule.COMMUNITY_INTERACT: "社区互动",
    FeatureModule.AI_COMPANION: "AI陪伴",
    FeatureModule.COURSE_180DAY: "180天课程",
    FeatureModule.PRIVATE_COACH: "专属教练",
    FeatureModule.CRISIS_SUPPORT: "危机支持",
    FeatureModule.FAMILY_SUPPORT: "家庭支持",
    FeatureModule.CLIENT_MANAGEMENT: "客户管理",
    FeatureModule.SESSION_CONDUCT: "咨询服务",
    FeatureModule.SUPERVISION: "督导功能",
    FeatureModule.SYSTEM_CONFIG: "系统配置",
    FeatureModule.USER_MANAGEMENT: "用户管理",
    FeatureModule.DATA_ANALYTICS: "数据分析",
}


# ========================================
# 权限配置
# ========================================

@dataclass
class PermissionConfig:
    """权限配置"""
    features: List[FeatureModule]
    paths: List[GrowthPath]
    description: str


# 按服务等级定义基础权限
BASE_PERMISSIONS: Dict[ServiceTier, PermissionConfig] = {
    ServiceTier.FREE: PermissionConfig(
        features=[
            FeatureModule.NEEDS_SURVEY,
            FeatureModule.CONTENT_FEED,
            FeatureModule.COMMUNITY_READ,
        ],
        paths=[],
        description="体验基础功能，了解平台价值",
    ),
    ServiceTier.BASIC: PermissionConfig(
        features=[
            FeatureModule.NEEDS_SURVEY,
            FeatureModule.CONTENT_FEED,
            FeatureModule.COMMUNITY_READ,
            FeatureModule.SELF_ASSESSMENT,
            FeatureModule.LEARNING_BASIC,
            FeatureModule.TOOL_LIBRARY,
            FeatureModule.PROGRESS_TRACKING,
        ],
        paths=[GrowthPath.KNOWLEDGE, GrowthPath.PRACTICE],
        description="自主学习，获得基础成长支持",
    ),
    ServiceTier.PREMIUM: PermissionConfig(
        features=[
            FeatureModule.NEEDS_SURVEY,
            FeatureModule.CONTENT_FEED,
            FeatureModule.COMMUNITY_READ,
            FeatureModule.SELF_ASSESSMENT,
            FeatureModule.LEARNING_BASIC,
            FeatureModule.TOOL_LIBRARY,
            FeatureModule.PROGRESS_TRACKING,
            FeatureModule.LEARNING_FULL,
            FeatureModule.EXPERT_CONSULT,
            FeatureModule.GROUP_SESSION,
            FeatureModule.COMMUNITY_INTERACT,
            FeatureModule.AI_COMPANION,
        ],
        paths=[
            GrowthPath.KNOWLEDGE,
            GrowthPath.PRACTICE,
            GrowthPath.EXPERT,
            GrowthPath.COMMUNITY,
        ],
        description="专家支持，深度成长",
    ),
    ServiceTier.VIP: PermissionConfig(
        features=[
            FeatureModule.NEEDS_SURVEY,
            FeatureModule.CONTENT_FEED,
            FeatureModule.COMMUNITY_READ,
            FeatureModule.SELF_ASSESSMENT,
            FeatureModule.LEARNING_BASIC,
            FeatureModule.TOOL_LIBRARY,
            FeatureModule.PROGRESS_TRACKING,
            FeatureModule.LEARNING_FULL,
            FeatureModule.EXPERT_CONSULT,
            FeatureModule.GROUP_SESSION,
            FeatureModule.COMMUNITY_INTERACT,
            FeatureModule.AI_COMPANION,
            FeatureModule.COURSE_180DAY,
            FeatureModule.PRIVATE_COACH,
            FeatureModule.CRISIS_SUPPORT,
            FeatureModule.FAMILY_SUPPORT,
        ],
        paths=[
            GrowthPath.INTERVENTION,
            GrowthPath.EXPERT,
            GrowthPath.KNOWLEDGE,
            GrowthPath.PRACTICE,
            GrowthPath.COMMUNITY,
        ],
        description="180天系统课程，全方位专属服务",
    ),
}


@dataclass
class SourceAdjustment:
    """来源调整配置"""
    additional_features: List[FeatureModule]
    restricted_features: List[FeatureModule]
    additional_paths: List[GrowthPath]
    description: str


# 来源特殊权限调整
SOURCE_ADJUSTMENTS: Dict[UserSource, SourceAdjustment] = {
    UserSource.ORGANIC: SourceAdjustment(
        additional_features=[],
        restricted_features=[],
        additional_paths=[],
        description="标准权限，按服务等级享受相应功能",
    ),
    UserSource.COACH_REFERRED: SourceAdjustment(
        additional_features=[FeatureModule.AI_COMPANION],
        restricted_features=[],
        additional_paths=[],
        description="教练专属跟进，额外获得AI陪伴支持",
    ),
    UserSource.INSTITUTION: SourceAdjustment(
        additional_features=[FeatureModule.CRISIS_SUPPORT],
        restricted_features=[FeatureModule.PRIVATE_COACH],
        additional_paths=[],
        description="机构统一服务，危机支持优先",
    ),
    UserSource.ENTERPRISE: SourceAdjustment(
        additional_features=[FeatureModule.GROUP_SESSION],
        restricted_features=[],
        additional_paths=[GrowthPath.COMMUNITY],
        description="企业健康计划，团体活动为主",
    ),
}


# ========================================
# 权限上下文
# ========================================

@dataclass
class UserPermissionContext:
    """用户权限上下文"""
    role: str
    source: UserSource
    service_tier: ServiceTier
    institution_id: Optional[str] = None
    coach_id: Optional[str] = None


# ========================================
# 权限检查函数
# ========================================

def check_role_permission(user_role: str, required_role: str) -> bool:
    """
    检查角色权限

    Args:
        user_role: 用户角色
        required_role: 需要的角色

    Returns:
        是否有权限
    """
    user_level = ROLE_LEVELS.get(user_role, 0)
    required_level = ROLE_LEVELS.get(required_role, 0)
    return user_level >= required_level


def get_user_features(context: UserPermissionContext) -> List[FeatureModule]:
    """
    获取用户可用的功能模块

    Args:
        context: 用户权限上下文

    Returns:
        可用功能列表
    """
    # 获取基础权限
    base_permissions = BASE_PERMISSIONS[context.service_tier]
    features = set(base_permissions.features)

    # 应用来源调整
    source_adjust = SOURCE_ADJUSTMENTS[context.source]

    # 添加额外功能
    for f in source_adjust.additional_features:
        features.add(f)

    # 移除受限功能
    for f in source_adjust.restricted_features:
        features.discard(f)

    # 专家端功能（根据角色）
    if context.role in ["coach", "promoter", "supervisor", "master"]:
        features.add(FeatureModule.CLIENT_MANAGEMENT)
        features.add(FeatureModule.SESSION_CONDUCT)

    if context.role in ["promoter", "supervisor", "master"]:
        features.add(FeatureModule.SUPERVISION)

    # 管理端功能
    if context.role == "admin":
        features.add(FeatureModule.SYSTEM_CONFIG)
        features.add(FeatureModule.USER_MANAGEMENT)
        features.add(FeatureModule.DATA_ANALYTICS)

    return list(features)


def get_user_paths(context: UserPermissionContext) -> List[GrowthPath]:
    """
    获取用户可用的成长路径

    Args:
        context: 用户权限上下文

    Returns:
        可用路径列表
    """
    base_permissions = BASE_PERMISSIONS[context.service_tier]
    paths = set(base_permissions.paths)

    # 应用来源调整
    source_adjust = SOURCE_ADJUSTMENTS[context.source]
    for p in source_adjust.additional_paths:
        paths.add(p)

    # 行为健康教练之路（专家角色）
    if context.role in ["coach", "promoter", "supervisor", "master"]:
        paths.add(GrowthPath.COACH)

    return list(paths)


def has_feature_access(context: UserPermissionContext, feature: FeatureModule) -> bool:
    """检查用户是否有某功能的权限"""
    user_features = get_user_features(context)
    return feature in user_features


def has_path_access(context: UserPermissionContext, path: GrowthPath) -> bool:
    """检查用户是否可以访问某成长路径"""
    user_paths = get_user_paths(context)
    return path in user_paths


def get_feature_min_tier(feature: FeatureModule) -> ServiceTier:
    """获取功能的最低服务等级要求"""
    for tier in [ServiceTier.FREE, ServiceTier.BASIC, ServiceTier.PREMIUM, ServiceTier.VIP]:
        if feature in BASE_PERMISSIONS[tier].features:
            return tier
    return ServiceTier.VIP


def get_upgrade_suggestion(
    context: UserPermissionContext,
    desired_feature: FeatureModule
) -> Dict[str, Any]:
    """获取升级建议"""
    required_tier = get_feature_min_tier(desired_feature)
    current_level = SERVICE_TIER_LEVELS[context.service_tier]
    required_level = SERVICE_TIER_LEVELS[required_tier]

    upgrade_needed = required_level > current_level

    if upgrade_needed:
        message = f"该功能需要{SERVICE_TIER_DISPLAY[required_tier]}，请升级您的服务"
    else:
        message = "您已有权限访问此功能"

    return {
        "current_tier": context.service_tier.value,
        "required_tier": required_tier.value,
        "upgrade_needed": upgrade_needed,
        "message": message,
    }


# ========================================
# 用户分群定义
# ========================================

@dataclass
class UserSegment:
    """用户分群"""
    id: str
    name: str
    description: str
    source: UserSource
    default_tier: ServiceTier
    features: List[FeatureModule]
    paths: List[GrowthPath]


USER_SEGMENTS: List[UserSegment] = [
    UserSegment(
        id="public_observer",
        name="C端观察者",
        description="公众用户，通过需求调查了解自己的状态",
        source=UserSource.ORGANIC,
        default_tier=ServiceTier.FREE,
        features=[
            FeatureModule.NEEDS_SURVEY,
            FeatureModule.CONTENT_FEED,
            FeatureModule.COMMUNITY_READ,
        ],
        paths=[],
    ),
    UserSegment(
        id="self_grower",
        name="自主成长者",
        description="付费会员，自主学习和实践成长",
        source=UserSource.ORGANIC,
        default_tier=ServiceTier.BASIC,
        features=[
            FeatureModule.NEEDS_SURVEY,
            FeatureModule.CONTENT_FEED,
            FeatureModule.COMMUNITY_READ,
            FeatureModule.SELF_ASSESSMENT,
            FeatureModule.LEARNING_BASIC,
            FeatureModule.TOOL_LIBRARY,
            FeatureModule.PROGRESS_TRACKING,
        ],
        paths=[GrowthPath.KNOWLEDGE, GrowthPath.PRACTICE],
    ),
    UserSegment(
        id="coach_client",
        name="教练客户",
        description="健康教练引荐的客户，获得专属跟进",
        source=UserSource.COACH_REFERRED,
        default_tier=ServiceTier.PREMIUM,
        features=[
            FeatureModule.NEEDS_SURVEY,
            FeatureModule.CONTENT_FEED,
            FeatureModule.COMMUNITY_READ,
            FeatureModule.SELF_ASSESSMENT,
            FeatureModule.LEARNING_FULL,
            FeatureModule.TOOL_LIBRARY,
            FeatureModule.PROGRESS_TRACKING,
            FeatureModule.EXPERT_CONSULT,
            FeatureModule.AI_COMPANION,
        ],
        paths=[GrowthPath.KNOWLEDGE, GrowthPath.PRACTICE, GrowthPath.EXPERT],
    ),
    UserSegment(
        id="institution_patient",
        name="机构服务对象",
        description="医疗机构/功能社区的服务群体",
        source=UserSource.INSTITUTION,
        default_tier=ServiceTier.PREMIUM,
        features=[
            FeatureModule.NEEDS_SURVEY,
            FeatureModule.CONTENT_FEED,
            FeatureModule.SELF_ASSESSMENT,
            FeatureModule.LEARNING_FULL,
            FeatureModule.TOOL_LIBRARY,
            FeatureModule.PROGRESS_TRACKING,
            FeatureModule.EXPERT_CONSULT,
            FeatureModule.GROUP_SESSION,
            FeatureModule.CRISIS_SUPPORT,
        ],
        paths=[GrowthPath.KNOWLEDGE, GrowthPath.PRACTICE, GrowthPath.EXPERT],
    ),
    UserSegment(
        id="enterprise_employee",
        name="企业员工",
        description="企业健康管理计划覆盖的员工",
        source=UserSource.ENTERPRISE,
        default_tier=ServiceTier.BASIC,
        features=[
            FeatureModule.NEEDS_SURVEY,
            FeatureModule.CONTENT_FEED,
            FeatureModule.COMMUNITY_READ,
            FeatureModule.SELF_ASSESSMENT,
            FeatureModule.LEARNING_BASIC,
            FeatureModule.TOOL_LIBRARY,
            FeatureModule.PROGRESS_TRACKING,
            FeatureModule.GROUP_SESSION,
        ],
        paths=[GrowthPath.KNOWLEDGE, GrowthPath.PRACTICE, GrowthPath.COMMUNITY],
    ),
    UserSegment(
        id="vip_member",
        name="VIP会员",
        description="180天系统课程学员，全方位专属服务",
        source=UserSource.ORGANIC,
        default_tier=ServiceTier.VIP,
        features=[
            FeatureModule.NEEDS_SURVEY,
            FeatureModule.CONTENT_FEED,
            FeatureModule.COMMUNITY_READ,
            FeatureModule.SELF_ASSESSMENT,
            FeatureModule.LEARNING_FULL,
            FeatureModule.TOOL_LIBRARY,
            FeatureModule.PROGRESS_TRACKING,
            FeatureModule.EXPERT_CONSULT,
            FeatureModule.GROUP_SESSION,
            FeatureModule.COMMUNITY_INTERACT,
            FeatureModule.AI_COMPANION,
            FeatureModule.COURSE_180DAY,
            FeatureModule.PRIVATE_COACH,
            FeatureModule.CRISIS_SUPPORT,
            FeatureModule.FAMILY_SUPPORT,
        ],
        paths=[
            GrowthPath.INTERVENTION,
            GrowthPath.EXPERT,
            GrowthPath.KNOWLEDGE,
            GrowthPath.PRACTICE,
            GrowthPath.COMMUNITY,
        ],
    ),
]


def get_segment_by_id(segment_id: str) -> Optional[UserSegment]:
    """根据ID获取用户分群"""
    for segment in USER_SEGMENTS:
        if segment.id == segment_id:
            return segment
    return None


def get_segments_by_source(source: UserSource) -> List[UserSegment]:
    """根据来源获取用户分群"""
    return [s for s in USER_SEGMENTS if s.source == source]


# ========================================
# 导出
# ========================================

__all__ = [
    # 枚举
    "UserSource",
    "ServiceTier",
    "FeatureModule",
    "GrowthPath",

    # 显示名称
    "USER_SOURCE_DISPLAY",
    "SERVICE_TIER_DISPLAY",
    "SERVICE_TIER_LEVELS",
    "FEATURE_MODULE_DISPLAY",
    "ROLE_LEVELS",
    "ROLE_DISPLAY_NAMES",

    # 权限配置
    "PermissionConfig",
    "SourceAdjustment",
    "BASE_PERMISSIONS",
    "SOURCE_ADJUSTMENTS",

    # 上下文和函数
    "UserPermissionContext",
    "check_role_permission",
    "get_user_features",
    "get_user_paths",
    "has_feature_access",
    "has_path_access",
    "get_feature_min_tier",
    "get_upgrade_suggestion",

    # 用户分群
    "UserSegment",
    "USER_SEGMENTS",
    "get_segment_by_id",
    "get_segments_by_source",
]
