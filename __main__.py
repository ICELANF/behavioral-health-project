"""
Behavioral Health Platform - Main Entry Point
行为健康平台主入口

使用方式：
    python -m behavioral_health [command] [options]

示例：
    python -m behavioral_health serve
    python -m behavioral_health init
    python -m behavioral_health status
    python -m behavioral_health test
"""
from cli import main

if __name__ == "__main__":
    main()
