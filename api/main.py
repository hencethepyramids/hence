import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.routers import players, servers, sessions
from api.services.poller import BattleMetricsPoller

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    poller = BattleMetricsPoller()
    task = asyncio.create_task(poller.run())
    logger.info("BattleMetrics polling task started")
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        logger.info("BattleMetrics polling task stopped")


app = FastAPI(
    title="Hence API",
    description="ARK: Survival Ascended player tracking backend",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(players.router, prefix="/players", tags=["players"])
app.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
app.include_router(servers.router, prefix="/servers", tags=["servers"])


@app.get("/health")
async def health():
    return {"status": "ok"}
