"""
专家自助注册入驻 API
Expert Self-Registration API

路由前缀: /api/v1/expert-registration

8 端点:
  GET  /domains                              — 领域列表 (公开)
  POST /apply                                — 提交入驻申请
  GET  /my-application                       — 查询我的申请
  PUT  /my-application                       — 修改申请 (仅 pending)
  GET  /admin/applications                   — 待审核列表 (admin)
  GET  /admin/applications/{tenant_id}       — 申请详情 (admin)
  POST /admin/applications/{tenant_id}/approve — 审核通过
  POST /admin/applications/{tenant_id}/reject  — 审核拒绝
"""
import json
import os
import re
import logging
from datetime import datetime
from typing import Optional, List

import uuid
import shutil

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.database import get_db
from core.models import (
    ExpertTenant, TenantAgentMapping, TenantAuditLog,
    TenantStatus, TenantTier, User, UserRole, ROLE_LEVEL,
)
from api.dependencies import get_current_user, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/expert-registration", tags=["expert-registration"])

# ── 领域配置缓存 ──
_domains_cache = None

def _load_domains() -> list:
    global _domains_cache
    if _domains_cache is not None:
        return _domains_cache
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "configs", "expert_domains.json",
    )
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        _domains_cache = data.get("domains", [])
    except Exception as e:
        logger.warning("加载 expert_domains.json 失败: %s", e)
        _domains_cache = []
    return _domains_cache


def _get_domain_by_id(domain_id: str) -> Optional[dict]:
    for d in _load_domains():
        if d["id"] == domain_id:
            return d
    return None


def _generate_tenant_id(brand_name: str, user_id: int, db: Session) -> str:
    """生成唯一 tenant_id slug"""
    # 去特殊字符, 保留字母数字和中文
    slug = re.sub(r'[^\w\u4e00-\u9fff]', '', brand_name).strip()
    # 纯中文或空 → fallback
    if not slug or not re.search(r'[a-zA-Z0-9]', slug):
        slug = f"expert-{user_id}"
    else:
        # 取前 16 字符的英数部分
        slug = re.sub(r'[\u4e00-\u9fff]', '', slug)[:16].lower()
        slug = re.sub(r'[^a-z0-9-]', '-', slug).strip('-')
        if not slug:
            slug = f"expert-{user_id}"

    # 唯一性检查
    base_slug = slug
    counter = 2
    while db.query(ExpertTenant).filter(ExpertTenant.id == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1

    return slug


# ── Pydantic Schemas ──

class ApplyRequest(BaseModel):
    brand_name: str = Field(..., min_length=2, max_length=128)
    brand_tagline: str = ""
    brand_avatar: str = ""
    expert_title: str = ""
    expert_self_intro: str = ""
    expert_specialties: List[str] = []
    expert_credentials: List[str] = []
    credential_images: List[str] = Field(default=[], description="资质证书图片URL列表")
    full_name: str = Field(default="", description="真实姓名")
    gender: str = Field(default="", description="性别: male/female/other")
    birthday: str = Field(default="", description="出生日期 YYYY-MM-DD")
    phone: str = Field(default="", description="手机号")
    email: str = Field(default="", description="邮箱")
    avatar_url: str = Field(default="", description="个人照片URL")
    workplace: str = Field(default="", description="工作单位")
    work_position: str = Field(default="", description="职务/职称")
    work_address: str = Field(default="", description="单位地址")
    communication_address: str = Field(default="", description="通信地址")
    bank_name: str = Field(default="", description="开户银行")
    bank_branch: str = Field(default="", description="开户支行")
    bank_account: str = Field(default="", description="银行账号")
    bank_holder: str = Field(default="", description="开户人")
    domain_id: str = Field(..., description="领域ID (来自 /domains)")
    selected_agents: List[str] = Field(default=[], description="用户选择的Agent (为空则用领域推荐)")
    welcome_message: str = ""
    service_packages: List[dict] = []

class ApplicationUpdateRequest(BaseModel):
    brand_name: Optional[str] = None
    brand_tagline: Optional[str] = None
    brand_avatar: Optional[str] = None
    expert_title: Optional[str] = None
    expert_self_intro: Optional[str] = None
    expert_specialties: Optional[List[str]] = None
    expert_credentials: Optional[List[str]] = None
    domain_id: Optional[str] = None
    selected_agents: Optional[List[str]] = None
    welcome_message: Optional[str] = None

class RejectRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)


# ── 辅助: 构建 application_data + 同步用户资料 ──

def _build_application_data(data: ApplyRequest, agents: list) -> dict:
    """将申请表单全字段打包为 JSON"""
    return {
        "domain_id": data.domain_id,
        "selected_agents": agents,
        "brand_name": data.brand_name,
        "brand_tagline": data.brand_tagline,
        "expert_title": data.expert_title,
        "expert_self_intro": data.expert_self_intro,
        "expert_specialties": data.expert_specialties,
        "expert_credentials": data.expert_credentials,
        "credential_images": data.credential_images,
        "full_name": data.full_name,
        "gender": data.gender,
        "birthday": data.birthday,
        "phone": data.phone,
        "email": data.email,
        "avatar_url": data.avatar_url,
        "workplace": data.workplace,
        "work_position": data.work_position,
        "work_address": data.work_address,
        "communication_address": data.communication_address,
        "bank_name": data.bank_name,
        "bank_branch": data.bank_branch,
        "bank_account": data.bank_account,
        "bank_holder": data.bank_holder,
        "welcome_message": data.welcome_message,
        "service_packages": data.service_packages,
    }


def _sync_user_profile(user: User, data: ApplyRequest):
    """将个人信息同步到 User 表"""
    if data.full_name:
        user.full_name = data.full_name
    if data.phone:
        user.phone = data.phone
    if data.gender:
        user.gender = data.gender
    if data.birthday:
        try:
            user.date_of_birth = datetime.strptime(data.birthday, "%Y-%m-%d")
        except ValueError:
            pass


# ── 公开端点 ──

@router.get("/domains")
def get_domains():
    """获取领域列表 + 推荐 Agent (公开)"""
    domains = _load_domains()
    return {
        "success": True,
        "data": domains,
    }


# ── 文件上传 ──

UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "static", "uploads", "credentials",
)
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/upload-credential")
async def upload_credential_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """上传资质证书图片，返回 URL"""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, detail=f"不支持的文件类型: {ext}")

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(400, detail="文件大小不能超过 10MB")

    filename = f"{current_user.id}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(contents)

    url = f"/api/static/uploads/credentials/{filename}"
    return {"success": True, "data": {"url": url, "filename": filename}}


# ── 用户端点 ──

@router.post("/apply")
def apply_registration(
    data: ApplyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """提交专家入驻申请"""
    # 1. 校验: 用户未有关联的 ExpertTenant
    existing = db.query(ExpertTenant).filter(
        ExpertTenant.expert_user_id == current_user.id,
    ).first()
    if existing:
        if existing.application_status == "rejected":
            # 被拒绝后可重新申请: 更新现有记录
            pass
        else:
            raise HTTPException(
                status_code=409,
                detail=f"您已有关联的工作室 (状态: {existing.application_status or existing.status.value})",
            )

    # 2. 加载领域配置
    domain = _get_domain_by_id(data.domain_id)
    if not domain:
        raise HTTPException(status_code=400, detail=f"无效领域: {data.domain_id}")

    # 3. 确定 Agent 列表
    agents = data.selected_agents if data.selected_agents else domain["recommended_agents"]
    # crisis 必须包含
    if "crisis" not in agents:
        agents = agents + ["crisis"]

    # 4. 品牌配色
    brand_colors = domain.get("default_colors", {"primary": "#1E40AF", "accent": "#3B82F6", "bg": "#F0F7FF"})
    brand_theme = domain.get("default_theme", "default")
    brand_avatar = data.brand_avatar or domain.get("icon", "🏥")

    now = datetime.utcnow()

    if existing and existing.application_status == "rejected":
        # 重新申请: 更新现有租户
        existing.brand_name = data.brand_name
        existing.brand_tagline = data.brand_tagline
        existing.brand_avatar = brand_avatar
        existing.brand_colors = brand_colors
        existing.brand_theme_id = brand_theme
        existing.expert_title = data.expert_title
        existing.expert_self_intro = data.expert_self_intro
        existing.expert_specialties = data.expert_specialties
        existing.expert_credentials = data.expert_credentials
        existing.enabled_agents = agents
        existing.welcome_message = data.welcome_message
        existing.service_packages = data.service_packages
        existing.status = TenantStatus.pending_review
        existing.application_status = "pending_review"
        existing.application_data = _build_application_data(data, agents)
        _sync_user_profile(current_user, data)
        existing.applied_at = now
        existing.updated_at = now
        tenant_id = existing.id

        db.commit()
        return {
            "success": True,
            "data": {
                "tenant_id": tenant_id,
                "status": "pending_review",
                "message": "申请已重新提交，请等待审核",
            },
        }

    # 5. 生成 tenant_id
    tenant_id = _generate_tenant_id(data.brand_name, current_user.id, db)

    # 6. 创建 ExpertTenant
    tenant = ExpertTenant(
        id=tenant_id,
        expert_user_id=current_user.id,
        brand_name=data.brand_name,
        brand_tagline=data.brand_tagline,
        brand_avatar=brand_avatar,
        brand_colors=brand_colors,
        brand_theme_id=brand_theme,
        expert_title=data.expert_title,
        expert_self_intro=data.expert_self_intro,
        expert_specialties=data.expert_specialties,
        expert_credentials=data.expert_credentials,
        enabled_agents=agents,
        welcome_message=data.welcome_message,
        service_packages=data.service_packages,
        status=TenantStatus.pending_review,
        tier=TenantTier.basic,
        application_status="pending_review",
        application_data=_build_application_data(data, agents),
        applied_at=now,
    )
    db.add(tenant)
    db.flush()

    _sync_user_profile(current_user, data)

    # 7. 创建 TenantAgentMapping
    for i, agent_id in enumerate(agents):
        mapping = TenantAgentMapping(
            tenant_id=tenant_id,
            agent_id=agent_id,
            display_name="",
            is_enabled=True,
            is_primary=(i == 0),
            sort_order=i,
            created_at=now,
        )
        db.add(mapping)

    db.commit()

    logger.info("专家入驻申请: user=%d, tenant=%s, domain=%s", current_user.id, tenant_id, data.domain_id)

    return {
        "success": True,
        "data": {
            "tenant_id": tenant_id,
            "status": "pending_review",
            "message": "申请已提交，请等待平台审核 (1-3 个工作日)",
        },
    }


@router.get("/my-application")
def get_my_application(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查询当前用户的入驻申请状态"""
    tenant = db.query(ExpertTenant).filter(
        ExpertTenant.expert_user_id == current_user.id,
    ).first()

    if not tenant:
        return {"success": True, "data": None}

    return {
        "success": True,
        "data": {
            "tenant_id": tenant.id,
            "brand_name": tenant.brand_name,
            "brand_avatar": tenant.brand_avatar,
            "brand_colors": tenant.brand_colors,
            "expert_title": tenant.expert_title,
            "status": tenant.status.value if tenant.status else None,
            "application_status": tenant.application_status,
            "application_data": tenant.application_data or {},
            "applied_at": tenant.applied_at.isoformat() if tenant.applied_at else None,
            "created_at": tenant.created_at.isoformat() if tenant.created_at else None,
        },
    }


@router.put("/my-application")
def update_my_application(
    data: ApplicationUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """修改入驻申请 (仅 pending_review 可改)"""
    tenant = db.query(ExpertTenant).filter(
        ExpertTenant.expert_user_id == current_user.id,
    ).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="未找到申请记录")
    if tenant.application_status != "pending_review":
        raise HTTPException(status_code=400, detail=f"当前状态 ({tenant.application_status}) 不可修改")

    update_data = data.dict(exclude_unset=True)

    # 处理领域变更
    if "domain_id" in update_data:
        domain = _get_domain_by_id(update_data["domain_id"])
        if not domain:
            raise HTTPException(status_code=400, detail=f"无效领域: {update_data['domain_id']}")

    # 更新 tenant 字段
    field_mapping = {
        "brand_name": "brand_name",
        "brand_tagline": "brand_tagline",
        "brand_avatar": "brand_avatar",
        "expert_title": "expert_title",
        "expert_self_intro": "expert_self_intro",
        "expert_specialties": "expert_specialties",
        "expert_credentials": "expert_credentials",
        "welcome_message": "welcome_message",
    }
    for req_field, model_field in field_mapping.items():
        if req_field in update_data and update_data[req_field] is not None:
            setattr(tenant, model_field, update_data[req_field])

    # 更新 Agent 列表
    if "selected_agents" in update_data and update_data["selected_agents"]:
        agents = update_data["selected_agents"]
        if "crisis" not in agents:
            agents.append("crisis")
        tenant.enabled_agents = agents

    # 同步 application_data
    app_data = tenant.application_data or {}
    app_data.update({k: v for k, v in update_data.items() if v is not None})
    tenant.application_data = app_data
    tenant.updated_at = datetime.utcnow()

    db.commit()
    return {"success": True, "message": "申请已更新"}


# ── Admin 端点 ──

@router.get("/admin/applications")
def list_applications(
    status: Optional[str] = Query(None, description="pending_review/approved/rejected"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """列出专家入驻申请"""
    q = db.query(ExpertTenant).filter(
        ExpertTenant.application_status.isnot(None),
    )
    if status:
        q = q.filter(ExpertTenant.application_status == status)

    total = q.count()
    items = q.order_by(ExpertTenant.applied_at.desc()).offset(skip).limit(limit).all()

    return {
        "success": True,
        "data": {
            "items": [_application_summary(t) for t in items],
            "total": total,
        },
    }


@router.get("/admin/applications/{tenant_id}")
def get_application_detail(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """查看申请详情"""
    tenant = db.query(ExpertTenant).filter(ExpertTenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="申请不存在")

    # 获取申请人信息
    applicant = db.query(User).filter(User.id == tenant.expert_user_id).first()

    return {
        "success": True,
        "data": {
            **_application_summary(tenant),
            "application_data": tenant.application_data or {},
            "expert_self_intro": tenant.expert_self_intro,
            "enabled_agents": tenant.enabled_agents or [],
            "service_packages": tenant.service_packages or [],
            "welcome_message": tenant.welcome_message,
            "applicant": {
                "id": applicant.id,
                "username": applicant.username,
                "full_name": applicant.full_name if hasattr(applicant, 'full_name') else None,
                "email": applicant.email,
                "role": applicant.role.value,
            } if applicant else None,
        },
    }


@router.post("/admin/applications/{tenant_id}/approve")
def approve_application(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """审核通过入驻申请"""
    tenant = db.query(ExpertTenant).filter(ExpertTenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="申请不存在")
    if tenant.application_status != "pending_review":
        raise HTTPException(status_code=400, detail=f"当前状态 ({tenant.application_status}) 不可审核")

    # 1. 更新租户状态
    tenant.status = TenantStatus.trial
    tenant.application_status = "approved"
    tenant.updated_at = datetime.utcnow()

    # 2. 升级用户角色
    applicant = db.query(User).filter(User.id == tenant.expert_user_id).first()
    if applicant:
        user_level = ROLE_LEVEL.get(applicant.role, 0)
        coach_level = ROLE_LEVEL.get(UserRole.COACH, 4)
        if user_level < coach_level:
            applicant.role = UserRole.COACH
            logger.info("用户角色升级: user=%d, %s -> COACH", applicant.id, applicant.role.value)

    # 3. 审计日志
    db.add(TenantAuditLog(
        tenant_id=tenant_id,
        actor_id=current_user.id,
        action="application_approved",
        detail={"approved_by": current_user.id},
        created_at=datetime.utcnow(),
    ))

    db.commit()

    # 4. 清缓存: 重置 v6 MasterAgent
    try:
        from api.main import reset_agent_master
        reset_agent_master()
    except Exception:
        pass

    logger.info("专家入驻审核通过: tenant=%s, approved_by=%d", tenant_id, current_user.id)

    return {
        "success": True,
        "message": "审核通过，工作室已开通",
        "data": {
            "tenant_id": tenant_id,
            "status": "trial",
            "role_upgraded": True if applicant and ROLE_LEVEL.get(applicant.role, 0) >= ROLE_LEVEL.get(UserRole.COACH, 4) else False,
        },
    }


@router.post("/admin/applications/{tenant_id}/reject")
def reject_application(
    tenant_id: str,
    data: RejectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """审核拒绝入驻申请"""
    tenant = db.query(ExpertTenant).filter(ExpertTenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="申请不存在")
    if tenant.application_status != "pending_review":
        raise HTTPException(status_code=400, detail=f"当前状态 ({tenant.application_status}) 不可审核")

    # 更新状态
    tenant.application_status = "rejected"
    app_data = tenant.application_data or {}
    app_data["reject_reason"] = data.reason
    app_data["rejected_by"] = current_user.id
    app_data["rejected_at"] = datetime.utcnow().isoformat()
    tenant.application_data = app_data
    tenant.updated_at = datetime.utcnow()
    # status 保持 pending_review, 允许重新申请

    # 审计日志
    db.add(TenantAuditLog(
        tenant_id=tenant_id,
        actor_id=current_user.id,
        action="application_rejected",
        detail={"reason": data.reason},
        created_at=datetime.utcnow(),
    ))

    db.commit()

    logger.info("专家入驻审核拒绝: tenant=%s, reason=%s", tenant_id, data.reason)

    return {
        "success": True,
        "message": "已拒绝申请",
        "data": {"tenant_id": tenant_id, "reason": data.reason},
    }


# ── 辅助函数 ──

def _application_summary(t: ExpertTenant) -> dict:
    return {
        "tenant_id": t.id,
        "brand_name": t.brand_name,
        "brand_avatar": t.brand_avatar,
        "brand_colors": t.brand_colors,
        "expert_title": t.expert_title,
        "expert_specialties": t.expert_specialties or [],
        "expert_credentials": t.expert_credentials or [],
        "application_status": t.application_status,
        "applied_at": t.applied_at.isoformat() if t.applied_at else None,
        "domain_id": (t.application_data or {}).get("domain_id"),
        "reject_reason": (t.application_data or {}).get("reject_reason"),
    }
