import asyncio
from core.database import init_db_async

async def reset():
    print("🧹 正在清理并重建数据库（含 pgvector 扩展）...")
    # 设置为 True 会删除旧表并重新根据最新的模型定义建表
    success = await init_db_async(drop_existing=True)
    if success:
        print("✅ 数据库重置成功！")
    else:
        print("❌ 重置失败，请检查数据库日志。")

if __name__ == "__main__":
    asyncio.run(reset())