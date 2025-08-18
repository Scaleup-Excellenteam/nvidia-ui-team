from fastapi import FastAPI
from nvidia_ui_team.models.basic_config import BasicAPIConfig
from nvidia_ui_team.routes.images import ImagesRouter
from nvidia_ui_team.routes.auth import UsersRouter
from nvidia_ui_team.routes.billing import BillingRouter
import uvicorn


def get_server():
    server = FastAPI()
    server.include_router(ImagesRouter().build())
    server.include_router(UsersRouter().build())
    server.include_router(BillingRouter().build())
    return server


app = get_server()


def main():
    config = BasicAPIConfig()
    uvicorn.run("nvidia_ui_team.main:app", host=config.host, port=config.port, reload=config.reload)


if __name__ == "__main__":
    main()
