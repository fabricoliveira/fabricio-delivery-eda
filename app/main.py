from app.src.configurations.logging_config import configure_logging

configure_logging()

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from sqlmodel import SQLModel

from app.src.routers import fabricio_delivery_router
from app.src.services.database_service import engine, wait_for_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await wait_for_db()
    SQLModel.metadata.drop_all(bind=engine)
    SQLModel.metadata.create_all(bind=engine)
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(fabricio_delivery_router.router)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8081)
