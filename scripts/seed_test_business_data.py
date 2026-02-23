# -*- coding: utf-8 -*-
"""
种子业务数据脚本 — 为测试用户注入完整业务数据
Seed Business Data Script — Inject realistic business data for test users

幂等: 先检查再插入，安全重复运行
运行方式: docker exec bhp-api python scripts/seed_test_business_data.py
预览模式: docker exec bhp-api python scripts/seed_test_business_data.py --dry-run
"""

import sys
import os
import random
import uuid
import argparse
from datetime import datetime, timedelta, date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import SessionLocal
from core.models import (
    User, UserRole,
    DailyTask, TaskCheckin,
    GlucoseReading, SleepRecord, ActivityRecord,
    ChatSession, ChatMessage,
    LearningTimeLog,
    CoachPushQueue, CoachMessage,
    CompanionRelation,
    ObserverQuotaLog,
)

random.seed(2026)

# ============================================
# 用户 ID 映射 (seed_test_users.py 创建)
# ============================================
USER_IDS = {
    "admin": 2, "observer": 3, "grower": 4, "sharer": 5,
    "coach": 6, "promoter": 7, "supervisor": 8, "master": 9,
}

# 目标积分 & 阶段
TARGET_GP = {
    "observer": 15, "grower": 120, "sharer": 500,
    "coach": 800, "promoter": 1500, "master": 3000,
}
TARGET_STAGE = {
    "observer": "S0", "grower": "S2", "sharer": "S3",
    "coach": "S4", "promoter": "S5", "master": "S6",
}

NOW = datetime.utcnow()
TODAY = date.today()

# ============================================
# Helper
# ============================================
def dt_ago(days=0, hours=0, minutes=0):
    return NOW - timedelta(days=days, hours=hours, minutes=minutes)


def make_task_id(user_id, task_date, order):
    return f"seed-{user_id}-{task_date.isoformat()}-{order:02d}"


# ============================================
# 1. 更新用户积分 & 阶段
# ============================================
def seed_user_points(db, dry_run=False):
    print("\n[1] 更新用户积分 & 阶段...")
    for username, gp in TARGET_GP.items():
        uid = USER_IDS[username]
        stage = TARGET_STAGE[username]
        if dry_run:
            print(f"  DRY-RUN: {username}(id={uid}) → gp={gp}, stage={stage}")
            continue
        db.execute(text(
            "UPDATE users SET growth_points = :gp, current_stage = :stage WHERE id = :uid"
        ), {"gp": gp, "stage": stage, "uid": uid})
    if not dry_run:
        db.commit()
        print("  ✓ 6 users updated")


# ============================================
# 2. 每日任务 + 打卡
# ============================================
TASK_TEMPLATES = [
    ("测量血糖", "血糖", "#dc2626", "早餐前空腹", "number"),
    ("测量血压", "血压", "#2563eb", "早起后", "number"),
    ("记录体重", "体重", "#7c3aed", "晨起空腹", "number"),
    ("步行30分钟", "运动", "#059669", "下午或傍晚", "confirm"),
    ("情绪自评", "情绪", "#d97706", "睡前", "scale"),
    ("学习健康知识15分钟", "学习", "#0891b2", "任意时间", "confirm"),
    ("记录三餐饮食", "饮食", "#e11d48", "三餐后", "text"),
    ("冥想/放松10分钟", "情绪", "#d97706", "睡前", "confirm"),
    ("写健康日记", "情绪", "#d97706", "睡前", "text"),
    ("深呼吸练习5分钟", "运动", "#059669", "任意", "confirm"),
]

COACH_TASKS = [
    ("审核学员推送", "教练", "#6366f1", "上午", "confirm"),
    ("撰写学员周报", "教练", "#6366f1", "周五", "text"),
    ("查看学员设备警报", "教练", "#6366f1", "每日", "confirm"),
    ("更新干预方案", "教练", "#6366f1", "按需", "text"),
    ("学习教练课程", "学习", "#0891b2", "任意", "confirm"),
]


def seed_daily_tasks(db, dry_run=False):
    print("\n[2] 种子每日任务 + 打卡...")
    # 每个角色的任务天数和模板
    configs = [
        ("grower", 4, 14, TASK_TEMPLATES[:7]),       # 7 templates × 14 days
        ("sharer", 5, 14, TASK_TEMPLATES[:8]),        # 8 templates × 14 days
        ("coach", 6, 14, TASK_TEMPLATES[:5] + COACH_TASKS),  # 10 templates × 14 days
        ("promoter", 7, 7, TASK_TEMPLATES[:5]),       # 5 templates × 7 days
    ]

    total_tasks = 0
    total_checkins = 0

    for username, uid, days, templates in configs:
        # Check existing
        existing = db.execute(text(
            "SELECT COUNT(*) FROM daily_tasks WHERE user_id = :uid AND id LIKE 'seed-%'"
        ), {"uid": uid}).scalar()
        if existing > 0:
            print(f"  跳过 {username}: 已有 {existing} 条种子任务")
            continue

        if dry_run:
            est = len(templates) * days
            print(f"  DRY-RUN: {username} → {est} tasks, ~{int(est*0.6)} checkins")
            continue

        for day_offset in range(days):
            task_date = TODAY - timedelta(days=day_offset)
            for idx, (title, tag, color, hint, mode) in enumerate(templates):
                tid = make_task_id(uid, task_date, idx)
                done = random.random() < 0.65  # 65% completion rate
                done_time = dt_ago(day_offset, random.randint(8, 20)) if done else None

                db.add(DailyTask(
                    id=tid, user_id=uid, task_date=task_date,
                    order_num=idx, title=title, tag=tag, tag_color=color,
                    time_hint=hint, input_mode=mode, quick_label="打卡",
                    source="seed", done=done, done_time=done_time,
                ))
                total_tasks += 1

                if done:
                    db.add(TaskCheckin(
                        task_id=tid, user_id=uid,
                        note=f"种子数据: {title} 完成" if random.random() > 0.5 else None,
                        value=round(random.uniform(1, 10), 1) if mode == "number" else None,
                        points_earned=random.choice([5, 10, 15]),
                        checked_at=done_time,
                    ))
                    total_checkins += 1

        db.flush()

    if not dry_run:
        db.commit()
    print(f"  ✓ {total_tasks} tasks, {total_checkins} checkins")


# ============================================
# 3. 健康设备数据 (血糖 + 睡眠 + 活动)
# ============================================
def seed_device_data(db, dry_run=False):
    print("\n[3] 种子设备数据 (血糖/睡眠/活动)...")

    targets = [
        ("grower", 4, 14),
        ("coach", 6, 14),
    ]

    for username, uid, days in targets:
        # Check existing glucose
        existing = db.execute(text(
            "SELECT COUNT(*) FROM glucose_readings WHERE user_id = :uid"
        ), {"uid": uid}).scalar()
        if existing >= days * 3:
            print(f"  跳过 {username} 血糖: 已有 {existing} 条")
        else:
            if dry_run:
                print(f"  DRY-RUN: {username} 血糖 → ~{days*4} readings")
            else:
                _seed_glucose(db, uid, days)

        # Check existing sleep
        existing = db.execute(text(
            "SELECT COUNT(*) FROM sleep_records WHERE user_id = :uid"
        ), {"uid": uid}).scalar()
        if existing >= days:
            print(f"  跳过 {username} 睡眠: 已有 {existing} 条")
        else:
            if dry_run:
                print(f"  DRY-RUN: {username} 睡眠 → {days} records")
            else:
                _seed_sleep(db, uid, days)

        # Check existing activity
        existing = db.execute(text(
            "SELECT COUNT(*) FROM activity_records WHERE user_id = :uid"
        ), {"uid": uid}).scalar()
        if existing >= days:
            print(f"  跳过 {username} 活动: 已有 {existing} 条")
        else:
            if dry_run:
                print(f"  DRY-RUN: {username} 活动 → {days} records")
            else:
                _seed_activity(db, uid, days)

    if not dry_run:
        db.commit()
        print("  ✓ 设备数据写入完成")


def _seed_glucose(db, user_id, days):
    count = 0
    for d in range(days):
        day = NOW - timedelta(days=d)
        for (hour, tag) in [(7, "fasting"), (13, "after_meal"), (17, "before_meal")]:
            val = round(random.uniform(4.5, 9.5), 1)
            db.add(GlucoseReading(
                user_id=user_id, value=val, unit="mmol/L",
                source="manual", meal_tag=tag,
                recorded_at=day.replace(hour=hour, minute=random.randint(0, 30))
            ))
            count += 1
        if random.random() > 0.3:
            db.add(GlucoseReading(
                user_id=user_id, value=round(random.uniform(5.5, 10.0), 1),
                unit="mmol/L", source="manual", meal_tag="after_meal",
                recorded_at=day.replace(hour=20, minute=random.randint(0, 59))
            ))
            count += 1
    print(f"    血糖: {count} readings (user_id={user_id})")


def _seed_sleep(db, user_id, days):
    for d in range(1, days + 1):
        day = NOW - timedelta(days=d)
        sleep_date = day.strftime("%Y-%m-%d")
        sleep_hour = random.choice([22, 23, 0])
        sleep_start = day.replace(hour=sleep_hour, minute=random.randint(0, 59))
        total_min = random.randint(330, 510)
        sleep_end = sleep_start + timedelta(minutes=total_min + random.randint(10, 40))
        deep = random.randint(60, 120)
        light = random.randint(120, 200)
        rem = random.randint(40, 100)
        awake = max(5, total_min - deep - light - rem)

        db.add(SleepRecord(
            user_id=user_id, sleep_date=sleep_date,
            sleep_start=sleep_start, sleep_end=sleep_end,
            total_duration_min=total_min, awake_min=awake,
            light_min=light, deep_min=deep, rem_min=rem,
            sleep_score=min(100, max(30, int(50 + deep/total_min*100 + total_min/60*5 - awake*0.5))),
            efficiency=round(random.uniform(80, 96), 1),
            awakenings=random.randint(0, 4),
        ))
    print(f"    睡眠: {days} records (user_id={user_id})")


def _seed_activity(db, user_id, days):
    for d in range(days):
        day = NOW - timedelta(days=d)
        steps = random.randint(3000, 15000)
        db.add(ActivityRecord(
            user_id=user_id,
            activity_date=day.strftime("%Y-%m-%d"),
            steps=steps, distance_m=int(steps * 0.7),
            floors_climbed=random.randint(0, 15),
            calories_total=random.randint(1500, 2500),
            calories_active=random.randint(150, 600),
            sedentary_min=random.randint(300, 600),
            light_active_min=random.randint(60, 180),
            moderate_active_min=random.randint(10, 60),
            vigorous_active_min=random.randint(0, 30),
        ))
    print(f"    活动: {days} records (user_id={user_id})")


# ============================================
# 4. 聊天会话 + 消息
# ============================================
CHAT_TEMPLATES = {
    "observer": [
        ("试用咨询: 血糖管理", [
            ("user", "我最近血糖偏高，有什么建议吗？"),
            ("assistant", "您好！血糖管理需要从饮食、运动、作息三方面入手。建议您先记录每日三餐和血糖数据，我可以帮您分析趋势。"),
            ("user", "好的，那我应该怎么开始记录呢？"),
        ]),
        ("试用咨询: 睡眠问题", [
            ("user", "最近总是睡不好觉怎么办？"),
            ("assistant", "睡眠问题很常见。建议您建立固定的作息时间，睡前1小时避免使用电子设备。您可以尝试深呼吸放松练习。"),
        ]),
    ],
    "grower": [
        ("血糖管理日志", [
            ("user", "今天空腹血糖6.2，比昨天降了0.3"),
            ("assistant", "很好的进步！空腹血糖6.2在正常范围。保持当前的饮食和运动计划，继续监测趋势。"),
            ("user", "午餐后血糖有点高，8.5"),
            ("assistant", "餐后血糖8.5稍偏高，建议注意午餐碳水化合物摄入量，饭后可以散步15-20分钟帮助降糖。"),
            ("user", "好的，我试试饭后散步"),
        ]),
        ("运动计划咨询", [
            ("user", "我想开始规律运动，有什么建议？"),
            ("assistant", "根据您的健康档案，建议从每日步行30分钟开始，逐渐增加强度。推荐快走、太极拳或游泳，这些都是适合慢性病管理的运动方式。"),
            ("user", "太极拳在哪里可以学？"),
            ("assistant", "您可以在平台的学习中心搜索太极拳课程，有视频教程和跟练指导。我们也推荐晨间在公园跟随社区活动一起练习。"),
        ]),
        ("饮食记录反馈", [
            ("user", "早餐: 全麦面包+鸡蛋+牛奶，午餐: 清蒸鱼+西兰花+糙米饭"),
            ("assistant", "您的饮食搭配很均衡！全麦面包和糙米提供了优质碳水，蛋白质摄入充足。建议晚餐可以适当增加蔬菜比例，减少主食量。"),
        ]),
    ],
    "sharer": [
        ("分享者交流: 同道者指导", [
            ("user", "我指导的成长者小张最近打卡不太积极，怎么鼓励他？"),
            ("assistant", "了解学员动机很重要。可以尝试：1)私信关心他的近况；2)分享自己曾经的困难期如何坚持；3)设置阶段性小目标，达成后给予肯定。同伴的鼓励往往比方法论更有效。"),
            ("user", "好建议，我今天就去联系他"),
            ("assistant", "很好！作为分享者，您的亲身经历是最有说服力的。记得在平台上记录您的指导经历，这也是积累贡献积分的方式。"),
        ]),
        ("健康经验分享讨论", [
            ("user", "我想投稿一篇关于糖尿病饮食控制的经验文章"),
            ("assistant", "太好了！经验分享是非常有价值的贡献。建议从您自己的真实经历出发，分享具体的饮食调整和效果变化。可以附上您的血糖趋势图更有说服力。"),
            ("user", "大概需要多少字？"),
            ("assistant", "建议800-1500字左右，图文并茂。您可以在学习中心→内容贡献→发起投稿。审核通过后会获得贡献积分，有助于您的晋级进度。"),
        ]),
        ("指导记录: 观察员引导", [
            ("user", "有位新注册的观察员在问一些基础问题，我该怎么引导？"),
            ("assistant", "新观察员需要引导完成初始评估和健康档案。您可以：1)分享平台使用指南；2)帮助他理解每日任务的意义；3)鼓励他完成3天试用后注册成为成长者。您的引导经验也是同道者积分来源。"),
        ]),
    ],
}


def seed_chat_sessions(db, dry_run=False):
    print("\n[4] 种子聊天会话 + 消息...")

    existing = db.execute(text(
        "SELECT COUNT(*) FROM chat_sessions WHERE session_id LIKE 'seed-%'"
    )).scalar()
    if existing > 0:
        print(f"  跳过: 已有 {existing} 条种子会话")
        return

    total_sessions = 0
    total_messages = 0

    for username, conversations in CHAT_TEMPLATES.items():
        uid = USER_IDS[username]
        if dry_run:
            msg_count = sum(len(msgs) for _, msgs in conversations)
            print(f"  DRY-RUN: {username} → {len(conversations)} sessions, {msg_count} messages")
            continue

        for conv_idx, (title, messages) in enumerate(conversations):
            sid = f"seed-{username}-{conv_idx:02d}"
            session = ChatSession(
                session_id=sid, user_id=uid, title=title,
                model="qwen2.5:0.5b", is_active=True,
                message_count=len(messages),
            )
            db.add(session)
            db.flush()  # get session.id

            for msg_idx, (role, content) in enumerate(messages):
                db.add(ChatMessage(
                    session_id=session.id, role=role, content=content,
                    model="qwen2.5:0.5b" if role == "assistant" else None,
                    tokens_used=random.randint(50, 300) if role == "assistant" else None,
                    created_at=dt_ago(days=7-conv_idx, hours=10-msg_idx),
                ))
                total_messages += 1
            total_sessions += 1

    if not dry_run:
        db.commit()
    print(f"  ✓ {total_sessions} sessions, {total_messages} messages")


# ============================================
# 5. 学习时长日志
# ============================================
LEARNING_DOMAINS = ["nutrition", "exercise", "sleep", "mental", "chronic", "tcm"]


def seed_learning_logs(db, dry_run=False):
    print("\n[5] 种子学习时长日志...")

    targets = [
        ("grower", 4, 14),
        ("sharer", 5, 10),
        ("coach", 6, 12),
    ]

    total = 0
    for username, uid, days in targets:
        existing = db.execute(text(
            "SELECT COUNT(*) FROM learning_time_logs WHERE user_id = :uid"
        ), {"uid": uid}).scalar()
        if existing >= days:
            print(f"  跳过 {username}: 已有 {existing} 条")
            continue

        if dry_run:
            print(f"  DRY-RUN: {username} → {days} learning logs")
            continue

        for d in range(days):
            db.add(LearningTimeLog(
                user_id=uid,
                content_id=random.randint(1, 50),
                domain=random.choice(LEARNING_DOMAINS),
                minutes=random.randint(10, 45),
                earned_at=dt_ago(days=d, hours=random.randint(9, 21)),
            ))
            total += 1

    if not dry_run:
        db.commit()
    print(f"  ✓ {total} learning logs")


# ============================================
# 6. 教练-学员绑定
# ============================================
def seed_coach_bindings(db, dry_run=False):
    print("\n[6] 种子教练-学员绑定...")

    coach_id = USER_IDS["coach"]
    bindings = [
        (coach_id, USER_IDS["grower"], "assigned"),
        (coach_id, USER_IDS["sharer"], "assigned"),
    ]

    total = 0
    for cid, sid, btype in bindings:
        existing = db.execute(text(
            "SELECT COUNT(*) FROM coach_schema.coach_student_bindings "
            "WHERE coach_id = :cid AND student_id = :sid"
        ), {"cid": cid, "sid": sid}).scalar()
        if existing > 0:
            print(f"  跳过: coach({cid})→student({sid}) 已存在")
            continue

        if dry_run:
            print(f"  DRY-RUN: coach({cid})→student({sid}) type={btype}")
            continue

        db.execute(text(
            "INSERT INTO coach_schema.coach_student_bindings "
            "(id, coach_id, student_id, binding_type, is_active, bound_at, created_at, updated_at) "
            "VALUES (gen_random_uuid(), :cid, :sid, :btype, true, now(), now(), now())"
        ), {"cid": cid, "sid": sid, "btype": btype})
        total += 1

    if not dry_run:
        db.commit()
    print(f"  ✓ {total} bindings created")


# ============================================
# 7. 教练推送审批队列
# ============================================
PUSH_ITEMS = [
    # (source_type, title, content, priority, status)
    ("ai_recommendation", "建议: 增加餐后步行", "根据学员近3天餐后血糖偏高趋势，建议推送餐后步行提醒", "normal", "pending"),
    ("device_alert", "设备警报: 血糖连续偏高", "学员grower连续2天空腹血糖>6.5，建议关注", "high", "pending"),
    ("challenge", "挑战推荐: 7天步行打卡", "AI推荐学员参加7天步行挑战，匹配其运动目标", "normal", "pending"),
    ("ai_recommendation", "营养建议: 低GI饮食方案", "根据血糖数据分析，推荐低GI饮食方案给sharer", "normal", "approved"),
    ("micro_action", "微行动: 深呼吸练习", "建议推送5分钟深呼吸放松练习给grower", "low", "approved"),
    ("ai_recommendation", "运动强度调整建议", "学员近期活动量下降，建议调整运动处方", "normal", "sent"),
    ("system", "系统提醒: 学员评估到期", "grower的月度评估即将到期，请安排跟进", "high", "sent"),
    ("ai_recommendation", "睡眠干预建议", "学员睡眠质量评分连续下降，建议添加助眠干预", "normal", "rejected"),
]


def seed_push_queue(db, dry_run=False):
    print("\n[7] 种子教练推送审批队列...")

    coach_id = USER_IDS["coach"]
    existing = db.execute(text(
        "SELECT COUNT(*) FROM coach_schema.coach_push_queue WHERE coach_id = :cid"
    ), {"cid": coach_id}).scalar()

    if existing >= len(PUSH_ITEMS):
        print(f"  跳过: 已有 {existing} 条推送记录")
        return

    if dry_run:
        print(f"  DRY-RUN: {len(PUSH_ITEMS)} push queue items")
        return

    students = [USER_IDS["grower"], USER_IDS["sharer"]]
    for idx, (src, title, content, priority, status) in enumerate(PUSH_ITEMS):
        student_id = students[idx % 2]
        reviewed_at = dt_ago(days=random.randint(0, 3)) if status != "pending" else None
        sent_at = dt_ago(days=random.randint(0, 2)) if status == "sent" else None

        db.execute(text(
            "INSERT INTO coach_schema.coach_push_queue "
            "(coach_id, student_id, source_type, title, content, priority, status, "
            "coach_note, reviewed_at, sent_at, created_at) "
            "VALUES (:cid, :sid, :src, :title, :content, :pri, :status, "
            ":note, :reviewed, :sent, :created)"
        ), {
            "cid": coach_id, "sid": student_id, "src": src,
            "title": title, "content": content, "pri": priority, "status": status,
            "note": "已审核" if status in ("approved", "sent") else ("不合适" if status == "rejected" else None),
            "reviewed": reviewed_at, "sent": sent_at,
            "created": dt_ago(days=random.randint(1, 5)),
        })

    db.commit()
    print(f"  ✓ {len(PUSH_ITEMS)} push queue items")


# ============================================
# 8. 教练消息 (coach → student)
# ============================================
COACH_MESSAGES = [
    (USER_IDS.get("coach", 6), USER_IDS.get("grower", 4), "text", "您好，看到您近几天血糖控制得不错，继续保持！"),
    (USER_IDS.get("coach", 6), USER_IDS.get("grower", 4), "advice", "建议这周增加一次太极拳练习，有助于改善血糖和睡眠。"),
    (USER_IDS.get("coach", 6), USER_IDS.get("grower", 4), "encouragement", "坚持打卡一周了，进步很大！加油！"),
    (USER_IDS.get("coach", 6), USER_IDS.get("sharer", 5), "text", "您指导的成长者反馈很好，感谢您的付出。"),
    (USER_IDS.get("coach", 6), USER_IDS.get("sharer", 5), "reminder", "本周记得完成学员月度评估跟进。"),
    (USER_IDS.get("coach", 6), USER_IDS.get("sharer", 5), "advice", "建议您在分享经验时加入更多个人数据变化，更有说服力。"),
]


def seed_coach_messages(db, dry_run=False):
    print("\n[8] 种子教练消息...")

    coach_id = USER_IDS["coach"]
    existing = db.execute(text(
        "SELECT COUNT(*) FROM coach_schema.coach_messages WHERE coach_id = :cid"
    ), {"cid": coach_id}).scalar()

    if existing >= len(COACH_MESSAGES):
        print(f"  跳过: 已有 {existing} 条消息")
        return

    if dry_run:
        print(f"  DRY-RUN: {len(COACH_MESSAGES)} coach messages")
        return

    for idx, (cid, sid, mtype, content) in enumerate(COACH_MESSAGES):
        db.execute(text(
            "INSERT INTO coach_schema.coach_messages "
            "(coach_id, student_id, content, message_type, is_read, created_at) "
            "VALUES (:cid, :sid, :content, :mtype, :read, :created)"
        ), {
            "cid": cid, "sid": sid, "content": content, "mtype": mtype,
            "read": random.random() > 0.3,
            "created": dt_ago(days=idx, hours=random.randint(8, 18)),
        })

    db.commit()
    print(f"  ✓ {len(COACH_MESSAGES)} coach messages")


# ============================================
# 9. 同道者关系
# ============================================
def seed_companion_relations(db, dry_run=False):
    print("\n[9] 种子同道者关系...")

    relations = [
        (USER_IDS["sharer"], USER_IDS["grower"], "SHARER", "GROWER"),
        (USER_IDS["sharer"], USER_IDS["observer"], "SHARER", "OBSERVER"),
    ]

    total = 0
    for mentor_id, mentee_id, mrole, erole in relations:
        existing = db.execute(text(
            "SELECT COUNT(*) FROM companion_relations "
            "WHERE mentor_id = :mid AND mentee_id = :eid"
        ), {"mid": mentor_id, "eid": mentee_id}).scalar()

        if existing > 0:
            print(f"  跳过: {mrole}({mentor_id})→{erole}({mentee_id}) 已存在")
            continue

        if dry_run:
            print(f"  DRY-RUN: {mrole}({mentor_id})→{erole}({mentee_id})")
            continue

        db.execute(text(
            "INSERT INTO companion_relations "
            "(id, mentor_id, mentee_id, mentor_role, mentee_role, status, "
            "quality_score, started_at, interaction_count, last_interaction_at) "
            "VALUES (gen_random_uuid(), :mid, :eid, :mrole, :erole, 'active', "
            ":score, :started, :count, :last)"
        ), {
            "mid": mentor_id, "eid": mentee_id,
            "mrole": mrole, "erole": erole,
            "score": round(random.uniform(3.5, 5.0), 1),
            "started": dt_ago(days=random.randint(10, 30)),
            "count": random.randint(5, 20),
            "last": dt_ago(days=random.randint(0, 3)),
        })
        total += 1

    if not dry_run:
        db.commit()
    print(f"  ✓ {total} companion relations")


# ============================================
# 10. Observer 配额日志 (补充至3条)
# ============================================
def seed_observer_quota(db, dry_run=False):
    print("\n[10] 种子Observer配额日志...")

    uid = USER_IDS["observer"]
    existing = db.execute(text(
        "SELECT COUNT(*) FROM observer_quota_logs WHERE user_id = :uid"
    ), {"uid": uid}).scalar()

    if existing >= 3:
        print(f"  跳过: 已有 {existing} 条")
        return

    need = 3 - existing
    if dry_run:
        print(f"  DRY-RUN: 补充 {need} 条配额日志")
        return

    types = ["chat", "assessment", "chat"]
    for i in range(need):
        db.add(ObserverQuotaLog(
            user_id=uid,
            quota_type=types[existing + i] if (existing + i) < len(types) else "chat",
        ))

    db.commit()
    print(f"  ✓ 补充 {need} 条配额日志")


# ============================================
# Main
# ============================================
def main():
    parser = argparse.ArgumentParser(description="种子业务数据脚本")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不写入数据库")
    args = parser.parse_args()

    dry_run = args.dry_run
    mode = "DRY-RUN (预览)" if dry_run else "LIVE (写入)"

    print("=" * 60)
    print(f"种子业务数据脚本 — 模式: {mode}")
    print("=" * 60)

    db = SessionLocal()
    try:
        # Verify users exist
        result = db.execute(text(
            "SELECT COUNT(*) FROM users WHERE username IN "
            "('observer','grower','sharer','coach','promoter','master')"
        )).scalar()
        if result < 6:
            print(f"ERROR: 只找到 {result}/6 个测试用户。请先运行 seed_test_users.py")
            return

        seed_user_points(db, dry_run)
        seed_daily_tasks(db, dry_run)
        seed_device_data(db, dry_run)
        seed_chat_sessions(db, dry_run)
        seed_learning_logs(db, dry_run)
        seed_coach_bindings(db, dry_run)
        seed_push_queue(db, dry_run)
        seed_coach_messages(db, dry_run)
        seed_companion_relations(db, dry_run)
        seed_observer_quota(db, dry_run)

        print("\n" + "=" * 60)
        if dry_run:
            print("DRY-RUN 完成 — 未写入任何数据")
        else:
            print("全部种子数据写入成功!")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
