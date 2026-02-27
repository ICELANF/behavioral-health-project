#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
import_knowledge_base.py — G:\\知识库 批量导入行为健康平台知识库

功能:
  - 登录平台(admin)
  - 按类别将 G:\\知识库 中的 15 个文档逐一通过 API 上传
  - 自动设置 domain_id / evidence_tier / priority / scope
  - 输出每条结果并生成 JSON 报告

用法:
  python3 scripts/import_knowledge_base.py
  python3 scripts/import_knowledge_base.py --dry-run
  python3 scripts/import_knowledge_base.py --source G:/知识库 --base-url http://localhost:8000
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from typing import Optional

try:
    import requests
except ImportError:
    print("请安装 requests: pip install requests")
    sys.exit(1)

# ──────────────────────────────────────────────
# 文档类别映射表
#
# 格式: (文件名, domain_id, evidence_tier, priority, 类别说明)
#
# 领域定义 (平台 8 领域):
#   nutrition  - 营养管理 (饮食/膳食/代谢相关)
#   exercise   - 运动习惯 (运动处方/康复运动)
#   cognitive  - 认知提升 (行为认知/平台规范)
#   tcm        - 中医健康 (中医养生/辨证施治)
#   sleep      - 睡眠调节
#   emotion    - 情绪调节
#   stress     - 压力管理
#   social     - 社交连接
#
# 证据分层 (T1-T4):
#   T1 - 国家指南/权威机构临床指南/系统综述/RCT
#   T2 - 专家共识/协会推荐意见
#   T3 - 回顾性研究/病例系列
#   T4 - 经验性/内部参考资料
# ──────────────────────────────────────────────
DOCUMENT_MAP = [
    # ── 国家级 / 权威机构临床指南 (T1) ────────────────────────────────
    (
        "国家基层糖尿病防治管理指南2022_知识库版.md",
        "nutrition", "T1", 9,
        "国家卫健委《国家基层糖尿病防治管理指南(2022版)》——糖尿病综合管理权威依据",
    ),
    (
        "ACLM生活方式干预糖尿病指南2025_知识库版.md",
        "nutrition", "T1", 9,
        "美国生活方式医学学会(ACLM)《生活方式干预糖尿病循证指南(2025)》",
    ),
    (
        "acsm_exercise_prescription_guideline.md",
        "exercise", "T1", 9,
        "ACSM美国运动医学学会《运动处方指南》——慢病运动干预权威参考",
    ),
    (
        "bgm_clinical_guideline_2021.md",
        "nutrition", "T1", 8,
        "《血糖监测临床应用指南(2021)》——BGM/CGM规范使用依据",
    ),
    (
        "动态葡萄糖图谱_AGP_报告临床应用指南.md",
        "nutrition", "T1", 8,
        "《动态葡萄糖图谱(AGP)报告临床应用国际共识》——CGM报告解读规范",
    ),
    (
        "成人肥胖食养指南-BHP知识库文档.md",
        "nutrition", "T1", 8,
        "国家卫健委《成人肥胖食养指南》——肥胖营养干预权威依据",
    ),
    (
        "成人高血压食养指南2023_BHP知识库文档.md",
        "nutrition", "T1", 8,
        "国家卫健委《成人高血压食养指南(2023)》——高血压膳食管理规范",
    ),
    (
        "成人高脂血症食养指南2023_BHP知识库文档.md",
        "nutrition", "T1", 8,
        "国家卫健委《成人高脂血症食养指南(2023)》——血脂异常膳食干预",
    ),
    # ── 专家共识 / 协会推荐意见 (T2) ──────────────────────────────────
    (
        "缓解2型糖尿病中国专家共识_知识库版.md",
        "nutrition", "T2", 8,
        "《缓解2型糖尿病中国专家共识》——低热量饮食/代谢手术/生活方式干预路径",
    ),
    (
        "LADA诊疗中国专家共识2021版解读.md",
        "nutrition", "T2", 7,
        "《成人隐匿性自身免疫糖尿病(LADA)诊疗中国专家共识(2021)》解读",
    ),
    (
        "成人隐匿性自身免疫糖尿病_LADA_临床指南.md",
        "nutrition", "T2", 7,
        "成人LADA临床指南——自身免疫糖尿病鉴别诊断与个性化治疗方案",
    ),
    (
        "diabetes_dietary_guide.md",
        "nutrition", "T2", 7,
        "糖尿病饮食实用指导——膳食计划/食物交换份/GI指数/餐后血糖管理",
    ),
    (
        "hyperuricemia_gout_dietary_guide.md",
        "nutrition", "T2", 7,
        "高尿酸血症与痛风食养指南——嘌呤管理/食物分级/生活方式干预",
    ),
    (
        "儿童青少年肥胖食养知识库_BHP.md",
        "nutrition", "T2", 7,
        "儿童青少年肥胖食养知识库——针对未成年群体营养干预与家庭管理策略",
    ),
    # ── 平台内部参考资料 (T4) ──────────────────────────────────────────
    (
        "行为健康数字平台标准规则知识库.md",
        "cognitive", "T4", 5,
        "行为健康数字平台内部标准规则知识库——平台行为干预规范与执行流程参考",
    ),
]

# 领域中文名映射
DOMAIN_ZH = {
    "nutrition": "营养管理", "exercise": "运动习惯",
    "cognitive": "认知提升", "tcm": "中医健康",
    "sleep": "睡眠调节", "emotion": "情绪调节",
    "stress": "压力管理", "social": "社交连接",
}


# ──────────────────────────────────────────────
# 输出工具
# ──────────────────────────────────────────────
def ok(msg):       print(f"  [OK]   {msg}")
def fail(msg):     print(f"  [FAIL] {msg}")
def info(msg):     print(f"  [INFO] {msg}")
def warn(msg):     print(f"  [WARN] {msg}")
def section(t):    print(f"\n{'='*65}\n{t}\n{'='*65}")
def subsect(t):    print(f"\n  ─── {t} ───")


# ──────────────────────────────────────────────
# HTTP 调用
# ──────────────────────────────────────────────
def do_login(base_url: str, username: str, password: str) -> Optional[str]:
    try:
        r = requests.post(
            f"{base_url}/api/v1/auth/login",
            data={"username": username, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10,
        )
        if r.status_code == 200:
            return r.json().get("access_token")
        fail(f"登录失败 HTTP {r.status_code}: {r.text[:200]}")
        return None
    except Exception as e:
        fail(f"登录异常: {e}")
        return None


def do_upload(
    base_url: str,
    token: str,
    file_path: str,
    filename: str,
    domain_id: str,
    evidence_tier: str,
    priority: int,
    scope: str = "platform",
) -> dict:
    try:
        with open(file_path, "rb") as f:
            files = {"file": (filename, f, "text/markdown")}
            data = {
                "scope": scope,
                "domain_id": domain_id,
                "evidence_tier": evidence_tier,
                "priority": str(priority),
            }
            r = requests.post(
                f"{base_url}/api/v1/knowledge/batch-upload",
                files=files,
                data=data,
                headers={"Authorization": f"Bearer {token}"},
                timeout=60,
            )
        if r.status_code == 200:
            return r.json()
        return {"_error": f"HTTP {r.status_code}", "_detail": r.text[:400]}
    except Exception as e:
        return {"_error": str(e)}


# ──────────────────────────────────────────────
# 主流程
# ──────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="G:\\知识库 批量导入行为健康平台知识库")
    parser.add_argument("--source",   default="G:/知识库",          help="知识库目录路径")
    parser.add_argument("--base-url", default="http://localhost:8000", help="API 地址")
    parser.add_argument("--username", default="admin",               help="登录用户名")
    parser.add_argument("--password", default="Admin@2026",          help="登录密码")
    parser.add_argument("--dry-run",  action="store_true",           help="预演模式，不实际上传")
    parser.add_argument("--delay",    type=float, default=1.5,       help="上传间隔秒数")
    args = parser.parse_args()

    base_url   = args.base_url.rstrip("/")
    source_dir = args.source.rstrip("/\\")

    section("G:\\知识库  →  行为健康平台知识库  批量导入")
    print(f"  来源目录 : {source_dir}")
    print(f"  API地址  : {base_url}")
    print(f"  运行模式 : {'[DRY-RUN] 预演，不实际上传' if args.dry_run else '[LIVE] 正式导入'}")
    print(f"  上传间隔 : {args.delay}s")

    # ── Step 1: 登录 ──────────────────────────
    section("Step 1: 登录")
    token = ""
    if not args.dry_run:
        token = do_login(base_url, args.username, args.password) or ""
        if not token:
            fail("登录失败，终止导入")
            return 1
        ok(f"登录成功 ({args.username}), token: {token[:22]}...")
    else:
        info("DRY-RUN 模式，跳过实际登录")

    # ── Step 2: 文件核查 ───────────────────────
    section("Step 2: 文件核查与类别映射")
    to_upload = []
    missing   = []
    domain_counter: dict = {}

    for fname, domain_id, ev_tier, prio, desc in DOCUMENT_MAP:
        fpath = os.path.join(source_dir, fname)
        exists = os.path.exists(fpath)
        if exists:
            size_kb = os.path.getsize(fpath) / 1024
            ok(f"[{ev_tier}][{domain_id:9s}] {fname}  ({size_kb:.0f} KB)")
            to_upload.append((fpath, fname, domain_id, ev_tier, prio, desc))
            domain_counter[domain_id] = domain_counter.get(domain_id, 0) + 1
        else:
            warn(f"[MISS]              {fname}  (不存在，跳过)")
            missing.append(fname)

    print(f"\n  待上传: {len(to_upload)} 个  |  缺失: {len(missing)} 个")
    print("\n  按领域分布:")
    for d, cnt in sorted(domain_counter.items()):
        print(f"    {d:9s} ({DOMAIN_ZH.get(d, d)}) : {cnt} 个文档")

    if not to_upload:
        fail("没有可上传的文件，退出")
        return 1

    # ── Step 3: 批量上传 ──────────────────────
    section(f"Step 3: 批量上传{'[DRY-RUN]' if args.dry_run else ''}")

    results  = []
    n_ok     = 0
    n_fail   = 0
    failed_names = []

    for idx, (fpath, fname, domain_id, ev_tier, prio, desc) in enumerate(to_upload, 1):
        pad = f"[{idx:02d}/{len(to_upload):02d}]"
        print(f"\n  {pad} {fname}")
        print(f"         domain={domain_id}  tier={ev_tier}  priority={prio}")
        print(f"         {desc}")

        if args.dry_run:
            ok(f"  [DRY] 已模拟上传")
            n_ok += 1
            results.append({
                "filename": fname, "domain_id": domain_id,
                "evidence_tier": ev_tier, "priority": prio,
                "description": desc, "status": "dry_run",
                "job_id": None, "chunks": None,
            })
        else:
            resp = do_upload(
                base_url, token, fpath, fname,
                domain_id, ev_tier, prio,
            )
            if "_error" in resp:
                fail(f"  上传失败: {resp['_error']}  {resp.get('_detail', '')}")
                n_fail += 1
                failed_names.append(fname)
                results.append({
                    "filename": fname, "domain_id": domain_id,
                    "evidence_tier": ev_tier, "priority": prio,
                    "description": desc, "status": "failed",
                    "error": resp["_error"],
                })
            else:
                job_id = resp.get("job_id", "?")
                chunks = resp.get("total_chunks", "?")
                status = resp.get("status", "?")
                ok(f"  job_id={job_id}  chunks={chunks}  status={status}")
                n_ok += 1
                results.append({
                    "filename": fname, "domain_id": domain_id,
                    "evidence_tier": ev_tier, "priority": prio,
                    "description": desc, "status": "ok",
                    "job_id": job_id, "chunks": chunks,
                })

            if idx < len(to_upload):
                time.sleep(args.delay)

    # ── Step 4: 总结 ──────────────────────────
    section("Step 4: 导入总结")
    print(f"  总计:  {len(to_upload)}")
    print(f"  成功:  {n_ok}")
    print(f"  失败:  {n_fail}")

    if failed_names:
        print("\n  失败文件:")
        for fn in failed_names:
            fail(f"    {fn}")

    # 证据层级分布
    tier_counts = {"T1": 0, "T2": 0, "T3": 0, "T4": 0}
    for r in results:
        if r["status"] in ("ok", "dry_run"):
            tier_counts[r["evidence_tier"]] = tier_counts.get(r["evidence_tier"], 0) + 1
    print(f"\n  证据层级: T1={tier_counts['T1']} 条  T2={tier_counts['T2']} 条  T4={tier_counts['T4']} 条")

    # ── Step 5: JSON 报告 ─────────────────────
    report = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source_dir": source_dir,
        "dry_run": args.dry_run,
        "total": len(to_upload),
        "passed": n_ok,
        "failed": n_fail,
        "domain_distribution": domain_counter,
        "evidence_distribution": tier_counts,
        "results": results,
    }
    report_path = "knowledge_import_report.json"
    with open(report_path, "w", encoding="utf-8") as fp:
        json.dump(report, fp, ensure_ascii=False, indent=2)
    print(f"\n  报告已保存: {report_path}")

    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
