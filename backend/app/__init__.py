from fastapi import FastAPI

from .routers import products, chat, admin


def create_app() -> FastAPI:
    app = FastAPI(
        title="Traya Product Discovery Assistant",
        version="0.1.0",
    )

    app.include_router(products.router, prefix="/products", tags=["products"])
    app.include_router(chat.router, prefix="/chat", tags=["chat"])
    app.include_router(admin.router, prefix="/admin", tags=["admin"])

    return app


