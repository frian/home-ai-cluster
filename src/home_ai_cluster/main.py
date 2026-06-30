from fastapi import FastAPI

from home_ai_cluster.api.routes import router


def create_app() -> FastAPI:
    app = FastAPI(title="Home AI Cluster")
    app.include_router(router)
    return app


app = create_app()
