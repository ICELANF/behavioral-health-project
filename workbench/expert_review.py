#!/usr/bin/env python3
"""
行为健康数字平台 - 专家审核工作台
Expert Review Workbench (Streamlit UI)

[v15] 真实API集成 + 完整disclosure模块

功能：
1. 待审核任务列表（从API获取，风险导向排序）
2. 三栏审核界面（原始数据-AI建议-披露决策）
3. 实时敏感词检测（波浪线标记）
4. 双重签名机制
5. 章节可见性控制
6. 真实审核/推送操作
"""
import streamlit as st
import sys
import os
import requests

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from datetime import datetime
from typing import Dict, List, Any, Optional

# ── API配置 ──
API_BASE = os.environ.get("BHP_API_URL", "http://bhp-api:8000")

# ── 导入披露控制模块 ──
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
# API 客户端
# ============================================

def api_login(username: str, password: str) -> Optional[dict]:
    """登录获取token"""
    try:
        resp = requests.post(
            f"{API_BASE}/api/v1/auth/login",
            data={"username": username, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def api_get(path: str, token: str) -> Optional[dict]:
    """带认证的GET请求"""
    try:
        resp = requests.get(
            f"{API_BASE}{path}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def api_put(path: str, token: str, data: dict) -> Optional[dict]:
    """带认证的PUT请求"""
    try:
        resp = requests.put(
            f"{API_BASE}{path}",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=data,
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def api_post(path: str, token: str, data: dict = None) -> Optional[dict]:
    """带认证的POST请求"""
    try:
        resp = requests.post(
            f"{API_BASE}{path}",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=data or {},
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


# ============================================
# 从API获取审核任务
# ============================================

def fetch_review_list(token: str) -> List[dict]:
    """从API获取待审核列表"""
    data = api_get("/api/v1/assessment-assignments/review-list", token)
    if data and "assignments" in data:
        return data["assignments"]
    return []


def fetch_behavioral_profile(user_id: int, token: str) -> Optional[dict]:
    """获取用户行为画像"""
    return api_get(f"/api/v1/assessment/profile/{user_id}", token)


def fetch_students(token: str) -> List[dict]:
    """获取教练学员列表"""
    data = api_get("/api/v1/coach/students", token)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "students" in data:
        return data["students"]
    return []


def build_review_item(assignment: dict, profile: Optional[dict] = None) -> dict:
    """从API数据构建审核条目"""
    pipeline = assignment.get("pipeline_result") or {}
    big5 = pipeline.get("big5_scores") or pipeline.get("personality") or {}
    ttm = pipeline.get("ttm_stage") or pipeline.get("stage") or "未知"
    bpt = pipeline.get("bpt6_type") or pipeline.get("behavior_type") or "未知"
    risk = pipeline.get("risk_level") or "moderate"
    notes = pipeline.get("expert_notes") or pipeline.get("summary") or assignment.get("note") or ""

    raw_scores = {}
    for dim in ["N", "E", "O", "A", "C"]:
        val = big5.get(dim) or big5.get(dim.lower()) or big5.get(
            {"N": "neuroticism", "E": "extraversion", "O": "openness",
             "A": "agreeableness", "C": "conscientiousness"}.get(dim, ""), 0
        )
        raw_scores[dim] = int(val) if val else 50

    # 如果pipeline没有BIG5，尝试从profile获取
    if profile and all(v == 50 for v in raw_scores.values()):
        p_scores = (profile.get("big5_scores") or profile.get("personality_scores") or {})
        for dim in ["N", "E", "O", "A", "C"]:
            if dim in p_scores:
                raw_scores[dim] = int(p_scores[dim])

    # 生成BIG5摘要
    high_dims = [d for d, v in raw_scores.items() if v >= 70]
    low_dims = [d for d, v in raw_scores.items() if v <= 35]
    dim_cn = {"N": "神经质", "E": "外向性", "O": "开放性", "A": "宜人性", "C": "尽责性"}
    parts = [f"高{dim_cn[d]}" for d in high_dims] + [f"低{dim_cn[d]}" for d in low_dims]
    big5_summary = " + ".join(parts) if parts else "均衡型"

    return {
        "report_id": f"ASN_{assignment.get('id', 0)}",
        "assignment_id": assignment.get("id"),
        "user_id": assignment.get("student_id"),
        "user_name": assignment.get("student_name", f"用户{assignment.get('student_id')}"),
        "risk_level": risk,
        "big5_summary": big5_summary,
        "ttm_stage": ttm if isinstance(ttm, str) else str(ttm),
        "bpt6_type": bpt if isinstance(bpt, str) else str(bpt),
        "created_at": assignment.get("completed_at") or assignment.get("created_at") or "",
        "expert_notes": notes,
        "raw_scores": raw_scores,
        "review_items": assignment.get("review_items", []),
        "pipeline_result": pipeline,
        "status": assignment.get("status", ""),
    }


# ============================================
# Mock数据（API无数据时降级）
# ============================================

MOCK_PENDING_REVIEWS = [
    {
        "report_id": "DEMO_001", "assignment_id": None,
        "user_id": 8829, "user_name": "张先生",
        "risk_level": "critical",
        "big5_summary": "高神经质 + 低尽责性",
        "ttm_stage": "前意向期", "bpt6_type": "矛盾型",
        "created_at": "2026-02-01 10:30",
        "expert_notes": "用户处于强烈抗拒阶段，N维度得分极高，有明显的焦虑倾向，执行力极差。",
        "raw_scores": {"N": 85, "E": 45, "O": 60, "A": 55, "C": 30},
        "review_items": [], "pipeline_result": {}, "status": "demo",
    },
    {
        "report_id": "DEMO_002", "assignment_id": None,
        "user_id": 8830, "user_name": "李女士",
        "risk_level": "high",
        "big5_summary": "高外向性 + 低开放性",
        "ttm_stage": "意向期", "bpt6_type": "情绪型",
        "created_at": "2026-02-01 11:15",
        "expert_notes": "情绪波动明显，需要共情支持。",
        "raw_scores": {"N": 65, "E": 80, "O": 35, "A": 70, "C": 50},
        "review_items": [], "pipeline_result": {}, "status": "demo",
    },
    {
        "report_id": "DEMO_003", "assignment_id": None,
        "user_id": 8831, "user_name": "王先生",
        "risk_level": "moderate",
        "big5_summary": "均衡型",
        "ttm_stage": "准备期", "bpt6_type": "执行型",
        "created_at": "2026-02-01 12:00",
        "expert_notes": "状态良好，可以开始行动计划。",
        "raw_scores": {"N": 50, "E": 55, "O": 60, "A": 55, "C": 65},
        "review_items": [], "pipeline_result": {}, "status": "demo",
    },
]


# ============================================
# 辅助函数
# ============================================

def get_risk_color(risk_level: str) -> str:
    return {"critical": "#FF0000", "high": "#FF8C00", "moderate": "#FFD700", "low": "#32CD32"}.get(risk_level, "#808080")

def get_risk_emoji(risk_level: str) -> str:
    return {"critical": "🔴", "high": "🟠", "moderate": "🟡", "low": "🟢"}.get(risk_level, "⚪")

RISK_ORDER = {"critical": 0, "high": 1, "moderate": 2, "low": 3}


# ============================================
# 侧边栏
# ============================================

with st.sidebar:
    # ── 登录区 ──
    st.header("🔐 专家登录")
    if "token" not in st.session_state:
        st.session_state.token = None
        st.session_state.user_info = None

    if not st.session_state.token:
        with st.form("login_form"):
            username = st.text_input("用户名", value="admin")
            password = st.text_input("密码", type="password", value="")
            submitted = st.form_submit_button("登录", use_container_width=True)
            if submitted and password:
                result = api_login(username, password)
                if result and "access_token" in result:
                    st.session_state.token = result["access_token"]
                    st.session_state.user_info = result.get("user", {})
                    st.rerun()
                else:
                    st.error("登录失败，请检查用户名和密码")
    else:
        user = st.session_state.user_info or {}
        st.success(f"✅ 已登录: {user.get('username', '?')} ({user.get('role', '?')})")
        if st.button("退出登录", use_container_width=True):
            st.session_state.token = None
            st.session_state.user_info = None
            st.session_state.pop("selected_report", None)
            st.session_state.pop("reviews", None)
            st.rerun()

    st.write("---")

    # ── 任务队列 ──
    st.header("📋 任务队列")

    # 获取数据
    data_source = "mock"
    if st.session_state.token:
        if "reviews" not in st.session_state or st.sidebar.button("🔄 刷新", use_container_width=True):
            raw_assignments = fetch_review_list(st.session_state.token)
            if raw_assignments:
                reviews = []
                for a in raw_assignments:
                    profile = fetch_behavioral_profile(a.get("student_id", 0), st.session_state.token)
                    reviews.append(build_review_item(a, profile))
                # 按风险排序
                reviews.sort(key=lambda r: RISK_ORDER.get(r["risk_level"], 9))
                st.session_state.reviews = reviews
                data_source = "api"
            else:
                st.session_state.reviews = MOCK_PENDING_REVIEWS
                data_source = "mock"
        else:
            data_source = "api" if st.session_state.reviews != MOCK_PENDING_REVIEWS else "mock"
    else:
        st.session_state.reviews = MOCK_PENDING_REVIEWS

    pending_reviews = st.session_state.get("reviews", MOCK_PENDING_REVIEWS)

    if data_source == "mock":
        st.caption("📌 演示模式 — 登录后加载真实数据")
    else:
        st.caption(f"📡 已连接API — {len(pending_reviews)} 条待审")

    # 筛选
    risk_filter = st.selectbox(
        "风险等级筛选",
        ["全部", "危急(CRITICAL)", "高(HIGH)", "中(MODERATE)", "低(LOW)"]
    )
    filter_map = {"危急(CRITICAL)": "critical", "高(HIGH)": "high", "中(MODERATE)": "moderate", "低(LOW)": "low"}
    if risk_filter != "全部":
        filtered = [r for r in pending_reviews if r["risk_level"] == filter_map.get(risk_filter)]
    else:
        filtered = pending_reviews

    st.write("---")

    for review in filtered:
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
            ts = review.get("created_at", "")
            st.caption(ts.split(" ")[1] if " " in ts else ts[:10] if ts else "")

    st.write("---")

    # ── 签名状态 ──
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

# 获取当前选中的报告
if "selected_report" not in st.session_state:
    st.session_state.selected_report = pending_reviews[0] if pending_reviews else MOCK_PENDING_REVIEWS[0]

current_review = st.session_state.selected_report

# ── 顶部信息栏 ──
col_info1, col_info2, col_info3, col_info4 = st.columns(4)
with col_info1:
    st.metric("用户", current_review["user_name"])
with col_info2:
    risk_color = get_risk_color(current_review["risk_level"])
    st.markdown(
        f"**风险等级**: <span style='color:{risk_color};font-size:1.2em;font-weight:bold'>"
        f"{current_review['risk_level'].upper()}</span>",
        unsafe_allow_html=True,
    )
with col_info3:
    st.metric("TTM阶段", current_review["ttm_stage"])
with col_info4:
    st.metric("行为模式", current_review["bpt6_type"])

st.write("---")

# ============================================
# 三栏布局
# ============================================

col_left, col_right = st.columns(2)

# ── 左栏：专家侧全量数据 ──
with col_left:
    st.subheader("🩸 专家侧全量版 (原始数据)")
    st.error("⚠️ 以下内容仅限专业人员可见，严禁直接展示给用户")

    # BIG5 剖面图
    st.write("**大五人格剖面：**")
    scores = current_review["raw_scores"]
    dim_names = {"N": "神经质", "E": "外向性", "O": "开放性", "A": "宜人性", "C": "尽责性"}
    for dim, score in scores.items():
        st.progress(score / 100, text=f"{dim_names[dim]}({dim}): {score}")

    # 原始评估数据
    st.write("**原始评估：**")
    st.json({
        "combination": current_review["big5_summary"],
        "risk_level": current_review["risk_level"],
        "stage": current_review["ttm_stage"],
        "type": current_review["bpt6_type"],
    })

    # 完整pipeline结果（如有）
    pipeline = current_review.get("pipeline_result", {})
    if pipeline:
        with st.expander("📊 完整评估管道结果 (JSON)", expanded=False):
            st.json(pipeline)

    # 专家备注
    st.write("**核心风险评估：**")
    st.warning(current_review["expert_notes"] or "暂无备注")

    # 审核条目（如有）
    review_items = current_review.get("review_items", [])
    if review_items:
        st.write("**干预方案审核：**")
        for item in review_items:
            cat_labels = {"goal": "🎯 目标", "prescription": "💊 处方", "suggestion": "💡 建议"}
            cat = cat_labels.get(item.get("category", ""), item.get("category", ""))
            status_labels = {"pending": "⏳待审", "approved": "✅已批", "modified": "✏️已改", "rejected": "❌已拒"}
            item_status = status_labels.get(item.get("status", ""), item.get("status", ""))
            domain = item.get("domain", "")
            content = item.get("original_content", {})
            if isinstance(content, dict):
                content_text = content.get("text") or content.get("description") or str(content)
            else:
                content_text = str(content)

            with st.expander(f"{cat} [{domain}] — {item_status}", expanded=item.get("status") == "pending"):
                st.write(content_text)
                if item.get("coach_content"):
                    st.info(f"教练修改: {item['coach_content']}")

                # 审核操作
                if item.get("status") == "pending" and st.session_state.token and item.get("id"):
                    action_cols = st.columns(3)
                    with action_cols[0]:
                        if st.button("✅ 批准", key=f"approve_{item['id']}"):
                            result = api_put(
                                f"/api/v1/assessment-assignments/review-items/{item['id']}",
                                st.session_state.token,
                                {"status": "approved"},
                            )
                            if result and result.get("success"):
                                st.success("已批准")
                                st.rerun()
                    with action_cols[1]:
                        if st.button("❌ 拒绝", key=f"reject_{item['id']}"):
                            result = api_put(
                                f"/api/v1/assessment-assignments/review-items/{item['id']}",
                                st.session_state.token,
                                {"status": "rejected", "coach_note": "专家审核拒绝"},
                            )
                            if result and result.get("success"):
                                st.warning("已拒绝")
                                st.rerun()


# ── 右栏：用户侧脱敏版 ──
with col_right:
    st.subheader("☀️ 用户侧脱敏版 (AI & 手动编辑)")

    # AI重写建议
    if DISCLOSURE_AVAILABLE:
        rewriter = get_ai_rewriter()
        ai_suggestion = rewriter.rewrite_assessment_summary(
            big5_summary=current_review["big5_summary"],
            ttm_stage=current_review["ttm_stage"],
            bpt6_type=current_review["bpt6_type"],
            risk_level=current_review["risk_level"],
        )
    else:
        ai_suggestion = (
            "你是一个情感敏锐且富有创意的人。目前的你正在审视改变的意义。"
            "我们建议先从小事做起，比如每天喝一杯水这样简单的习惯开始，好吗？"
        )

    user_content = st.text_area(
        "编辑发送给用户的文字：",
        value=ai_suggestion,
        height=250,
        key="user_content",
    )

    # 实时敏感词检测
    st.write("**实时预览（用户端视角）：**")

    if DISCLOSURE_AVAILABLE:
        blacklist = get_blacklist_manager()
        preview_html = blacklist.highlight_html(user_content)
        has_sensitive = blacklist.contains_sensitive(user_content)
    else:
        sensitive_words = ["神经质", "低尽责性", "抗拒", "失败", "障碍", "焦虑症", "抑郁", "人格", "缺陷"]
        preview_html = user_content
        has_sensitive = False
        for word in sensitive_words:
            if word in user_content:
                has_sensitive = True
                preview_html = preview_html.replace(
                    word,
                    f'<span style="text-decoration: underline wavy red; color: red;" title="禁词">{word}</span>',
                )

    st.markdown(
        f'<div style="border:1px solid #ddd; padding:15px; border-radius:8px; '
        f'background-color:{"#fff5f5" if has_sensitive else "#f0fff4"}; min-height:150px;">'
        f'{preview_html}</div>',
        unsafe_allow_html=True,
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

if DISCLOSURE_AVAILABLE and DEFAULT_CHAPTERS:
    chapter_cols = st.columns(3)
    chapter_visibility = {}
    for i, chapter in enumerate(DEFAULT_CHAPTERS):
        with chapter_cols[i % 3]:
            default_visible = chapter.default_visibility.get(ViewerRole.PATIENT, False)
            chapter_visibility[chapter.chapter_id] = st.checkbox(
                f"{chapter.name}",
                value=default_visible,
                key=f"chap_{chapter.chapter_id}",
                help=chapter.description,
            )
else:
    # Disclosure模块不可用时显示默认章节
    default_chapters = [
        ("基本信息", True), ("健康目标", True), ("行动计划", True),
        ("日常建议", True), ("进步记录", True), ("激励反馈", True),
        ("大五人格详情", False), ("风险等级评估", False), ("TTM阶段分析", False),
        ("行为模式分型", False), ("原始量表得分", False), ("临床建议", False),
        ("危机预警指标", False), ("专家内部备注", False), ("干预处方详情", False),
        ("教练督导记录", False), ("数据溯源日志", False),
    ]
    chapter_cols = st.columns(3)
    chapter_visibility = {}
    for i, (name, default) in enumerate(default_chapters):
        with chapter_cols[i % 3]:
            chapter_visibility[name] = st.checkbox(name, value=default, key=f"chap_{i}")

st.write("---")

# ============================================
# 发布控制
# ============================================

col_action1, col_action2, col_action3 = st.columns([2, 2, 1])

with col_action1:
    disclosure_level = st.selectbox(
        "披露等级",
        ["有条件披露", "全量披露", "最小披露", "暂不披露"],
        index=0,
    )

with col_action2:
    review_notes = st.text_input("审核备注", placeholder="可选：填写审核意见")

with col_action3:
    st.write("")

# 发布按钮
sig1 = st.session_state.get("sig1", False)
sig2 = st.session_state.get("sig2", False)

if sig1 and sig2:
    if has_sensitive:
        st.error("❌ 无法发布：内容中仍包含禁词，请修正后再试。")
        st.button("发布报告", disabled=True)
    else:
        if st.button("✅ 双重签名确认：正式发布报告", type="primary", use_container_width=True):
            assignment_id = current_review.get("assignment_id")
            published = False
            if assignment_id and st.session_state.token:
                result = api_post(
                    f"/api/v1/assessment-assignments/{assignment_id}/push",
                    st.session_state.token,
                )
                if result and result.get("success"):
                    published = True
                    st.balloons()
                    st.success(f"🎉 报告已通过API推送至用户端！{result.get('message', '')}")
                else:
                    st.warning("API推送失败，请检查审核条目是否已全部处理")
            if not published:
                st.balloons()
                st.success(f"🎉 报告 {current_review['report_id']} 已标记为发布（演示模式）")
            st.info(f"披露等级: {disclosure_level} | 审核人备注: {review_notes or '无'}")
else:
    st.button(
        "发布报告（需完成双重签名）",
        disabled=True,
        use_container_width=True,
        help="需要完成双重电子签名后方可发布",
    )

# ============================================
# 模块状态
# ============================================

st.write("---")
status_cols = st.columns(4)
with status_cols[0]:
    if DISCLOSURE_AVAILABLE:
        st.caption("🟢 Disclosure 模块已加载")
    else:
        st.caption("🔴 Disclosure 模块未加载")
with status_cols[1]:
    st.caption(f"{'🟢' if st.session_state.token else '🔴'} API 连接")
with status_cols[2]:
    st.caption(f"📋 {len(pending_reviews)} 条待审")
with status_cols[3]:
    st.caption(f"BAPS 专家审核工作台 v15 | {datetime.now().strftime('%H:%M:%S')}")
