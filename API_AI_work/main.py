import uvicorn
from fastapi import FastAPI

from config.settings import settings
from routers.esp_socket import router as esp_router


app = FastAPI(title=settings.app_title)
app.include_router(esp_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host=settings.host, port=settings.port)
