"""Two production mounts of the same reading-list router."""

from fastapi import FastAPI

from routes import router

app = FastAPI(title="Reading list")
app.include_router(router, prefix="/api")
app.include_router(router, prefix="/preview")
