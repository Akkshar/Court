from fastapi import FastAPI
from app.core.settings import settings
from app.routes import auth, cases, jury

app = FastAPI(title=settings.APP_NAME)

app.include_router(auth.router)
app.include_router(cases.router)
app.include_router(jury.router)

@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "env": settings.ENV}