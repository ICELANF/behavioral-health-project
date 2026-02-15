# -*- coding: utf-8 -*-
"""
patch_main_dual_singleton.py — main.py 双单例→统一单例 迁移补丁

用法:
  python patch_main_dual_singleton.py

功能:
  1. 在 main.py 中查找双单例初始化代码
  2. 替换为统一 MasterAgent 单例
  3. 将 get_agent_master() 重定向到 get_master_agent()
  4. 生成备份和变更日志

Before (main.py):
  _master_agent = None
  _agent_master = None

  def get_master_agent():
      global _master_agent
      if _master_agent is None:
          from core.master_agent import MasterAgent
          _master_agent = MasterAgent(config_path="config.yaml")
      return _master_agent

  def get_agent_master(db=None):
      global _agent_master
      if _agent_master is None:
          from core.agents.master_agent import MasterAgent
          _agent_master = MasterAgent(db_session=db)
      return _agent_master

After (main.py):
  _master_agent = None

  def get_master_agent(db_session=None):
      global _master_agent
      if _master_agent is None:
          from core.master_agent_unified import UnifiedMasterAgent
          _master_agent = UnifiedMasterAgent(db_session=db_session)
      return _master_agent

  # deprecated 别名 — 所有调用方逐步迁移到 get_master_agent()
  def get_agent_master(db_session=None):
      return get_master_agent(db_session)
"""

import re
import shutil
from pathlib import Path
from datetime import datetime


def patch_main():
    main_path = Path("main.py")
    if not main_path.exists():
        # 尝试 api/main.py
        main_path = Path("api/main.py")
    if not main_path.exists():
        print("[!] main.py not found")
        return False

    # 备份
    backup = main_path.with_suffix(f".py.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}")
    shutil.copy2(main_path, backup)
    print(f"[✓] Backup: {backup}")

    content = main_path.read_text(encoding="utf-8")
    changes = []

    # ── 1. 移除 _agent_master 全局变量 ──
    if "_agent_master" in content:
        content = re.sub(
            r'^_agent_master\s*[=:][^\n]*\n',
            '# _agent_master removed — merged into _master_agent\n',
            content, flags=re.MULTILINE,
        )
        changes.append("removed _agent_master global")

    # ── 2. 替换 get_master_agent 函数 ──
    old_get_master = re.compile(
        r'def get_master_agent\([^)]*\):[^}]*?return _master_agent',
        re.DOTALL,
    )
    new_get_master = '''def get_master_agent(db_session=None):
    """获取统一 MasterAgent 单例 (v0+v6 合并)"""
    global _master_agent
    if _master_agent is None:
        from core.master_agent_unified import UnifiedMasterAgent
        _master_agent = UnifiedMasterAgent(db_session=db_session)
    return _master_agent'''

    if old_get_master.search(content):
        content = old_get_master.sub(new_get_master, content)
        changes.append("replaced get_master_agent()")

    # ── 3. 替换 get_agent_master 函数 ──
    old_get_agent = re.compile(
        r'def get_agent_master\([^)]*\):[^}]*?return _agent_master',
        re.DOTALL,
    )
    new_get_agent = '''def get_agent_master(db_session=None):
    """deprecated — 使用 get_master_agent()"""
    return get_master_agent(db_session)'''

    if old_get_agent.search(content):
        content = old_get_agent.sub(new_get_agent, content)
        changes.append("replaced get_agent_master() → alias")

    # ── 4. 替换导入 ──
    content = re.sub(
        r'from core\.master_agent import MasterAgent',
        'from core.master_agent_unified import UnifiedMasterAgent as MasterAgent',
        content,
    )
    content = re.sub(
        r'from core\.agents\.master_agent import MasterAgent',
        '# merged: from core.agents.master_agent import MasterAgent → unified',
        content,
    )

    if changes:
        main_path.write_text(content, encoding="utf-8")
        print(f"[✓] Patched main.py: {', '.join(changes)}")
    else:
        print("[i] No changes needed in main.py")

    return True


# ── 辅助: 扫描所有文件中的双入口引用 ──
def scan_dual_references(root: str = "."):
    """扫描项目中对双 MasterAgent 的引用"""
    patterns = [
        "get_agent_master",
        "from core.agents.master_agent import MasterAgent",
        "_agent_master",
    ]
    found = []
    for p in Path(root).rglob("*.py"):
        if ".venv" in str(p) or "__pycache__" in str(p):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
            for pat in patterns:
                if pat in text:
                    lines = [i+1 for i, line in enumerate(text.splitlines()) if pat in line]
                    found.append((str(p), pat, lines))
        except Exception:
            continue

    if found:
        print(f"\n[!] 发现 {len(found)} 处双入口引用需要迁移:")
        for path, pattern, lines in found:
            print(f"  {path}:{lines} → {pattern}")
    else:
        print("\n[✓] 无双入口引用残留")

    return found


if __name__ == "__main__":
    print("=" * 60)
    print(" MasterAgent 双单例 → 统一单例 迁移")
    print("=" * 60)
    patch_main()
    scan_dual_references()
    print("\n[完成] 请运行 pytest 验证无回归")
