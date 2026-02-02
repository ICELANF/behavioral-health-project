#!/usr/bin/env python3
"""
行为健康数字平台 - 专家审核工作台
Expert Review Workbench (Streamlit UI)

[v14-NEW] 专家工作台模块

运行方式：
    streamlit run workbench/expert_review.py --server.port 8501

功能：
1. 待审核任务列表（风险导向排序）
2. 三栏审核界面（原始数据-AI建议-披露决策）
3. 实时敏感词检测（波浪线标记）
4. 双重签名机制
5. 章节可见性控制

界面布局：
┌─────────────────────────────────────────────────────────────┐
│  侧边栏：任务队列 + 签名状态                                   │
├─────────────────────────┬───────────────────────────────────┤
│  专家侧（原始数据）       │  用户侧（脱敏预览）                 │
│  - BIG5 剖面图          │  - AI重写建议                      │
│  - 风险评估              │  - 实时波浪线检测                   │
│  - 专家备注              │  - 章节可见性开关                   │
└─────────────────────────┴───────────────────────────────────┘
"""
import streamlit as st
import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from datetime import datetime
from typing import Dict, List, Any, Optional

# 导入披露控制模块
try:
    from disclosure import (
        get_blacklist_manager,
        get_disclosure_controller,
        get_ai_rewriter,
        get_signature_manager,
        ViewerRole,
        DisclosureLevel,
        RiskLevel,
        SignatureRole,
        DEFAULT_CHAPTERS
    )
    DISCLOSURE_AVAILABLE = True
except ImportError as e:
    DISCLOSURE_AVAILABLE = False
    st.error(f"披露控制模块加载失败: {e}")


# ============================================
# 页面配置
# ============================================
st.set_page_config(
    layout="wide",
    page_title="BAPS 专家审核工作台",
    page_icon="🛡️",
    initial_sidebar_state="expanded"
)


# ============================================
# 模拟数据（实际应从数据库获取）
# ============================================

MOCK_PENDING_REVIEWS = [
    {
        "report_id": "RPT_8829",
        "user_id": 8829,
        "user_name": "张先生",
        "risk_level": "critical",
        "big5_summary": "高神经质 + 低尽责性",
        "ttm_stage": "前意向期",
        "bpt6_type": "矛盾型",
        "created_at": "2026-02-01 10:30",
        "expert_notes": "用户处于强烈抗拒阶段，N维度得分极高，有明显的焦虑倾向，执行力极差。",
        "raw_scores": {
            "N": 85, "E": 45, "O": 60, "A": 55, "C": 30
        }
    },
    {
        "report_id": "RPT_8830",
        "user_id": 8830,
        "user_name": "李女士",
        "risk_level": "high",
        "big5_summary": "高外向性 + 低开放性",
        "ttm_stage": "意向期",
        "bpt6_type": "情绪型",
        "created_at": "2026-02-01 11:15",
        "expert_notes": "情绪波动明显，需要共情支持。",
        "raw_scores": {
            "N": 65, "E": 80, "O": 35, "A": 70, "C": 50
        }
    },
    {
        "report_id": "RPT_8831",
        "user_id": 8831,
        "user_name": "王先生",
        "risk_level": "moderate",
        "big5_summary": "均衡型",
        "ttm_stage": "准备期",
        "bpt6_type": "执行型",
        "created_at": "2026-02-01 12:00",
        "expert_notes": "状态良好，可以开始行动计划。",
        "raw_scores": {
            "N": 50, "E": 55, "O": 60, "A": 55, "C": 65
        }
    }
]


def get_risk_color(risk_level: str) -> str:
    """获取风险等级颜色"""
    colors = {
        "critical": "#FF0000",
        "high": "#FF8C00",
        "moderate": "#FFD700",
        "low": "#32CD32"
    }
    return colors.get(risk_level, "#808080")


def get_risk_emoji(risk_level: str) -> str:
    """获取风险等级emoji"""
    emojis = {
        "critical": "🔴",
        "high": "🟠",
        "moderate": "🟡",
        "low": "🟢"
    }
    return emojis.get(risk_level, "⚪")


# ============================================
# 侧边栏：任务队列
# ============================================

with st.sidebar:
    st.header("📋 任务队列")
    
    # 筛选
    risk_filter = st.selectbox(
        "风险等级筛选",
        ["全部", "危急(CRITICAL)", "高(HIGH)", "中(MODERATE)", "低(LOW)"]
    )
    
    st.write("---")
    
    # 任务列表
    for review in MOCK_PENDING_REVIEWS:
        risk_emoji = get_risk_emoji(review["risk_level"])
        
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button(
                f"{risk_emoji} {review['user_name']}",
                key=f"btn_{review['report_id']}",
                use_container_width=True
            ):
                st.session_state.selected_report = review
        with col2:
            st.caption(review["created_at"].split(" ")[1])
    
    st.write("---")
    
    # 签名状态
    st.subheader("🔒 双重签名状态")
    sig1 = st.checkbox("第一负责人 (主审专家) 签名", key="sig1")
    sig2 = st.checkbox("第二负责人 (督导专家) 签名", key="sig2")
    
    if sig1 and sig2:
        st.success("✅ 双重签名已完成")
    elif sig1:
        st.warning("⏳ 等待督导签名")
    else:
        st.info("⏳ 等待主审签名")


# ============================================
# 主界面
# ============================================

st.title("🛡️ BAPS 专家审核工作台")

# 获取当前选中的报告
if "selected_report" not in st.session_state:
    st.session_state.selected_report = MOCK_PENDING_REVIEWS[0]

current_review = st.session_state.selected_report

# 顶部信息栏
col_info1, col_info2, col_info3, col_info4 = st.columns(4)
with col_info1:
    st.metric("用户", current_review["user_name"])
with col_info2:
    risk_color = get_risk_color(current_review["risk_level"])
    st.markdown(f"**风险等级**: <span style='color:{risk_color}'>{current_review['risk_level'].upper()}</span>", 
                unsafe_allow_html=True)
with col_info3:
    st.metric("TTM阶段", current_review["ttm_stage"])
with col_info4:
    st.metric("行为模式", current_review["bpt6_type"])

st.write("---")

# ============================================
# 三栏布局
# ============================================

col_left, col_right = st.columns(2)

# 左栏：专家侧全量数据
with col_left:
    st.subheader("🩸 专家侧全量版 (原始数据)")
    st.error("⚠️ 以下内容仅限专业人员可见，严禁直接展示给用户")
    
    # BIG5 剖面图
    st.write("**大五人格剖面：**")
    scores = current_review["raw_scores"]
    
    # 简单的条形图展示
    for dim, score in scores.items():
        dim_name = {"N": "神经质", "E": "外向性", "O": "开放性", "A": "宜人性", "C": "尽责性"}[dim]
        bar_color = "red" if (dim == "N" and score > 70) or (dim == "C" and score < 40) else "blue"
        st.progress(score / 100, text=f"{dim_name}({dim}): {score}")
    
    # 原始评估数据
    st.write("**原始评估：**")
    st.json({
        "combination": current_review["big5_summary"],
        "risk_level": current_review["risk_level"],
        "stage": current_review["ttm_stage"],
        "type": current_review["bpt6_type"]
    })
    
    # 专家备注
    st.write("**核心风险评估：**")
    st.warning(current_review["expert_notes"])

# 右栏：用户侧脱敏版
with col_right:
    st.subheader("☀️ 用户侧脱敏版 (AI & 手动编辑)")
    
    # AI重写建议
    if DISCLOSURE_AVAILABLE:
        rewriter = get_ai_rewriter()
        ai_suggestion = rewriter.rewrite_assessment_summary(
            big5_summary=current_review["big5_summary"],
            ttm_stage=current_review["ttm_stage"],
            bpt6_type=current_review["bpt6_type"],
            risk_level=current_review["risk_level"]
        )
    else:
        ai_suggestion = "你是一个情感敏锐且富有创意的人。目前的你正在审视改变的意义。我们建议先从小事做起，比如每天喝一杯水这样简单的习惯开始，好吗？"
    
    # 专家编辑区
    user_content = st.text_area(
        "编辑发送给用户的文字：",
        value=ai_suggestion,
        height=250,
        key="user_content"
    )
    
    # 实时敏感词检测
    st.write("**实时预览（用户端视角）：**")
    
    if DISCLOSURE_AVAILABLE:
        blacklist = get_blacklist_manager()
        preview_html = blacklist.highlight_html(user_content)
        has_sensitive = blacklist.contains_sensitive(user_content)
    else:
        # 简化版检测
        sensitive_words = ["神经质", "低尽责性", "抗拒", "失败", "障碍", "焦虑症"]
        preview_html = user_content
        has_sensitive = False
        for word in sensitive_words:
            if word in user_content:
                has_sensitive = True
                preview_html = preview_html.replace(
                    word,
                    f'<span style="text-decoration: underline wavy red; color: red;" title="禁词">{word}</span>'
                )
    
    st.markdown(
        f'<div style="border:1px solid #ddd; padding:15px; border-radius:5px; '
        f'background-color:#f9f9f9; min-height:150px;">{preview_html}</div>',
        unsafe_allow_html=True
    )
    
    if has_sensitive:
        st.error("⚠️ 内容中仍包含敏感词（红色波浪线部分），请修正后再发布")
    else:
        st.success("✅ 内容已脱敏，可以发布")

st.write("---")

# ============================================
# 章节可见性控制
# ============================================

st.subheader("📋 章节可见性控制")

# 将17个章节分成3列展示
chapters_per_col = 6
chapter_cols = st.columns(3)

chapter_visibility = {}
for i, chapter in enumerate(DEFAULT_CHAPTERS if DISCLOSURE_AVAILABLE else []):
    col_idx = i // chapter_cols.__len__()
    with chapter_cols[col_idx % 3]:
        # 默认：敏感章节对患者不可见
        default_visible = chapter.default_visibility.get(ViewerRole.PATIENT, False) if DISCLOSURE_AVAILABLE else False
        chapter_visibility[chapter.chapter_id] = st.checkbox(
            f"{chapter.name}",
            value=default_visible,
            key=f"chap_{chapter.chapter_id}",
            help=chapter.description if DISCLOSURE_AVAILABLE else ""
        )

st.write("---")

# ============================================
# 发布控制
# ============================================

col_action1, col_action2, col_action3 = st.columns([2, 2, 1])

with col_action1:
    disclosure_level = st.selectbox(
        "披露等级",
        ["有条件披露", "全量披露", "最小披露", "暂不披露"],
        index=0
    )

with col_action2:
    review_notes = st.text_input("审核备注", placeholder="可选：填写审核意见")

with col_action3:
    st.write("")  # 占位

# 发布按钮
sig1 = st.session_state.get("sig1", False)
sig2 = st.session_state.get("sig2", False)

if sig1 and sig2:
    if has_sensitive:
        st.error("❌ 无法发布：内容中仍包含禁词，请修正后再试。")
        st.button("发布报告", disabled=True)
    else:
        if st.button("✅ 双重签名确认：正式发布报告", type="primary", use_container_width=True):
            st.balloons()
            st.success(f"🎉 报告 {current_review['report_id']} 已加密释放至用户端！")
            st.info(f"披露等级: {disclosure_level} | 审核人备注: {review_notes or '无'}")
else:
    st.button(
        "发布报告（需完成双重签名）",
        disabled=True,
        use_container_width=True,
        help="需要完成双重电子签名后方可发布"
    )

# ============================================
# 页脚
# ============================================

st.write("---")
st.caption(f"BAPS 专家审核工作台 v14 | 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
