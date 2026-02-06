# ==============================================
# Expert Review Workbench - Streamlit
# Port: 8501
# ==============================================

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

WORKDIR /app

# Install workbench dependencies
COPY workbench/requirements.txt /app/workbench/requirements.txt
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn -r /app/workbench/requirements.txt

# Copy disclosure module (required by expert_review.py)
COPY disclosure/ /app/disclosure/

# Copy workbench source
COPY workbench/expert_review.py /app/workbench/expert_review.py

RUN chown -R appuser:appuser /app

EXPOSE 8501

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "workbench/expert_review.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]
