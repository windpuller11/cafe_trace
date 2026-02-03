from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.config import get_settings
from app.api import plots, lots, events, files

settings = get_settings()
app = FastAPI(title="咖啡处理溯源与对账系统", version="0.1.0")

app.include_router(plots.router)
app.include_router(lots.router)
app.include_router(events.router)
app.include_router(files.router)

# 静态文件：/uploads -> uploads/
upload_path = Path(settings.upload_dir)
upload_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(upload_path)), name="uploads")


@app.get("/health")
def health():
    return {"status": "ok"}
