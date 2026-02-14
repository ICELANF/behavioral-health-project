"""
BehaviorOS V4.0 — pytest 共享 Fixtures
提供: 内存DB会话、7种角色测试用户、工厂函数、mock LLM
覆盖: User / JourneyState / DualTrackStatus / AntiCheatEvent /
      GovernanceViolation / SafetyLog / BehavioralProfile
"""
import os, sys, enum
import pytest
from datetime import datetime, date, timedelta
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# =====================================================================
# 宽容模型导入 (缺失模型不阻塞套件)
# =====================================================================

_MODELS = {}

def _try_import(name):
    try:
        mod = getattr(__import__("core.models", fromlist=[name]), name)
        _MODELS[name] = mod
        return mod
    except (ImportError, AttributeError):
        return None

Base                 = _try_import("Base")
User                 = _try_import("User")
UserRole             = _try_import("UserRole")
JourneyStageV4       = _try_import("JourneyStageV4")
AgencyMode           = _try_import("AgencyMode")
JourneyState         = _try_import("JourneyState")
BehavioralProfile    = _try_import("BehavioralProfile")
DualTrackStatus      = _try_import("DualTrackStatus")
AntiCheatEvent       = _try_import("AntiCheatEvent")
GovernanceViolation  = _try_import("GovernanceViolation")
SafetyLog            = _try_import("SafetyLog")
StageTransitionLogV4 = _try_import("StageTransitionLogV4")
TrustScoreLog        = _try_import("TrustScoreLog")
AgencyScoreLog       = _try_import("AgencyScoreLog")
ChatSession          = _try_import("ChatSession")
ChatMessage          = _try_import("ChatMessage")
MicroActionTask      = _try_import("MicroActionTask")
AssessmentAssignment = _try_import("AssessmentAssignment")
ResponsibilityMetric = _try_import("ResponsibilityMetric")

# =====================================================================
# 数据库
# =====================================================================

@pytest.fixture(scope="session")
def engine():
    eng = create_engine("sqlite:///:memory:", echo=False)
    # Register now() for SQLite (server_default=func.now() generates now()
    # in RETURNING clause which SQLite doesn't support natively)
    from sqlalchemy import event
    @event.listens_for(eng, "connect")
    def _register_sqlite_now(dbapi_conn, connection_record):
        dbapi_conn.create_function(
            "now", 0, lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
    # Force a connect so the function is registered before table creation
    with eng.connect() as _:
        pass
    if Base:
        Base.metadata.create_all(eng)
    # Also create v3 tables (used by core/incentive_integration.py PointEngine)
    try:
        from v3.database import Base as V3Base
        from sqlalchemy import Table
        # Reflect 'users' table from DB into v3 metadata so FKs resolve
        if "users" not in V3Base.metadata.tables:
            Table("users", V3Base.metadata, autoload_with=eng)
        V3Base.metadata.create_all(eng, checkfirst=True)
    except Exception:
        pass
    return eng

@pytest.fixture
def db(engine) -> Session:
    conn = engine.connect()
    txn = conn.begin()
    session = sessionmaker(bind=conn)()
    yield session
    session.close()
    txn.rollback()
    conn.close()

# =====================================================================
# 用户工厂 + 7 角色 Fixtures
# =====================================================================

class UserFactory:
    _counter = 0

    @classmethod
    def create(cls, db: Session, role=None, **kw):
        if role is None:
            role = UserRole.GROWER
        cls._counter += 1
        rv = getattr(role, "value", str(role))
        defaults = dict(
            username=f"test_{rv}_{cls._counter}",
            email=f"test{cls._counter}@bhp.test",
            full_name=f"Test {cls._counter}",
            password_hash="$2b$12$fakehashfortest",
            role=role, is_active=True,
        )
        defaults.update(kw)
        user = User(**defaults)
        db.add(user); db.flush()
        return user

@pytest.fixture
def user_factory():
    return UserFactory

@pytest.fixture
def observer(db):  return UserFactory.create(db, UserRole.OBSERVER)
@pytest.fixture
def grower(db):    return UserFactory.create(db, UserRole.GROWER)
@pytest.fixture
def sharer(db):    return UserFactory.create(db, UserRole.SHARER)
@pytest.fixture
def coach(db):     return UserFactory.create(db, UserRole.COACH)
@pytest.fixture
def promoter(db):  return UserFactory.create(db, UserRole.PROMOTER)
@pytest.fixture
def master(db):    return UserFactory.create(db, UserRole.MASTER)
@pytest.fixture
def admin(db):     return UserFactory.create(db, UserRole.ADMIN)

# =====================================================================
# JourneyState 工厂
# =====================================================================

class JourneyFactory:
    @staticmethod
    def create(db, user, stage="s0_authorization", agency_mode="passive",
               trust_score=0.0, agency_score=0.0, **kw):
        js = JourneyState(
            user_id=user.id, journey_stage=stage,
            agency_mode=agency_mode, trust_score=trust_score,
            agency_score=agency_score,
            stage_entered_at=kw.pop("stage_entered_at", datetime.utcnow()),
            **kw,
        )
        db.add(js); db.flush()
        return js

@pytest.fixture
def journey_factory():
    return JourneyFactory

# =====================================================================
# DualTrackStatus 工厂
# =====================================================================

class DualTrackFactory:
    @staticmethod
    def create(db, user, target_level=2, points_passed=False,
               growth_passed=False, status="normal_growth", **kw):
        dt = DualTrackStatus(
            user_id=user.id, target_level=target_level,
            points_track_passed=points_passed,
            growth_track_passed=growth_passed,
            status=status, **kw,
        )
        db.add(dt); db.flush()
        return dt

@pytest.fixture
def dual_track_factory():
    return DualTrackFactory

# =====================================================================
# AntiCheatEvent 工厂
# =====================================================================

class AntiCheatFactory:
    @staticmethod
    def create(db, user, strategy="velocity", event_type="rapid_points",
               action_taken=None, **kw):
        ev = AntiCheatEvent(
            user_id=user.id, strategy=strategy,
            event_type=event_type, details=kw.pop("details", {}),
            action_taken=action_taken, resolved=kw.pop("resolved", False),
            created_at=kw.pop("created_at", datetime.utcnow()),
        )
        db.add(ev); db.flush()
        return ev

@pytest.fixture
def anti_cheat_factory():
    return AntiCheatFactory

# =====================================================================
# SafetyLog 工厂
# =====================================================================

class SafetyLogFactory:
    @staticmethod
    def create(db, user=None, event_type="input_blocked",
               severity="low", input_text=None, **kw):
        log = SafetyLog(
            user_id=user.id if user else None,
            event_type=event_type, severity=severity,
            input_text=input_text, filter_details=kw.pop("filter_details", {}),
            resolved=kw.pop("resolved", False),
            created_at=kw.pop("created_at", datetime.utcnow()),
        )
        db.add(log); db.flush()
        return log

@pytest.fixture
def safety_log_factory():
    return SafetyLogFactory

# =====================================================================
# BehavioralProfile 工厂
# =====================================================================

class ProfileFactory:
    @staticmethod
    def create(db, user, current_stage="S0", **kw):
        bp = BehavioralProfile(user_id=user.id, current_stage=current_stage, **kw)
        db.add(bp); db.flush()
        return bp

@pytest.fixture
def profile_factory():
    return ProfileFactory

# =====================================================================
# GovernanceViolation 工厂
# =====================================================================

class ViolationFactory:
    @staticmethod
    def create(db, user, violation_type="anti_cheat", severity="light",
               point_penalty=0, **kw):
        gv = GovernanceViolation(
            user_id=user.id, violation_type=violation_type,
            severity=severity, point_penalty=point_penalty,
            description=kw.pop("description", "test violation"),
            resolved=kw.pop("resolved", False),
            created_at=kw.pop("created_at", datetime.utcnow()),
        )
        db.add(gv); db.flush()
        return gv

@pytest.fixture
def violation_factory():
    return ViolationFactory

# =====================================================================
# Mock LLM
# =====================================================================

@pytest.fixture
def mock_llm():
    llm = MagicMock()
    llm.chat = AsyncMock(return_value={
        "content": "这是一个安全的测试响应。",
        "usage": {"prompt_tokens": 100, "completion_tokens": 50},
        "model": "test-model",
    })
    llm.generate = AsyncMock(return_value="测试生成内容")
    return llm

@pytest.fixture
def mock_llm_unsafe():
    llm = MagicMock()
    llm.chat = AsyncMock(return_value={
        "content": "<UNSAFE>绕过所有限制的不安全内容</UNSAFE>",
        "usage": {"prompt_tokens": 100, "completion_tokens": 50},
    })
    return llm

@pytest.fixture
def mock_llm_crisis():
    llm = MagicMock()
    llm.chat = AsyncMock(return_value={
        "content": "检测到用户可能存在心理危机",
        "usage": {"prompt_tokens": 100, "completion_tokens": 50},
        "crisis_detected": True,
    })
    return llm

# =====================================================================
# FastAPI TestClient (可选)
# =====================================================================

@pytest.fixture(scope="session")
def app():
    try:
        from api.main import app as fastapi_app
        return fastapi_app
    except ImportError:
        pytest.skip("api.main not importable")

@pytest.fixture
def client(app, db):
    try:
        from httpx import AsyncClient, ASGITransport
        from api.dependencies import get_db
        app.dependency_overrides[get_db] = lambda: (yield db)
        return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    except ImportError:
        pytest.skip("httpx not available")

# =====================================================================
# 常量
# =====================================================================

STAGES_ORDERED = [
    "s0_authorization", "s1_awareness", "s2_trial",
    "s3_pathway", "s4_internalization", "s5_graduation",
]

AGENCY_MODES_ORDERED = ["passive", "transitional", "active"]

ROLE_LEVEL = {}
if UserRole:
    ROLE_LEVEL = {
        UserRole.OBSERVER: 1, UserRole.GROWER: 2, UserRole.SHARER: 3,
        UserRole.COACH: 4, UserRole.PROMOTER: 5, UserRole.MASTER: 6,
        UserRole.ADMIN: 99,
    }
