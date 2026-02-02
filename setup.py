"""
Behavioral Health Platform - Setup Configuration
行为健康平台安装配置
"""
from setuptools import setup, find_packages
from pathlib import Path

# 读取README（如果存在）
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    long_description = readme_file.read_text(encoding="utf-8")

# 读取requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    with open(requirements_file) as f:
        requirements = [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        ]

setup(
    name="behavioral-health",
    version="0.1.0",
    author="Behavioral Health Team",
    author_email="team@behavioral-health.com",
    description="多模态AI行为健康管理平台 - Multimodal AI Behavioral Health Management Platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/behavioral-health-project",
    packages=find_packages(
        exclude=["tests", "tests.*", "docs", "*.tests", "*.tests.*"]
    ),
    include_package_data=True,
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=9.0.2",
            "pytest-asyncio>=1.3.0",
            "black>=23.12.0",
            "ruff>=0.1.9",
            "mypy>=1.8.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "bh=cli:main",
            "behavioral-health=cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Healthcare Industry",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    keywords="healthcare AI behavioral-health multimodal assessment",
    project_urls={
        "Documentation": "https://github.com/your-org/behavioral-health-project/docs",
        "Source": "https://github.com/your-org/behavioral-health-project",
        "Bug Reports": "https://github.com/your-org/behavioral-health-project/issues",
    },
)
