import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from utilities.utils import init_database
from routes import (
    auth,
    scrapper,
)


logging.config.fileConfig("logging.conf", disable_existing_loggers=False)
logger = logging.getLogger(__name__)

ORIGINS = [
    "*",
]

app = FastAPI(
    title="Instagram Scraper",
    version="0.1",
    responses={
        404: {"description": "Not found"},
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router)
app.include_router(scrapper.router)



@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Hello World"}


@app.on_event("startup")
async def startup_event():
    logger.info("Starting up...")
    await init_database(is_srv=True)