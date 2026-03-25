from fastapi import FastAPI
from core.config import settings
from routers import doc_router, chat_router, auth_router
from core.observability import RequestContextMiddleware, configure_logging, init_sentry
from fastapi.middleware.cors import CORSMiddleware

configure_logging()
init_sentry()

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(doc_router.router)
app.include_router(chat_router.router)
app.include_router(auth_router.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}
    
