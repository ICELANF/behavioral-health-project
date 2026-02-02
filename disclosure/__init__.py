"""
行为健康数字平台 - 披露控制模块
Disclosure Control Module

[v14.1-NEW] 全新模块

核心理念："黑盒评估，白盒干预"

四级权限架构：
┌─────────────────────────────────────────────────────────────┐
│  第一层：患者端 — 只参与，不知晓                              │
│  - 做：完成问卷、日常打卡、健康数据采集                        │
│  - 看：正向激励信息，不出现分类标签                           │
│  - 不看：行为阶段、风险等级、人格分型等敏感评估结果             │
├─────────────────────────────────────────────────────────────┤
│  第二层：教练端 — 看到结果，执行干预                          │
│  - 看：学员的行为阶段、风险等级、评估报告摘要                  │
│  - 做：根据评估结果选择干预策略，审核AI建议后推送               │
├─────────────────────────────────────────────────────────────┤
│  第三层：专家/督导端 — 审核确认                               │
│  - 看：完整评估报告（含量表原始分、AI分析）                    │
│  - 做：审核评估结果、标注是否可向患者披露、处理敏感案例上报      │
├─────────────────────────────────────────────────────────────┤
│  第四层：管理员端 — 系统配置                                  │
│  - 做：配置评估量表、设置披露规则、查看整体统计                 │
│  - 不看：个人敏感数据（脱敏后的统计数据除外）                  │
└─────────────────────────────────────────────────────────────┘

模块组成：
- blacklist: 敏感词库管理
- signature: 双重签名机制
- controller: 披露控制器
- rewriter: AI文案重写器
- permissions: 四级权限管理
- display_adapter: 评估结果展示适配器

使用方式：
    from disclosure import (
        # 权限管理
        get_permission_manager,
        PermissionLevel,
        DataCategory,
        
        # 展示适配
        get_display_adapter,
        PatientDataFilter,
        CoachDataView,
        
        # 披露控制
        get_disclosure_controller,
        get_blacklist_manager,
        get_signature_manager,
        get_ai_rewriter,
    )
    
    # 根据权限过滤数据
    adapter = get_display_adapter()
    display = adapter.adapt(assessment_data, viewer_id, PermissionLevel.PATIENT)
"""

# 禁词库
from disclosure.blacklist import (
    BlacklistCategory,
    SensitivityLevel,
    BlacklistWord,
    BlacklistManager,
    get_blacklist_manager,
    DEFAULT_BLACKLIST
)

# 双重签名
from disclosure.signature import (
    SignatureRole,
    SignatureStatus,
    RiskLevel,
    Signature,
    DualSignatureRequest,
    DualSignatureManager,
    get_signature_manager,
    get_signature_rule,
    SIGNATURE_RULES
)

# 披露控制器
from disclosure.controller import (
    DisclosureLevel,
    ViewerRole,
    ReportChapter,
    DisclosureDecision,
    DisclosureController,
    get_disclosure_controller,
    DEFAULT_CHAPTERS
)

# AI重写器
from disclosure.rewriter import (
    AIRewriter,
    RewriteResult,
    get_ai_rewriter,
    get_positive_feedback,
    BIG5_REWRITES,
    TTM_REWRITES,
    BPT6_REWRITES,
    POSITIVE_FEEDBACK_TEMPLATES
)

# 四级权限管理
from disclosure.permissions import (
    PermissionLevel,
    DataCategory,
    ActionType,
    UserPermission,
    PermissionManager,
    get_permission_manager,
    PatientDataFilter,
    CoachDataView,
    VIEW_PERMISSIONS,
    ACTION_PERMISSIONS
)

# 展示适配器
from disclosure.display_adapter import (
    AssessmentDisplay,
    AssessmentDisplayAdapter,
    get_display_adapter
)

__all__ = [
    # blacklist
    'BlacklistCategory',
    'SensitivityLevel',
    'BlacklistWord',
    'BlacklistManager',
    'get_blacklist_manager',
    'DEFAULT_BLACKLIST',
    
    # signature
    'SignatureRole',
    'SignatureStatus',
    'RiskLevel',
    'Signature',
    'DualSignatureRequest',
    'DualSignatureManager',
    'get_signature_manager',
    'get_signature_rule',
    'SIGNATURE_RULES',
    
    # controller
    'DisclosureLevel',
    'ViewerRole',
    'ReportChapter',
    'DisclosureDecision',
    'DisclosureController',
    'get_disclosure_controller',
    'DEFAULT_CHAPTERS',
    
    # rewriter
    'AIRewriter',
    'RewriteResult',
    'get_ai_rewriter',
    'get_positive_feedback',
    'BIG5_REWRITES',
    'TTM_REWRITES',
    'BPT6_REWRITES',
    'POSITIVE_FEEDBACK_TEMPLATES',
    
    # permissions
    'PermissionLevel',
    'DataCategory',
    'ActionType',
    'UserPermission',
    'PermissionManager',
    'get_permission_manager',
    'PatientDataFilter',
    'CoachDataView',
    'VIEW_PERMISSIONS',
    'ACTION_PERMISSIONS',
    
    # display_adapter
    'AssessmentDisplay',
    'AssessmentDisplayAdapter',
    'get_display_adapter',
]

__version__ = "14.1.0"
