from contextlib import asynccontextmanager
import os

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import AppError, app_error_handler
from app.core.logging import get_logger, new_request_id, request_id_ctx, setup_logging
from app.db import models
from app.services.yuanqi_client import YuanqiClient

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    client = YuanqiClient(settings)
    app.state.yuanqi = client
    logger.info("应用启动")
    yield
    await client.aclose()
    logger.info("应用关闭")


def create_app() -> FastAPI:
    setup_logging()
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        lifespan=lifespan,
        debug=settings.debug,
        swagger_ui_parameters={"persistAuthorization": True},
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        rid = request.headers.get("X-Request-ID") or new_request_id()
        token = request_id_ctx.set(rid)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = rid
            return response
        finally:
            request_id_ctx.reset(token)

    app.add_exception_handler(AppError, app_error_handler)

    # 托管前端静态文件（必须在根路由之前）
    frontend_path = "/home/ubuntu/Legal_Assistant/frontend"
    if os.path.exists(frontend_path):
        app.mount("/static", StaticFiles(directory=frontend_path), name="static")
        logger.info(f"静态文件托管: {frontend_path}")
        
        # 手动处理根路由返回 index.html
        @app.get("/")
        async def root():
            from fastapi.responses import FileResponse
            index_path = os.path.join(frontend_path, "index.html")
            if os.path.exists(index_path):
                return FileResponse(index_path)
            return {"service": settings.app_name, "docs": "/docs"}
    else:
        @app.get("/")
        async def root() -> dict[str, str]:
            return {"service": settings.app_name, "docs": "/docs"}

    app.include_router(api_router)
    return app


app = create_app()
