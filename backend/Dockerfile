FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /app/uploads

# 启动时先等待 DB，再执行迁移，再启动服务
CMD ["sh", "-c", "sleep 3 && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
