"""
BHP 里程碑激励服务 - 同步版 (匹配项目现有DB模式)
==================================================
用法:
  1. 复制到 app/services/milestone_service.py (或 core/)
  2. main.py 中:
       from app.services.milestone_service import incentive_router
       app.include_router(incentive_router)
  3. 确保 V003 SQL 已执行
  4. 确保 configs/ 下有 milestones.json + badges.json

无额外依赖 — 使用项目已有的 SQLAlchemy + psycopg2
"""

import json, random, os
from datetime import datetime, date, timedelta
from typing import Optional, List
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

# ═══ 配置加载 ═══
# 适配项目实际路径: configs/ 目录
CONFIG_DIR = Path(os.environ.get(
    "BHP_CONFIG_DIR",
    Path(__file__).resolve().parent.parent / "configs"
))

def _load(name):
    p = CONFIG_DIR / name
    if not p.exists():
        raise FileNotFoundError(f"缺少配置: {p}")
    return json.loads(p.read_text(encoding="utf-8"))

try:
    _ms_data = _load("milestones.json")
    MILESTONES = _ms_data["milestones"]
    MS_MAP = {m["key"]: m for m in MILESTONES}
    FLIP_POOLS = _ms_data.get("flip_card_pools", {})
except FileNotFoundError:
    MILESTONES, MS_MAP, FLIP_POOLS = [], {}, {}

try:
    _badge_data = _load("badges.json")
    BADGE_CATS = _badge_data["badge_categories"]
    ALL_BADGES = {}
    for ck, cv in BADGE_CATS.items():
        for b in cv.get("badges", []): ALL_BADGES[b["id"]] = {**b, "category": ck}
        for b in cv.get("combo_badges", []): ALL_BADGES[b["id"]] = {**b, "category": ck}
except FileNotFoundError:
    BADGE_CATS, ALL_BADGES = {}, {}


# ═══ DB会话 — 使用项目已有的 get_db ═══
# 方式1: 从项目导入(推荐)
try:
    from core.database import get_db
except ImportError:
    try:
        from core.db import get_db
    except ImportError:
        # 方式2: 如果项目的get_db路径不同，自行修改上面的导入
        # 临时后备: 从环境变量创建
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        _DB_URL = os.environ.get(
            "DATABASE_URL",
            "postgresql+psycopg2://postgres:postgres@localhost:5432/health_platform"
        )
        _engine = create_engine(_DB_URL, echo=False)
        _SessionLocal = sessionmaker(bind=_engine)
        def get_db():
            db = _SessionLocal()
            try:
                yield db
            finally:
                db.close()


# ═══ Pydantic 模型 ═══
class FlipCardChoice(BaseModel):
    record_id: str
    chosen_item_id: str

class StreakRecoveryReq(BaseModel):
    method: str  # free_recovery | credit_recovery | friend_rescue

class RitualPlayed(BaseModel):
    milestone: str


# ═══ 核心引擎 (全部同步) ═══
class MilestoneEngine:
    def __init__(self, db: Session):
        self.db = db

    def daily_checkin(self, uid: int) -> dict:
        """每日打卡 → 更新连续天数 → 检查里程碑 → 发放奖励"""
        row = self.db.execute(text(
            "SELECT current_streak, longest_streak, last_checkin_date "
            "FROM user_streaks WHERE user_id = :uid FOR UPDATE"
        ), {"uid": uid}).fetchone()

        today = date.today()

        if row is None:
            self.db.execute(text(
                "INSERT INTO user_streaks (user_id, current_streak, longest_streak, last_checkin_date) "
                "VALUES (:uid, 0, 0, NULL)"
            ), {"uid": uid})
            self.db.flush()
            streak, longest, last = 0, 0, None
        else:
            streak, longest, last = row.current_streak, row.longest_streak, row.last_checkin_date

        # 今天已打卡
        if last == today:
            return {"streak": streak, "milestones_triggered": [], "rewards": [], "daily_points": 0}

        # 计算新连续天数
        if last is None or last == today - timedelta(1):
            streak += 1
        elif last == today - timedelta(2):
            streak += 1  # 36h宽限
        else:
            streak = 1  # 断签重置

        longest = max(longest, streak)

        self.db.execute(text(
            "UPDATE user_streaks SET current_streak = :s, longest_streak = :l, "
            "last_checkin_date = :d, updated_at = NOW() WHERE user_id = :uid"
        ), {"s": streak, "l": longest, "d": today, "uid": uid})

        self._pts(uid, "growth", 5, "daily_checkin")

        # 检查里程碑触发
        ms_days = {"DAY_3": 3, "DAY_7": 7, "DAY_14": 14, "DAY_21": 21, "DAY_30": 30}
        triggered, rewards = [], []
        for k, d in ms_days.items():
            if streak >= d:
                exists = self.db.execute(text(
                    "SELECT 1 FROM user_milestones WHERE user_id = :uid AND milestone = :ms"
                ), {"uid": uid, "ms": k}).fetchone()
                if not exists:
                    r = self._trigger(uid, k, streak)
                    triggered.append(k)
                    rewards.append(r)

        self.db.commit()
        return {"streak": streak, "milestones_triggered": triggered, "rewards": rewards, "daily_points": 5}

    def first_login(self, uid: int) -> dict:
        """注册后调用 → 触发种子仪式"""
        exists = self.db.execute(text(
            "SELECT 1 FROM user_milestones WHERE user_id = :uid AND milestone = 'FIRST_LOGIN'"
        ), {"uid": uid}).fetchone()
        if exists:
            return {"milestone": "FIRST_LOGIN", "status": "already_achieved"}
        result = self._trigger(uid, "FIRST_LOGIN", 0)
        self.db.commit()
        return result

    def _trigger(self, uid, ms_key, streak):
        """触发一个里程碑 — 记录+发积分+发徽章+处理奖励"""
        cfg = MS_MAP[ms_key]
        rw = cfg["rewards"]

        self.db.execute(text(
            "INSERT INTO user_milestones (user_id, milestone, streak_days, rewards_json) "
            "VALUES (:uid, :ms, :s, :rj) ON CONFLICT (user_id, milestone) DO NOTHING"
        ), {"uid": uid, "ms": ms_key, "s": streak, "rj": json.dumps(rw)})

        for pt in rw["points"]:
            self._pts(uid, pt["type"], pt["amount"], pt["action"])

        bg = []
        for bid in rw.get("badges", []):
            if self._badge(uid, bid):
                bg.append(bid)

        items = []
        for item in rw.get("items", []):
            items.append(self._item(uid, item, ms_key))

        return {
            "milestone": ms_key, "display": cfg["display"], "ritual": cfg["ritual"],
            "credits": rw.get("credits", 0),
            "points": sum(p["amount"] for p in rw["points"]),
            "badges": bg, "items": items, "unlocks": rw.get("unlocks", [])
        }

    def _pts(self, uid, pt, amt, act):
        """写入积分事务 + 更新汇总"""
        self.db.execute(text(
            "INSERT INTO point_transactions (user_id, point_type, amount, action, created_at) "
            "VALUES (:uid, :pt, :amt, :act, NOW())"
        ), {"uid": uid, "pt": pt, "amt": amt, "act": act})

        self.db.execute(text(
            "INSERT INTO user_points (user_id, point_type, total_points) "
            "VALUES (:uid, :pt, :amt) "
            "ON CONFLICT (user_id, point_type) "
            "DO UPDATE SET total_points = user_points.total_points + :amt"
        ), {"uid": uid, "pt": pt, "amt": amt})

    def _badge(self, uid, bid) -> bool:
        """发放徽章 (幂等)"""
        exists = self.db.execute(text(
            "SELECT 1 FROM badges WHERE id = :bid"
        ), {"bid": bid}).fetchone()

        if not exists:
            info = ALL_BADGES.get(bid)
            if info:
                self.db.execute(text(
                    "INSERT INTO badges (id, name, category, icon, rarity, condition_json) "
                    "VALUES (:id, :n, :c, :i, :r, :cj) ON CONFLICT (id) DO NOTHING"
                ), {
                    "id": bid, "n": info.get("name", bid), "c": info.get("category", "misc"),
                    "i": info.get("icon", ""), "r": info.get("rarity", "common"),
                    "cj": json.dumps(info.get("condition", {}))
                })

        r = self.db.execute(text(
            "INSERT INTO user_badges (user_id, badge_id) "
            "VALUES (:uid, :bid) ON CONFLICT (user_id, badge_id) DO NOTHING RETURNING id"
        ), {"uid": uid, "bid": bid}).fetchone()
        return r is not None

    def _item(self, uid, item, ms_key):
        """处理奖励项: 翻牌/海报/数据艺术等"""
        t = item["type"]

        if t == "flip_card_reward":
            pool = FLIP_POOLS.get(item["pool"])
            if not pool:
                return {"type": t, "status": "pool_not_found"}
            shown = random.sample(pool["items"], k=min(item.get("show", 3), len(pool["items"])))
            self.db.execute(text(
                "INSERT INTO flip_card_records (user_id, pool_id, shown_items, chosen_item_id, reward_json) "
                "VALUES (:uid, :p, :s, '', '{}')"
            ), {"uid": uid, "p": item["pool"], "s": json.dumps([x["id"] for x in shown])})
            return {
                "type": "flip_card", "status": "pending_choice",
                "shown": [{"id": x["id"], "label": x["label"]} for x in shown]
            }

        if t in ("data_poster", "data_art", "ai_documentary"):
            snap = self._snap(uid)
            tmpl = item.get("template", ms_key)
            self.db.execute(text(
                "INSERT INTO user_memorials (user_id, type, template, data_snapshot) "
                "VALUES (:uid, :t, :tm, :d)"
            ), {"uid": uid, "t": t, "tm": tmpl, "d": json.dumps(snap)})
            return {"type": t, "template": tmpl, "status": "generated" if t == "data_poster" else "queued"}

        return {"type": t, "status": "granted", **{k: v for k, v in item.items() if k != "type"}}

    def _snap(self, uid):
        """生成用户数据快照"""
        r = self.db.execute(text(
            "SELECT * FROM v_user_incentive_summary WHERE user_id = :uid"
        ), {"uid": uid}).fetchone()
        base = {"user_id": uid, "ts": datetime.utcnow().isoformat()}
        if r:
            base.update({
                "streak": r.current_streak,
                "badges": r.badge_count,
                "milestones": r.milestone_count
            })
        return base

    def flip_choose(self, uid, record_id, chosen_id):
        """前端翻牌选择回调"""
        row = self.db.execute(text(
            "SELECT id, pool_id, shown_items FROM flip_card_records "
            "WHERE id = :rid AND user_id = :uid AND chosen_item_id = ''"
        ), {"rid": record_id, "uid": uid}).fetchone()

        if not row:
            raise HTTPException(400, "记录不存在或已选择")

        shown = json.loads(row.shown_items)
        if chosen_id not in shown:
            raise HTTPException(400, "所选项不在展示列表中")

        pool = FLIP_POOLS.get(row.pool_id, {})
        item = next((i for i in pool.get("items", []) if i["id"] == chosen_id), None)
        if not item:
            raise HTTPException(400, "奖励项不存在")

        reward = {"id": chosen_id, "label": item["label"], "type": item["type"]}
        if item["type"] == "credits":
            self._pts(uid, "growth", item["amount"], "flip_card_bonus")
            reward["amount"] = item["amount"]

        self.db.execute(text(
            "UPDATE flip_card_records SET chosen_item_id = :cid, reward_json = :rj WHERE id = :rid"
        ), {"cid": chosen_id, "rj": json.dumps(reward), "rid": record_id})

        self.db.commit()
        return {"status": "rewarded", "reward": reward}

    def recover_streak(self, uid, method):
        """断签恢复: 免费(1次/月) / 积分(10分) / 好友"""
        row = self.db.execute(text(
            "SELECT current_streak, last_checkin_date, grace_used_month "
            "FROM user_streaks WHERE user_id = :uid FOR UPDATE"
        ), {"uid": uid}).fetchone()

        if not row:
            return {"success": False, "reason": "no_streak_record"}

        today = date.today()
        if row.last_checkin_date and (today - row.last_checkin_date).days <= 1:
            return {"success": False, "reason": "no_break"}
        if row.last_checkin_date and (today - row.last_checkin_date).days > 3:
            return {"success": False, "reason": "break_too_long"}

        if method == "free_recovery":
            if row.grace_used_month >= 1:
                return {"success": False, "reason": "used_this_month"}
            self.db.execute(text(
                "UPDATE user_streaks SET current_streak = current_streak + 1, "
                "last_checkin_date = :d, grace_used_month = grace_used_month + 1, "
                "recovery_count = recovery_count + 1 WHERE user_id = :uid"
            ), {"d": today - timedelta(1), "uid": uid})

        elif method == "credit_recovery":
            pts = self.db.execute(text(
                "SELECT total_points FROM user_points "
                "WHERE user_id = :uid AND point_type = 'growth'"
            ), {"uid": uid}).fetchone()
            if not pts or pts.total_points < 10:
                return {"success": False, "reason": "insufficient_points"}
            self._pts(uid, "growth", -10, "streak_recovery_cost")
            self.db.execute(text(
                "UPDATE user_streaks SET current_streak = current_streak + 1, "
                "last_checkin_date = :d, recovery_count = recovery_count + 1 WHERE user_id = :uid"
            ), {"d": today - timedelta(1), "uid": uid})

        elif method == "friend_rescue":
            has = self.db.execute(text(
                "SELECT 1 FROM companion_relations "
                "WHERE mentee_id = :uid AND status = 'active' LIMIT 1"
            ), {"uid": uid}).fetchone()
            if not has:
                return {"success": False, "reason": "no_companion"}
            self.db.execute(text(
                "UPDATE user_streaks SET current_streak = current_streak + 1, "
                "last_checkin_date = :d, recovery_count = recovery_count + 1 WHERE user_id = :uid"
            ), {"d": today - timedelta(1), "uid": uid})
        else:
            return {"success": False, "reason": "invalid_method"}

        self.db.commit()
        return {"success": True, "method": method}

    def check_learning_badges(self, uid, hours):
        """学时更新后调用"""
        for b in BADGE_CATS.get("learning_hours", {}).get("badges", []):
            if hours >= b["condition"]["training_hours_gte"]:
                self._badge(uid, b["id"])
        self.db.commit()

    def check_module_badges(self, uid):
        """学分更新后调用"""
        rows = self.db.execute(text(
            "SELECT cm.module_type, SUM(uc.credit_earned) t FROM user_credits uc "
            "JOIN course_modules cm ON uc.module_id = cm.id WHERE uc.user_id = :uid "
            "GROUP BY cm.module_type"
        ), {"uid": uid}).fetchall()
        creds = {r.module_type: float(r.t) for r in rows}
        for b in BADGE_CATS.get("module_mastery", {}).get("badges", []):
            c = b["condition"]
            if creds.get(c["module"], 0) >= c["module_credits_gte"]:
                self._badge(uid, b["id"])
        self.db.commit()

    def check_promotion_badge(self, uid, role):
        """晋级后调用"""
        for b in BADGE_CATS.get("promotion_ceremony", {}).get("badges", []):
            if b["condition"]["role"] == role:
                self._badge(uid, b["id"])
        self.db.commit()

    def dashboard(self, uid):
        """用户激励面板"""
        done = self.db.execute(text(
            "SELECT milestone, achieved_at, ritual_played FROM user_milestones "
            "WHERE user_id = :uid ORDER BY achieved_at"
        ), {"uid": uid}).fetchall()
        dm = {r.milestone: r for r in done}

        journey, nxt = [], None
        for m in MILESTONES:
            d = dm.get(m["key"])
            a = d is not None
            journey.append({
                "key": m["key"], "display": m["display"], "achieved": a,
                "achieved_at": d.achieved_at.isoformat() if d else None,
                "ritual_played": d.ritual_played if d else False,
                "ritual": m["ritual"] if a and d and not d.ritual_played else None
            })
            if not a and nxt is None:
                nxt = m["key"]

        s = self.db.execute(text(
            "SELECT current_streak, longest_streak, last_checkin_date "
            "FROM user_streaks WHERE user_id = :uid"
        ), {"uid": uid}).fetchone()

        badges = self.db.execute(text(
            "SELECT ub.badge_id, ub.earned_at, b.name, b.icon, b.rarity, b.category "
            "FROM user_badges ub JOIN badges b ON ub.badge_id = b.id "
            "WHERE ub.user_id = :uid ORDER BY ub.earned_at"
        ), {"uid": uid}).fetchall()

        mems = self.db.execute(text(
            "SELECT type, template, created_at, asset_url, shared_count "
            "FROM user_memorials WHERE user_id = :uid ORDER BY created_at DESC LIMIT 20"
        ), {"uid": uid}).fetchall()

        return {
            "journey": journey, "next_milestone": nxt,
            "streak": {
                "current": s.current_streak if s else 0,
                "longest": s.longest_streak if s else 0,
                "last_date": s.last_checkin_date.isoformat() if s and s.last_checkin_date else None
            },
            "badges": [
                {"id": r.badge_id, "name": r.name, "icon": r.icon, "rarity": r.rarity,
                 "category": r.category, "earned_at": r.earned_at.isoformat()}
                for r in badges
            ],
            "memorials": [
                {"type": r.type, "template": r.template, "created_at": r.created_at.isoformat(),
                 "asset_url": r.asset_url, "shares": r.shared_count}
                for r in mems
            ]
        }


# ═══ FastAPI 路由 (同步) ═══
incentive_router = APIRouter(prefix="/api/v1/incentive", tags=["incentive"])


def _uid(request: Request) -> int:
    """从请求中获取用户ID — 支持 JWT Bearer / X-User-Id / user_id"""
    # 1. JWT Bearer token (标准认证)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            from core.auth import verify_token_with_blacklist
            payload = verify_token_with_blacklist(auth_header.split(" ", 1)[1])
            if payload and "user_id" in payload:
                return int(payload["user_id"])
        except Exception:
            pass
    # 2. 后备: X-User-Id header 或 user_id query param
    v = request.headers.get("X-User-Id") or request.query_params.get("user_id")
    if not v:
        raise HTTPException(401, "需要Authorization Bearer或X-User-Id参数")
    return int(v)


@incentive_router.post("/checkin")
def checkin(uid: int = Depends(_uid), db: Session = Depends(get_db)):
    """每日打卡"""
    return MilestoneEngine(db).daily_checkin(uid)


@incentive_router.post("/first-login")
def first_login(uid: int = Depends(_uid), db: Session = Depends(get_db)):
    """注册后触发种子仪式"""
    return MilestoneEngine(db).first_login(uid)


@incentive_router.get("/dashboard")
def dash(uid: int = Depends(_uid), db: Session = Depends(get_db)):
    """用户激励面板"""
    return MilestoneEngine(db).dashboard(uid)


@incentive_router.post("/flip-card/choose")
def flip(body: FlipCardChoice, uid: int = Depends(_uid), db: Session = Depends(get_db)):
    """翻牌选择"""
    return MilestoneEngine(db).flip_choose(uid, body.record_id, body.chosen_item_id)


@incentive_router.post("/streak/recover")
def recover(body: StreakRecoveryReq, uid: int = Depends(_uid), db: Session = Depends(get_db)):
    """断签恢复"""
    return MilestoneEngine(db).recover_streak(uid, body.method)


@incentive_router.post("/ritual/played")
def ritual(body: RitualPlayed, uid: int = Depends(_uid), db: Session = Depends(get_db)):
    """仪式播放完成回调"""
    db.execute(text(
        "UPDATE user_milestones SET ritual_played = true "
        "WHERE user_id = :uid AND milestone = :ms"
    ), {"uid": uid, "ms": body.milestone})
    db.commit()
    return {"status": "ok"}


@incentive_router.get("/badges")
def badges(uid: int = Depends(_uid), db: Session = Depends(get_db)):
    """已获徽章列表"""
    rows = db.execute(text(
        "SELECT ub.badge_id, ub.earned_at, b.name, b.icon, b.rarity, b.category "
        "FROM user_badges ub JOIN badges b ON ub.badge_id = b.id "
        "WHERE ub.user_id = :uid"
    ), {"uid": uid}).fetchall()
    return [
        {"id": r.badge_id, "name": r.name, "icon": r.icon, "rarity": r.rarity,
         "category": r.category, "earned_at": r.earned_at.isoformat()}
        for r in rows
    ]


@incentive_router.get("/badges/available")
def badges_avail(uid: int = Depends(_uid), db: Session = Depends(get_db)):
    """所有可获徽章+进度"""
    earned = {r.badge_id for r in db.execute(text(
        "SELECT badge_id FROM user_badges WHERE user_id = :uid"
    ), {"uid": uid}).fetchall()}
    return [
        {"id": bid, "name": b.get("name", bid), "icon": b.get("icon", ""),
         "rarity": b.get("rarity", "common"), "category": b.get("category"),
         "earned": bid in earned, "condition": b.get("condition", {})}
        for bid, b in ALL_BADGES.items()
    ]


@incentive_router.get("/memorials")
def memorials(uid: int = Depends(_uid), db: Session = Depends(get_db)):
    """纪念物列表"""
    rows = db.execute(text(
        "SELECT id, type, template, created_at, asset_url, shared_count "
        "FROM user_memorials WHERE user_id = :uid ORDER BY created_at DESC"
    ), {"uid": uid}).fetchall()
    return [
        {"id": str(r.id), "type": r.type, "template": r.template,
         "created_at": r.created_at.isoformat(), "asset_url": r.asset_url, "shares": r.shared_count}
        for r in rows
    ]


@incentive_router.get("/ceremony/{from_role}/{to_role}")
def ceremony_cfg(from_role: str, to_role: str):
    """晋级仪式配置"""
    for c in BADGE_CATS.get("promotion_ceremony", {}).get("ceremony_configs", []):
        if c["from_role"] == from_role and c["to_role"] == to_role:
            return c
    raise HTTPException(404, f"未找到 {from_role}→{to_role} 仪式配置")


@incentive_router.post("/ceremony/{from_role}/{to_role}/complete")
def ceremony_done(from_role: str, to_role: str,
                  uid: int = Depends(_uid), db: Session = Depends(get_db)):
    """晋级仪式完成"""
    eng = MilestoneEngine(db)
    eng.check_promotion_badge(uid, to_role)
    snap = eng._snap(uid)
    db.execute(text(
        "INSERT INTO user_memorials (user_id, type, template, data_snapshot) "
        "VALUES (:uid, :t, :tm, :d)"
    ), {"uid": uid, "t": f"ceremony_{to_role}", "tm": f"{from_role}_to_{to_role}", "d": json.dumps(snap)})
    db.commit()
    return {"status": "completed", "from": from_role, "to": to_role}
