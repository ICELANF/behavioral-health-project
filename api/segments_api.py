"""
用户分层与权限 API
User Segments and Permissions API

提供用户分层、权限检查、升级建议等接口
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from loguru import logger

from core.user_segments import (
    UserSource,
    ServiceTier,
    FeatureModule,
    GrowthPath,
    UserPermissionContext,
    USER_SOURCE_DISPLAY,
    SERVICE_TIER_DISPLAY,
    SERVICE_TIER_LEVELS,
    FEATURE_MODULE_DISPLAY,
    ROLE_LEVELS,
    ROLE_DISPLAY_NAMES,
    USER_SEGMENTS,
    get_user_features,
    get_user_paths,
    has_feature_access,
    has_path_access,
    get_feature_min_tier,
    get_upgrade_suggestion,
    get_segment_by_id,
    get_segments_by_source,
    check_role_permission,
)


router = APIRouter(prefix="/api/v1/segments", tags=["用户分层"])


# ========================================
# 响应模型
# ========================================

class FeatureInfo(BaseModel):
    """功能信息"""
    id: str
    name: str
    accessible: bool
    min_tier: str
    min_tier_name: str


class PathInfo(BaseModel):
    """路径信息"""
    id: str
    name: str
    accessible: bool


class UserPermissionsResponse(BaseModel):
    """用户权限响应"""
    role: str
    role_name: str
    role_level: int
    source: str
    source_name: str
    service_tier: str
    service_tier_name: str
    service_tier_level: int
    features: List[FeatureInfo]
    paths: List[PathInfo]


class SegmentInfo(BaseModel):
    """用户分群信息"""
    id: str
    name: str
    description: str
    source: str
    source_name: str
    default_tier: str
    default_tier_name: str
    feature_count: int
    path_count: int


class SegmentDetailResponse(BaseModel):
    """用户分群详情响应"""
    id: str
    name: str
    description: str
    source: str
    source_name: str
    default_tier: str
    default_tier_name: str
    features: List[str]
    feature_names: List[str]
    paths: List[str]
    path_names: List[str]


class UpgradeSuggestionResponse(BaseModel):
    """升级建议响应"""
    feature: str
    feature_name: str
    current_tier: str
    current_tier_name: str
    required_tier: str
    required_tier_name: str
    upgrade_needed: bool
    message: str


class RoleInfo(BaseModel):
    """角色信息"""
    id: str
    name: str
    level: int


class TierInfo(BaseModel):
    """服务等级信息"""
    id: str
    name: str
    level: int
    description: str


class SourceInfo(BaseModel):
    """用户来源信息"""
    id: str
    name: str
    description: str


# ========================================
# API 端点
# ========================================

@router.get("/permissions", response_model=UserPermissionsResponse)
async def get_user_permissions(
    role: str = Query("observer", description="用户角色"),
    source: str = Query("organic", description="用户来源"),
    service_tier: str = Query("free", description="服务等级"),
):
    """
    获取用户权限

    根据角色、来源和服务等级计算用户的可用功能和路径
    """
    try:
        # 验证参数
        try:
            user_source = UserSource(source)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的用户来源: {source}")

        try:
            tier = ServiceTier(service_tier)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的服务等级: {service_tier}")

        if role not in ROLE_LEVELS:
            raise HTTPException(status_code=400, detail=f"无效的用户角色: {role}")

        # 创建权限上下文
        context = UserPermissionContext(
            role=role,
            source=user_source,
            service_tier=tier,
        )

        # 获取可用功能
        user_features = get_user_features(context)
        features_info = []
        for feature in FeatureModule:
            min_tier = get_feature_min_tier(feature)
            features_info.append(FeatureInfo(
                id=feature.value,
                name=FEATURE_MODULE_DISPLAY.get(feature, feature.value),
                accessible=feature in user_features,
                min_tier=min_tier.value,
                min_tier_name=SERVICE_TIER_DISPLAY.get(min_tier, min_tier.value),
            ))

        # 获取可用路径
        user_paths = get_user_paths(context)
        paths_info = []
        for path in GrowthPath:
            paths_info.append(PathInfo(
                id=path.value,
                name=path.value,  # 使用英文名作为ID
                accessible=path in user_paths,
            ))

        return UserPermissionsResponse(
            role=role,
            role_name=ROLE_DISPLAY_NAMES.get(role, role),
            role_level=ROLE_LEVELS.get(role, 0),
            source=source,
            source_name=USER_SOURCE_DISPLAY.get(user_source, source),
            service_tier=service_tier,
            service_tier_name=SERVICE_TIER_DISPLAY.get(tier, service_tier),
            service_tier_level=SERVICE_TIER_LEVELS.get(tier, 0),
            features=features_info,
            paths=paths_info,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户权限失败: {e}")
        raise HTTPException(status_code=500, detail="获取用户权限失败")


@router.get("/check-feature")
async def check_feature_access(
    feature: str = Query(..., description="功能模块ID"),
    role: str = Query("observer", description="用户角色"),
    source: str = Query("organic", description="用户来源"),
    service_tier: str = Query("free", description="服务等级"),
):
    """
    检查用户是否有某功能的权限
    """
    try:
        # 验证参数
        try:
            feature_module = FeatureModule(feature)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的功能模块: {feature}")

        try:
            user_source = UserSource(source)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的用户来源: {source}")

        try:
            tier = ServiceTier(service_tier)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的服务等级: {service_tier}")

        context = UserPermissionContext(
            role=role,
            source=user_source,
            service_tier=tier,
        )

        accessible = has_feature_access(context, feature_module)

        return {
            "feature": feature,
            "feature_name": FEATURE_MODULE_DISPLAY.get(feature_module, feature),
            "accessible": accessible,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"检查功能权限失败: {e}")
        raise HTTPException(status_code=500, detail="检查功能权限失败")


@router.get("/check-path")
async def check_path_access(
    path: str = Query(..., description="成长路径ID"),
    role: str = Query("observer", description="用户角色"),
    source: str = Query("organic", description="用户来源"),
    service_tier: str = Query("free", description="服务等级"),
):
    """
    检查用户是否可以访问某成长路径
    """
    try:
        # 验证参数
        try:
            growth_path = GrowthPath(path)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的成长路径: {path}")

        try:
            user_source = UserSource(source)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的用户来源: {source}")

        try:
            tier = ServiceTier(service_tier)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的服务等级: {service_tier}")

        context = UserPermissionContext(
            role=role,
            source=user_source,
            service_tier=tier,
        )

        accessible = has_path_access(context, growth_path)

        return {
            "path": path,
            "accessible": accessible,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"检查路径权限失败: {e}")
        raise HTTPException(status_code=500, detail="检查路径权限失败")


@router.get("/upgrade-suggestion", response_model=UpgradeSuggestionResponse)
async def get_upgrade_suggestion_api(
    feature: str = Query(..., description="功能模块ID"),
    service_tier: str = Query("free", description="当前服务等级"),
    source: str = Query("organic", description="用户来源"),
    role: str = Query("observer", description="用户角色"),
):
    """
    获取升级建议

    根据用户想要使用的功能，给出升级建议
    """
    try:
        # 验证参数
        try:
            feature_module = FeatureModule(feature)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的功能模块: {feature}")

        try:
            user_source = UserSource(source)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的用户来源: {source}")

        try:
            tier = ServiceTier(service_tier)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的服务等级: {service_tier}")

        context = UserPermissionContext(
            role=role,
            source=user_source,
            service_tier=tier,
        )

        suggestion = get_upgrade_suggestion(context, feature_module)

        return UpgradeSuggestionResponse(
            feature=feature,
            feature_name=FEATURE_MODULE_DISPLAY.get(feature_module, feature),
            current_tier=suggestion["current_tier"],
            current_tier_name=SERVICE_TIER_DISPLAY.get(
                ServiceTier(suggestion["current_tier"]),
                suggestion["current_tier"]
            ),
            required_tier=suggestion["required_tier"],
            required_tier_name=SERVICE_TIER_DISPLAY.get(
                ServiceTier(suggestion["required_tier"]),
                suggestion["required_tier"]
            ),
            upgrade_needed=suggestion["upgrade_needed"],
            message=suggestion["message"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取升级建议失败: {e}")
        raise HTTPException(status_code=500, detail="获取升级建议失败")


@router.get("/list", response_model=List[SegmentInfo])
async def list_segments(
    source: Optional[str] = Query(None, description="按来源过滤"),
):
    """
    获取用户分群列表
    """
    try:
        if source:
            try:
                user_source = UserSource(source)
                segments = get_segments_by_source(user_source)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的用户来源: {source}")
        else:
            segments = USER_SEGMENTS

        return [
            SegmentInfo(
                id=s.id,
                name=s.name,
                description=s.description,
                source=s.source.value,
                source_name=USER_SOURCE_DISPLAY.get(s.source, s.source.value),
                default_tier=s.default_tier.value,
                default_tier_name=SERVICE_TIER_DISPLAY.get(s.default_tier, s.default_tier.value),
                feature_count=len(s.features),
                path_count=len(s.paths),
            )
            for s in segments
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户分群列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取用户分群列表失败")


@router.get("/detail/{segment_id}", response_model=SegmentDetailResponse)
async def get_segment_detail(segment_id: str):
    """
    获取用户分群详情
    """
    try:
        segment = get_segment_by_id(segment_id)

        if not segment:
            raise HTTPException(status_code=404, detail=f"用户分群不存在: {segment_id}")

        return SegmentDetailResponse(
            id=segment.id,
            name=segment.name,
            description=segment.description,
            source=segment.source.value,
            source_name=USER_SOURCE_DISPLAY.get(segment.source, segment.source.value),
            default_tier=segment.default_tier.value,
            default_tier_name=SERVICE_TIER_DISPLAY.get(
                segment.default_tier, segment.default_tier.value
            ),
            features=[f.value for f in segment.features],
            feature_names=[
                FEATURE_MODULE_DISPLAY.get(f, f.value) for f in segment.features
            ],
            paths=[p.value for p in segment.paths],
            path_names=[p.value for p in segment.paths],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户分群详情失败: {e}")
        raise HTTPException(status_code=500, detail="获取用户分群详情失败")


@router.get("/roles", response_model=List[RoleInfo])
async def list_roles():
    """
    获取所有角色列表
    """
    roles = []
    for role, level in sorted(ROLE_LEVELS.items(), key=lambda x: x[1]):
        if role not in ["system"]:  # 排除系统角色
            roles.append(RoleInfo(
                id=role,
                name=ROLE_DISPLAY_NAMES.get(role, role),
                level=level,
            ))
    return roles


@router.get("/tiers", response_model=List[TierInfo])
async def list_service_tiers():
    """
    获取所有服务等级列表
    """
    tier_descriptions = {
        ServiceTier.FREE: "体验基础功能，了解平台价值",
        ServiceTier.BASIC: "自主学习，获得基础成长支持",
        ServiceTier.PREMIUM: "专家支持，深度成长",
        ServiceTier.VIP: "180天系统课程，全方位专属服务",
    }

    return [
        TierInfo(
            id=tier.value,
            name=SERVICE_TIER_DISPLAY.get(tier, tier.value),
            level=SERVICE_TIER_LEVELS.get(tier, 0),
            description=tier_descriptions.get(tier, ""),
        )
        for tier in ServiceTier
    ]


@router.get("/sources", response_model=List[SourceInfo])
async def list_user_sources():
    """
    获取所有用户来源列表
    """
    source_descriptions = {
        UserSource.ORGANIC: "通过官网、社交媒体等渠道自主注册的用户",
        UserSource.COACH_REFERRED: "由健康教练引荐并跟进服务的客户",
        UserSource.INSTITUTION: "医疗机构、功能社区等合作机构的服务对象",
        UserSource.ENTERPRISE: "企业健康管理计划覆盖的员工",
    }

    return [
        SourceInfo(
            id=source.value,
            name=USER_SOURCE_DISPLAY.get(source, source.value),
            description=source_descriptions.get(source, ""),
        )
        for source in UserSource
    ]


@router.get("/features", response_model=List[dict])
async def list_features():
    """
    获取所有功能模块列表
    """
    return [
        {
            "id": feature.value,
            "name": FEATURE_MODULE_DISPLAY.get(feature, feature.value),
            "min_tier": get_feature_min_tier(feature).value,
            "min_tier_name": SERVICE_TIER_DISPLAY.get(
                get_feature_min_tier(feature),
                get_feature_min_tier(feature).value
            ),
        }
        for feature in FeatureModule
    ]


@router.get("/paths", response_model=List[dict])
async def list_growth_paths():
    """
    获取所有成长路径列表
    """
    path_descriptions = {
        GrowthPath.INTERVENTION: "180天系统干预课程，全面提升行为健康",
        GrowthPath.EXPERT: "专家一对一支持，解决具体问题",
        GrowthPath.KNOWLEDGE: "自主学习知识，理解行为健康原理",
        GrowthPath.PRACTICE: "实践成长，将知识转化为行动",
        GrowthPath.COMMUNITY: "社区互动，获得同伴支持",
        GrowthPath.COACH: "教练培养，成为专业健康教练",
    }

    return [
        {
            "id": path.value,
            "name": path.value,
            "description": path_descriptions.get(path, ""),
        }
        for path in GrowthPath
    ]


@router.post("/check-role-permission")
async def check_role_permission_api(
    user_role: str = Query(..., description="用户角色"),
    required_role: str = Query(..., description="需要的角色"),
):
    """
    检查角色权限

    判断用户角色是否满足所需角色要求
    """
    if user_role not in ROLE_LEVELS:
        raise HTTPException(status_code=400, detail=f"无效的用户角色: {user_role}")

    if required_role not in ROLE_LEVELS:
        raise HTTPException(status_code=400, detail=f"无效的角色要求: {required_role}")

    has_permission = check_role_permission(user_role, required_role)

    return {
        "user_role": user_role,
        "user_role_name": ROLE_DISPLAY_NAMES.get(user_role, user_role),
        "user_role_level": ROLE_LEVELS.get(user_role, 0),
        "required_role": required_role,
        "required_role_name": ROLE_DISPLAY_NAMES.get(required_role, required_role),
        "required_role_level": ROLE_LEVELS.get(required_role, 0),
        "has_permission": has_permission,
    }
