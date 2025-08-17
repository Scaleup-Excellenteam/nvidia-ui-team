from fastapi import FastAPI
from tel_hai.models.basic_config import BasicAPIConfig
from tel_hai.routes.images import ImagesRouter
import uvicorn


def get_server():
    server = FastAPI()
    server.include_router(ImagesRouter().build())
    return server


def main():
    config = BasicAPIConfig()
    uvicorn.run("tel_hai.main:get_server", host=config.host, port=config.port, reload=config.reload)


if __name__ == "__main__":
    main()
