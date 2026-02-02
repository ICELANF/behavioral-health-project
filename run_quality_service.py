#!/usr/bin/env python3
"""
行为健康数字平台 - 质量审计服务（独立运行）
Quality Audit Service (Standalone)

[v14-NEW] 独立执行文件

用法：
    # 启动服务
    python run_quality_service.py
    
    # 指定端口
    python run_quality_service.py --port 8003
    
    # 指定模型
    python run_quality_service.py --model qwen2.5:14b --backend ollama
    
    # 同时启动主服务
    python run_quality_service.py --with-main

端口规划：
    - 8000: Agent Gateway
    - 8001: BAPS API
    - 8002: 决策引擎（main.py）
    - 8003: 质量审计服务（本文件）
"""
import os
import sys
import argparse
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

# 确保项目根目录在PATH中
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def create_app(
    model_name: str = "qwen2.5:14b",
    backend: str = "ollama"
) -> FastAPI:
    """
    创建质量审计服务应用
    
    Args:
        model_name: 评判模型名称
        backend: 后端类型 (ollama/dify)
    
    Returns:
        FastAPI应用实例
    """
    # 设置环境变量
    os.environ["QUALITY_JUDGE_MODEL"] = model_name
    os.environ["QUALITY_JUDGE_BACKEND"] = backend
    
    app = FastAPI(
        title="行为健康平台 - 质量审计服务",
        version="14.0.0",
        description="AI响应质量审计API（独立服务）"
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 导入并挂载质量审计路由
    from api.v14.quality_routes import router as quality_router
    app.include_router(quality_router, prefix="/api/v2")
    
    # 健康检查
    @app.get("/")
    def root():
        return {
            "service": "quality-audit",
            "version": "v14",
            "status": "online",
            "model": model_name,
            "backend": backend
        }
    
    @app.get("/health")
    def health():
        return {"status": "healthy", "service": "quality-audit"}
    
    logger.info(f"[Quality] 服务已创建: model={model_name} backend={backend}")
    
    return app


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        description="质量审计服务",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    # 默认启动（端口8003）
    python run_quality_service.py
    
    # 使用Dify作为评判后端
    python run_quality_service.py --backend dify
    
    # 指定模型
    python run_quality_service.py --model gpt-4o-mini
        """
    )
    
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8003,
        help="服务端口 (默认: 8003)"
    )
    
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="监听地址 (默认: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--model", "-m",
        default=os.getenv("QUALITY_JUDGE_MODEL", "qwen2.5:14b"),
        help="评判模型 (默认: qwen2.5:14b)"
    )
    
    parser.add_argument(
        "--backend", "-b",
        choices=["ollama", "dify", "openai"],
        default=os.getenv("QUALITY_JUDGE_BACKEND", "ollama"),
        help="LLM后端 (默认: ollama)"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        help="开发模式（热重载）"
    )
    
    parser.add_argument(
        "--with-main",
        action="store_true",
        help="同时启动主决策引擎服务（端口8002）"
    )
    
    args = parser.parse_args()
    
    # 打印启动信息
    print(f"""
╔═══════════════════════════════════════════════════════╗
║       行为健康平台 - 质量审计服务 v14                    ║
╠═══════════════════════════════════════════════════════╣
║  端口: {args.port}                                          ║
║  模型: {args.model:<40}      ║
║  后端: {args.backend:<40}      ║
╚═══════════════════════════════════════════════════════╝
""")
    
    # 如果需要同时启动主服务
    if args.with_main:
        import subprocess
        import threading
        
        def run_main_service():
            subprocess.run([
                sys.executable, "main.py"
            ], cwd=project_root)
        
        main_thread = threading.Thread(target=run_main_service, daemon=True)
        main_thread.start()
        logger.info("[Quality] 主服务(8002)已在后台启动")
    
    # 创建并启动应用
    app = create_app(
        model_name=args.model,
        backend=args.backend
    )
    
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload
    )


if __name__ == "__main__":
    main()
