from fastapi import FastAPI

from app.routers.tmx import router

app = FastAPI()
app.include_router(router)
