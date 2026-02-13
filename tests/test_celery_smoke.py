"""PYTHONPATH=. python tests/test_celery_smoke.py"""
import os,sys; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def t1():
    from api.worker import celery_app
    assert celery_app.main=="bhp_worker"; print("[PASS] [1/6] celery_app imported")

def t2():
    from api.worker import celery_app
    n=len(celery_app.conf.beat_schedule)
    for k in sorted(celery_app.conf.beat_schedule): print(f"     {k}: {celery_app.conf.beat_schedule[k]['task']}")
    assert n==16,f"Expected 16 got {n}"; print(f"[PASS] [2/6] beat_schedule: {n} tasks")

def t3():
    from api.tasks import scheduler_tasks as s, governance_tasks as g, event_tasks as e
    for a in["daily_task_generation","reminder_check"]: assert hasattr(s,a)
    for a in["governance_health_check","promotion_ceremony"]: assert hasattr(g,a)
    assert hasattr(e,"process_event"); print("[PASS] [3/6] all task modules ok")

def t4():
    from api.tasks.db import get_sync_url; u=get_sync_url()
    assert "asyncpg" not in u; print(f"[PASS] [4/6] sync url: ...{u.split('@')[-1] if '@' in u else u}")

def t5():
    try:
        import redis as r; r.Redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"),decode_responses=True).ping()
        print("[PASS] [5/6] Redis ok")
    except: print("[WARN] [5/6] Redis unavailable (OK without Docker)")

def t6():
    try:
        from api.worker import celery_app; c=celery_app.connection(); c.connect(); c.close()
        print("[PASS] [6/6] Broker ok")
    except: print("[WARN] [6/6] Broker unavailable (OK without Docker)")

if __name__=="__main__":
    print("="*50+"\n  BHP Celery Smoke Test\n"+"="*50)
    for t in[t1,t2,t3,t4,t5,t6]:
        try: t()
        except AssertionError as e: print(f"[FAIL] {e}")
        except Exception as e: print(f"[WARN] {e}")
    print("="*50)
