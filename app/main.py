import asyncio
import logging

from fastapi import FastAPI

from .src.routers import fabricio_delivery_router
from .src.services.consumer_service import iniciar_consumidor
from .src.services.database_service import inicializar_db
from .src.services.publisher_service import publicar_outbox_loop
from .src.services.worker_service import processar_pedidos_loop

app = FastAPI(title="Sistema de Processamento de Pedidos")


@app.on_event("startup")
async def startup():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    asyncio.create_task(asyncio.to_thread(inicializar_db, 8, 2.0))
    asyncio.create_task(processar_pedidos_loop())
    asyncio.create_task(publicar_outbox_loop())
    asyncio.create_task(iniciar_consumidor())


app.include_router(fabricio_delivery_router.router)
