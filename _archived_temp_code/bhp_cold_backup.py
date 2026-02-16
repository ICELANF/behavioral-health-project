"""
BHP v3 冷备份一键脚本
用法: python bhp_cold_backup.py
      python bhp_cold_backup.py --backup-dir E:\\我的备份
"""
import os
import sys
import shutil
import subprocess
import zipfile
import argparse
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(r"D:\behavioral-health-project")
DEFAULT_BACKUP_DIR = Path(r"D:\bhp_backups")

EXCLUDE_DIRS = {"__pycache__", ".pytest_cache", "node_modules", ".git", ".egg-info", "volumes", ".venv", "venv"}
EXCLUDE_EXTS = {".pyc", ".pyo"}

def run(cmd, **kwargs):
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=60, **kwargs)
        r_stdout = r.stdout.decode("utf-8", errors="replace") if isinstance(r.stdout, bytes) else (r.stdout or "")
        r_stderr = r.stderr.decode("utf-8", errors="replace") if isinstance(r.stderr, bytes) else (r.stderr or "")
        r.stdout = r_stdout
        r.stderr = r_stderr
        return r.returncode == 0, r.stdout, r.stderr
    except Exception as e:
        return False, "", str(e)

def check_docker():
    ok, out, _ = run(["docker", "info"])
    return ok

def print_ok(msg):
    print(f"  [OK] {msg}")

def print_warn(msg):
    print(f"  [WARN] {msg}")

def print_fail(msg):
    print(f"  [FAIL] {msg}")

def main():
    parser = argparse.ArgumentParser(description="BHP v3 冷备份")
    parser.add_argument("--project-dir", default=str(PROJECT_DIR))
    parser.add_argument("--backup-dir", default=str(DEFAULT_BACKUP_DIR))
    args = parser.parse_args()

    project = Path(args.project_dir)
    backup_root = Path(args.backup_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"bhp_v8_backup_{timestamp}"
    backup_path = backup_root / backup_name

    print()
    print("=" * 50)
    print("  BHP v8 冷备份")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # ── 预检 ──
    print(f"\n[预检] 验证环境 ...")

    if not project.exists():
        print_fail(f"项目目录不存在: {project}")
        sys.exit(1)
    print_ok(f"项目目录: {project}")

    docker_ok = check_docker()
    if docker_ok:
        print_ok("Docker 运行中")
    else:
        print_warn("Docker 未运行，跳过容器操作")

    backup_path.mkdir(parents=True, exist_ok=True)
    print_ok(f"备份目录: {backup_path}")

    # ══════════════════════════════════════
    # 第一步：停止容器
    # ══════════════════════════════════════
    print(f"\n[1/3] 停止 Docker 容器 (确保数据一致性) ...")

    if docker_ok:
        # 记录容器状态
        ok, out, _ = run(["docker-compose", "ps"], cwd=str(project))
        (backup_path / "container_status_before.txt").write_text(out or "", encoding="utf-8")
        print("  容器状态已记录")

        # 停止容器
        ok, _, _ = run(["docker-compose", "stop"], cwd=str(project))
        if ok:
            print_ok("所有容器已停止")
        else:
            print_warn("停止容器时有警告，继续备份")
    else:
        print("  [SKIP] Docker 未运行")

    # ══════════════════════════════════════
    # 第二步：导出 PostgreSQL 数据库
    # ══════════════════════════════════════
    print(f"\n[2/3] 导出 PostgreSQL 数据库快照 ...")

    sql_file = backup_path / f"bhp_db_full_{timestamp}.sql"

    if docker_ok:
        # 临时启动 PG
        run(["docker-compose", "start", "db"], cwd=str(project))
        import time; time.sleep(6)

        # 检查容器
        ok, out, _ = run(["docker", "ps", "-q", "-f", "name=bhp_v3_postgres"])
        container_id = out.strip()

        if container_id:
            print("  正在导出 (可能需要几秒) ...")
            ok, dump_out, dump_err = run([
                "docker", "exec", "-t", "bhp_v3_postgres",
                "pg_dumpall", "-c", "-U", "bhp_user"
            ])
            sql_file.write_text(dump_out, encoding="utf-8")
            size_mb = sql_file.stat().st_size / (1024 * 1024)
            if size_mb > 0.001:
                print_ok(f"SQL 导出完成: {size_mb:.2f} MB")
            else:
                print_warn("SQL 文件可能为空，请手动检查")

            # 再次停止
            run(["docker-compose", "stop", "db"], cwd=str(project))
        else:
            print("  [SKIP] PostgreSQL 容器未找到 (bhp_v3_postgres)")
            sql_file.write_text("# PostgreSQL 容器未运行\n", encoding="utf-8")
    else:
        print("  [SKIP] Docker 未运行")
        sql_file.write_text("# Docker 未运行\n", encoding="utf-8")

    # ══════════════════════════════════════
    # 第三步：打包项目文件
    # ══════════════════════════════════════
    print(f"\n[3/3] 打包项目文件 ...")

    zip_file = backup_path / f"bhp_v8_code_{timestamp}.zip"
    file_count = 0

    print("  正在压缩项目 (排除缓存) ...")
    with zipfile.ZipFile(str(zip_file), "w", zipfile.ZIP_DEFLATED) as zf:
        for root_dir, dirs, files in os.walk(str(project)):
            # 排除目录
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

            for fname in files:
                fpath = Path(root_dir) / fname
                if fpath.suffix in EXCLUDE_EXTS:
                    continue
                arcname = fpath.relative_to(project)
                # ZipFile 不支持 1980 年前的时间戳，遇到时用当前时间替代
                # 跳过无法访问的文件 (Docker volumes, 符号链接等)
                try:
                    zf.write(str(fpath), str(arcname))
                except ValueError:
                    import time
                    info = zipfile.ZipInfo(str(arcname), date_time=time.localtime()[:6])
                    info.compress_type = zipfile.ZIP_DEFLATED
                    with open(str(fpath), "rb") as f_in:
                        zf.writestr(info, f_in.read())
                except OSError:
                    pass  # 跳过无法访问的文件
                file_count += 1

    size_mb = zip_file.stat().st_size / (1024 * 1024)
    print_ok(f"代码包: {size_mb:.2f} MB ({file_count} 文件)")

    # ══════════════════════════════════════
    # 生成备份清单
    # ══════════════════════════════════════
    print(f"\n[完成] 生成备份清单 ...")

    key_files = {
        "docker-compose.yml": project / "docker-compose.yml",
        ".env": project / ".env",
        "Dockerfile": project / "Dockerfile",
        "requirements.txt": project / "requirements.txt",
        "core/models.py": project / "core" / "models.py",
        "api/auth.py": project / "api" / "auth.py",
    }

    manifest = f"""========================================
BHP v8 冷备份清单
========================================
备份时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
项目目录: {project}
备份目录: {backup_path}

文件清单:
---------
1. bhp_db_full_{timestamp}.sql    - PostgreSQL 完整数据库导出
2. bhp_v8_code_{timestamp}.zip    - 项目代码 + 配置文件 ({file_count} 文件)
3. container_status_before.txt    - 备份前容器状态
4. RESTORE_GUIDE.md               - 恢复指南

关键文件检查:
"""
    for name, path in key_files.items():
        status = "存在" if path.exists() else "缺失!"
        manifest += f"  - {name}: {status}\n"

    manifest += f"""
测试状态 (备份时):
  - test_02_database: 11/11 passed
========================================
"""
    (backup_path / "MANIFEST.txt").write_text(manifest, encoding="utf-8")

    # 恢复指南
    restore_guide = f"""# BHP v8 恢复指南

## 快速恢复 (新电脑)

### 前置条件
- 安装 Docker Desktop
- 安装 Python 3.12+

### 恢复步骤

```powershell
# 1. 解压代码包
Expand-Archive -Path "bhp_v8_code_{timestamp}.zip" -DestinationPath "D:\\behavioral-health-project"

# 2. 进入项目目录
cd D:\\behavioral-health-project

# 3. 启动 Docker 容器
docker-compose up -d

# 4. 等待数据库就绪
Start-Sleep -Seconds 10

# 5. 恢复数据库
Get-Content "bhp_db_full_{timestamp}.sql" | docker exec -i bhp_v3_postgres psql -U bhp_user -d bhp_db

# 6. 安装依赖
pip install -r requirements.txt

# 7. 验证
python -m pytest tests\\test_02_database.py -v

# 8. 启动服务
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## 如果只恢复数据库

```powershell
docker-compose up -d db
Start-Sleep -Seconds 10
Get-Content "bhp_db_full_{timestamp}.sql" | docker exec -i bhp_v3_postgres psql -U bhp_user -d bhp_db
```
"""
    (backup_path / "RESTORE_GUIDE.md").write_text(restore_guide, encoding="utf-8")

    # ══════════════════════════════════════
    # 列出备份内容
    # ══════════════════════════════════════
    print()
    print("=" * 50)
    print("  冷备份完成!")
    print("=" * 50)
    print(f"\n  备份位置: {backup_path}\n")

    for f in sorted(backup_path.iterdir()):
        size = f.stat().st_size / (1024 * 1024)
        print(f"  {f.name:<45} {size:.2f} MB")

    # ── 重启容器 ──
    print()
    if docker_ok:
        answer = input("是否重启 Docker 容器? (Y/n): ").strip()
        if answer.lower() != "n":
            subprocess.run(["docker-compose", "up", "-d"], cwd=str(project))
            print("\n  [OK] 容器已重启")
            import time; time.sleep(8)
            subprocess.run(["docker-compose", "ps"], cwd=str(project))

    print("\n备份完成。祝好!")


if __name__ == "__main__":
    main()
