"""修复 bhp_cold_backup.py 的 GBK 编码问题"""
import re

p = "bhp_cold_backup.py"
c = open(p, "r", encoding="utf-8").read()

# 1. 修复 subprocess.run — 加 encoding 和 errors
old = "capture_output=True, text=True, timeout=60, **kwargs)"
new = 'capture_output=True, timeout=60, **kwargs)\n        r.stdout = r.stdout.decode("utf-8", errors="replace") if isinstance(r.stdout, bytes) else (r.stdout or "")\n        r.stderr = r.stderr.decode("utf-8", errors="replace") if isinstance(r.stderr, bytes) else (r.stderr or "")'

if old in c:
    # 把 text=True 去掉，改用 bytes 模式再手动 decode
    c = c.replace(old, old.replace(", text=True", ""))
    # 在 subprocess.run 返回后加 decode
    c = c.replace(
        "r = subprocess.run(cmd, capture_output=True, timeout=60, **kwargs)",
        'r = subprocess.run(cmd, capture_output=True, timeout=60, **kwargs)\n        r_stdout = r.stdout.decode("utf-8", errors="replace") if isinstance(r.stdout, bytes) else (r.stdout or "")\n        r_stderr = r.stderr.decode("utf-8", errors="replace") if isinstance(r.stderr, bytes) else (r.stderr or "")\n        r.stdout = r_stdout\n        r.stderr = r_stderr'
    )
    print("[OK] subprocess.run 编码修复")
else:
    print("[INFO] 已修改过或格式不同，尝试备用方案")
    # 备用: 直接在 run_cmd 函数里包装
    c = c.replace(
        "r = subprocess.run(cmd, capture_output=True, text=True, timeout=60",
        "r = subprocess.run(cmd, capture_output=True, timeout=60"
    )

# 2. 修复 write_text(out, ...) — out 可能为 None
c = c.replace(
    '.write_text(out, encoding="utf-8")',
    '.write_text(out or "", encoding="utf-8")'
)
# 也处理单引号版本
c = c.replace(
    ".write_text(out, encoding='utf-8')",
    ".write_text(out or '', encoding='utf-8')"
)

open(p, "w", encoding="utf-8").write(c)
print("[OK] 修复完成")
print("\n运行: python bhp_cold_backup.py")
