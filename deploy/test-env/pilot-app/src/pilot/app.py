from fastapi import FastAPI

app = FastAPI(title="pilot-app", version="0.1.0")

# 基线: 仅 /health。新功能由 OpenHands 按任务清单实现(首个试点意图: 任务统计接口)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
