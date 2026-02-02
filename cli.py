"""
Behavioral Health Platform - CLI Interface
行为健康平台命令行工具

支持命令：
- serve: 启动API服务器
- init: 初始化系统
- test: 运行测试
- status: 检查系统状态
- db: 数据库管理
"""
import click
import sys
import os
from pathlib import Path
from typing import Optional

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


@click.group()
@click.version_option(version="0.1.0", prog_name="behavioral-health")
def main():
    """
    行为健康平台 - 多模态AI健康管理系统

    Behavioral Health Platform - Multimodal AI Health Management System
    """
    pass


@main.command()
@click.option("--host", default="127.0.0.1", help="服务器主机地址")
@click.option("--port", default=8000, type=int, help="服务器端口")
@click.option("--reload", is_flag=True, help="启用热重载（开发模式）")
@click.option("--workers", default=1, type=int, help="工作进程数")
def serve(host: str, port: int, reload: bool, workers: int):
    """启动API服务器"""
    click.echo(click.style("=" * 60, fg="cyan"))
    click.echo(click.style("[START] 行为健康平台 - 启动中...", fg="green", bold=True))
    click.echo(click.style("=" * 60, fg="cyan"))

    # 检查环境变量
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        click.echo(click.style("[WARN]  警告：未找到 .env 文件", fg="yellow"))
        click.echo("提示：复制 .env.example 并配置后再运行")
        if not click.confirm("是否继续？", default=False):
            sys.exit(1)

    click.echo(f"[LOC] 主机: {host}:{port}")
    click.echo(f"[RELOAD] 热重载: {'启用' if reload else '禁用'}")
    click.echo(f"[WORKERS] 工作进程: {workers}")
    click.echo()

    try:
        import uvicorn
        from dotenv import load_dotenv

        # 加载环境变量
        load_dotenv(env_path)

        # 启动服务器
        uvicorn.run(
            "api.main:app",
            host=host,
            port=port,
            reload=reload,
            workers=1 if reload else workers,
            log_level="info"
        )
    except ImportError as e:
        click.echo(click.style(f"[ERROR] 错误：缺少依赖 - {e}", fg="red"))
        click.echo("请运行：pip install -r requirements.txt")
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo(click.style("\n\n[BYE] 服务已停止", fg="yellow"))
    except Exception as e:
        click.echo(click.style(f"[ERROR] 错误：{e}", fg="red"))
        sys.exit(1)


@main.command()
@click.option("--force", is_flag=True, help="强制重新初始化")
def init(force: bool):
    """初始化系统（数据库、配置等）"""
    click.echo(click.style("=" * 60, fg="cyan"))
    click.echo(click.style("[INIT] 系统初始化", fg="green", bold=True))
    click.echo(click.style("=" * 60, fg="cyan"))

    # 1. 检查.env文件
    env_path = PROJECT_ROOT / ".env"
    env_example = PROJECT_ROOT / ".env.example"

    if not env_path.exists():
        if env_example.exists():
            click.echo("[CREATE] 创建 .env 文件...")
            import shutil
            shutil.copy(env_example, env_path)
            click.echo(click.style("[OK] .env 文件已创建", fg="green"))
            click.echo(click.style("[WARN]  请编辑 .env 文件配置数据库等信息", fg="yellow"))
        else:
            click.echo(click.style("[ERROR] 未找到 .env.example", fg="red"))
            sys.exit(1)
    else:
        click.echo(click.style("[OK] .env 文件已存在", fg="green"))

    # 2. 创建必要的目录
    click.echo("\n[DIR] 创建必要目录...")
    dirs_to_create = [
        "data/profiles",
        "data/assessments",
        "data/logs",
        "data/uploads",
    ]

    for dir_path in dirs_to_create:
        full_path = PROJECT_ROOT / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        click.echo(f"  [OK] {dir_path}")

    # 3. 数据库初始化（如果已安装SQLAlchemy）
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)

        click.echo("\n[DB] 数据库初始化...")

        # 这里可以添加数据库初始化逻辑
        # 例如：调用 alembic upgrade head
        click.echo("  [INFO]  数据库Schema待定义（后续实现）")

    except ImportError:
        click.echo(click.style("[WARN]  跳过数据库初始化（缺少依赖）", fg="yellow"))

    # 4. 验证关键服务
    click.echo("\n[CHECK] 验证外部服务...")

    # 检查Ollama
    try:
        import httpx
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        response = httpx.get(f"{ollama_url}/api/tags", timeout=2)
        if response.status_code == 200:
            click.echo(click.style(f"  [OK] Ollama服务正常 ({ollama_url})", fg="green"))
        else:
            click.echo(click.style(f"  [WARN]  Ollama响应异常", fg="yellow"))
    except:
        click.echo(click.style("  [FAIL] Ollama服务未运行", fg="red"))
        click.echo("    提示：请先启动 Ollama")

    # 检查多模态系统（如果配置了）
    multimodal_url = os.getenv("MULTIMODAL_API_URL", "http://localhost:8090")
    try:
        response = httpx.get(f"{multimodal_url}/health", timeout=2)
        if response.status_code == 200:
            click.echo(click.style(f"  [OK] 多模态系统正常 ({multimodal_url})", fg="green"))
        else:
            click.echo(click.style("  [WARN]  多模态系统响应异常", fg="yellow"))
    except:
        click.echo(click.style("  [INFO]  多模态系统未运行（可选服务）", fg="blue"))

    click.echo(click.style("\n[SUCCESS] 初始化完成！", fg="green", bold=True))
    click.echo("\n下一步：")
    click.echo("  1. 编辑 .env 文件配置必要参数")
    click.echo("  2. 运行 'python -m behavioral_health serve' 启动服务")


@main.command()
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
def status(verbose: bool):
    """检查系统状态"""
    click.echo(click.style("=" * 60, fg="cyan"))
    click.echo(click.style("[STATS] 系统状态检查", fg="green", bold=True))
    click.echo(click.style("=" * 60, fg="cyan"))

    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")

    # 检查Python环境
    click.echo("\n[PYTHON] Python环境：")
    click.echo(f"  版本: {sys.version.split()[0]}")
    click.echo(f"  路径: {sys.executable}")

    # 检查关键目录
    click.echo("\n[DIR] 目录结构：")
    key_dirs = ["core", "api", "agents", "knowledge", "data"]
    for dir_name in key_dirs:
        dir_path = PROJECT_ROOT / dir_name
        status_icon = "[OK]" if dir_path.exists() else "[FAIL]"
        color = "green" if dir_path.exists() else "red"
        click.echo(click.style(f"  {status_icon} {dir_name}/", fg=color))

    # 检查配置文件
    click.echo("\n[CONFIG] 配置文件：")
    config_files = [".env", "config.yaml", "architecture.yaml"]
    for file_name in config_files:
        file_path = PROJECT_ROOT / file_name
        status_icon = "[OK]" if file_path.exists() else "[FAIL]"
        color = "green" if file_path.exists() else "red"
        click.echo(click.style(f"  {status_icon} {file_name}", fg=color))

    # 检查外部服务
    click.echo("\n[SERVICE] 外部服务：")
    services = [
        ("Ollama", os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"), "/api/tags"),
        ("多模态系统", os.getenv("MULTIMODAL_API_URL", "http://localhost:8090"), "/health"),
        ("Dify", "http://localhost:8080", "/health"),
    ]

    import httpx
    for name, base_url, path in services:
        try:
            response = httpx.get(f"{base_url}{path}", timeout=2)
            if response.status_code == 200:
                click.echo(click.style(f"  [OK] {name} ({base_url})", fg="green"))
            else:
                click.echo(click.style(f"  [WARN]  {name} - 响应异常", fg="yellow"))
        except httpx.ConnectError:
            click.echo(click.style(f"  [FAIL] {name} - 连接失败", fg="red"))
        except:
            click.echo(click.style(f"  ? {name} - 未知状态", fg="blue"))

    click.echo(click.style("\n" + "=" * 60, fg="cyan"))


@main.command()
@click.option("--pattern", "-p", default="tests/", help="测试文件路径或模式")
@click.option("--verbose", "-v", is_flag=True, help="显示详细输出")
def test(pattern: str, verbose: bool):
    """运行测试套件"""
    click.echo(click.style("=" * 60, fg="cyan"))
    click.echo(click.style("[TEST] 运行测试", fg="green", bold=True))
    click.echo(click.style("=" * 60, fg="cyan"))

    try:
        import pytest

        args = [pattern]
        if verbose:
            args.append("-v")
        else:
            args.append("-q")

        # 运行pytest
        exit_code = pytest.main(args)

        if exit_code == 0:
            click.echo(click.style("\n[SUCCESS] 所有测试通过！", fg="green", bold=True))
        else:
            click.echo(click.style(f"\n[ERROR] 测试失败（退出码: {exit_code}）", fg="red"))
            sys.exit(exit_code)
    except ImportError:
        click.echo(click.style("[ERROR] pytest未安装", fg="red"))
        click.echo("请运行：pip install pytest pytest-asyncio")
        sys.exit(1)


@main.group()
def db():
    """数据库管理命令"""
    pass


@db.command()
@click.option("--drop", is_flag=True, help="删除现有表后重新创建")
@click.option("--sample-data", is_flag=True, help="同时加载示例数据")
def init(drop: bool, sample_data: bool):
    """初始化数据库"""
    click.echo(click.style("=" * 60, fg="cyan"))
    click.echo(click.style("[DATABASE INIT] 数据库初始化", fg="green", bold=True))
    click.echo(click.style("=" * 60, fg="cyan"))

    if drop:
        if not click.confirm("[WARN]  确定要删除所有现有表吗？", default=False):
            click.echo("操作已取消")
            return

    try:
        from core.database import init_database, check_database_connection, get_database_info

        # 1. 检查连接
        click.echo("\n[1/3] 检查数据库连接...")
        if not check_database_connection():
            click.echo(click.style("  [FAIL] 数据库连接失败", fg="red"))
            click.echo("\n提示：请检查 .env 中的 DATABASE_URL 配置")
            sys.exit(1)

        db_info = get_database_info()
        click.echo(click.style(f"  [OK] 数据库连接成功", fg="green"))
        click.echo(f"    类型: {db_info['dialect']}")
        click.echo(f"    位置: {db_info['url']}")

        # 2. 创建表
        click.echo("\n[2/3] 创建数据库表...")
        if init_database(drop_existing=drop):
            click.echo(click.style("  [OK] 数据库表创建成功", fg="green"))
            click.echo("    - users (用户表)")
            click.echo("    - assessments (评估记录表)")
            click.echo("    - trigger_records (触发器记录表)")
            click.echo("    - interventions (干预记录表)")
            click.echo("    - user_sessions (会话表)")
            click.echo("    - health_data (健康数据表)")
        else:
            click.echo(click.style("  [FAIL] 表创建失败", fg="red"))
            sys.exit(1)

        # 3. 加载种子数据（如果指定）
        if sample_data:
            click.echo("\n[3/3] 加载种子数据...")
            from scripts.seed_data import seed_all
            seed_all()
        else:
            click.echo("\n[3/3] 跳过种子数据加载")
            click.echo("  提示：运行 'python -m behavioral_health db seed' 加载示例数据")

        click.echo(click.style("\n[SUCCESS] 数据库初始化完成！", fg="green", bold=True))

    except ImportError as e:
        click.echo(click.style(f"[ERROR] 导入失败: {e}", fg="red"))
        click.echo("提示：确保已安装所有依赖")
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"[ERROR] 初始化失败: {e}", fg="red"))
        import traceback
        traceback.print_exc()
        sys.exit(1)


@db.command()
@click.option("--clear", is_flag=True, help="清空现有数据后重新加载")
def seed(clear: bool):
    """加载种子数据"""
    click.echo(click.style("=" * 60, fg="cyan"))
    click.echo(click.style("[SEED DATA] 加载种子数据", fg="green", bold=True))
    click.echo(click.style("=" * 60, fg="cyan"))

    if clear:
        if not click.confirm("[WARN]  确定要清空所有现有数据吗？", default=False):
            click.echo("操作已取消")
            return

    try:
        from core.database import check_database_connection, clear_all_data

        # 检查连接
        if not check_database_connection():
            click.echo(click.style("[ERROR] 数据库连接失败", fg="red"))
            sys.exit(1)

        # 清空数据（如果指定）
        if clear:
            click.echo("\n清空现有数据...")
            if clear_all_data():
                click.echo(click.style("  [OK] 数据已清空", fg="green"))
            else:
                click.echo(click.style("  [FAIL] 清空失败", fg="red"))
                sys.exit(1)

        # 加载种子数据
        click.echo("\n加载种子数据...")
        from scripts.seed_data import seed_all
        seed_all()

        click.echo(click.style("\n[SUCCESS] 种子数据加载完成！", fg="green", bold=True))

    except ImportError as e:
        click.echo(click.style(f"[ERROR] 导入失败: {e}", fg="red"))
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"[ERROR] 加载失败: {e}", fg="red"))
        import traceback
        traceback.print_exc()
        sys.exit(1)


@db.command()
def stats():
    """查看数据库统计信息"""
    click.echo(click.style("=" * 60, fg="cyan"))
    click.echo(click.style("[DATABASE STATS] 数据库统计", fg="green", bold=True))
    click.echo(click.style("=" * 60, fg="cyan"))

    try:
        from core.database import check_database_connection, get_table_counts, get_database_info

        # 检查连接
        if not check_database_connection():
            click.echo(click.style("[ERROR] 数据库连接失败", fg="red"))
            sys.exit(1)

        # 数据库信息
        db_info = get_database_info()
        click.echo("\n数据库信息:")
        click.echo(f"  类型: {db_info['dialect']}")
        click.echo(f"  位置: {db_info['url']}")

        # 表记录数
        counts = get_table_counts()
        click.echo("\n表记录统计:")
        total = 0
        for table, count in counts.items():
            click.echo(f"  {table:20s}: {count:>6d} 条")
            total += count

        click.echo(f"  {'总计':20s}: {total:>6d} 条")

    except Exception as e:
        click.echo(click.style(f"[ERROR] 获取统计失败: {e}", fg="red"))
        sys.exit(1)


@db.command()
def migrate():
    """执行数据库迁移"""
    click.echo(click.style("[MIGRATE] 执行数据库迁移", fg="yellow"))
    click.echo("  [INFO]  功能待实现（考虑使用Alembic）")
    click.echo("\n当前可用操作:")
    click.echo("  - python -m behavioral_health db init --drop  # 重建所有表")
    click.echo("  - python -m behavioral_health db seed --clear # 重载数据")


@main.group()
def user():
    """用户管理命令"""
    pass


@user.command()
@click.argument("username")
@click.option("--email", prompt=True, help="邮箱地址")
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True, help="密码")
@click.option("--admin", is_flag=True, help="创建管理员用户")
def create(username: str, email: str, password: str, admin: bool):
    """创建新用户"""
    click.echo(click.style(f"[USER] 创建用户: {username}", fg="green"))
    click.echo(f"  邮箱: {email}")
    click.echo(f"  角色: {'管理员' if admin else '普通用户'}")

    # 这里添加用户创建逻辑
    click.echo("  [INFO]  功能待实现")


@user.command()
def list():
    """列出所有用户"""
    click.echo(click.style("[USERS] 用户列表", fg="green"))
    click.echo("  [INFO]  功能待实现")


if __name__ == "__main__":
    main()
