from fastapi import FastAPI
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

from producer.src.handlers.stream_handler import stream_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stream_router)

if __name__ == "__main__":
    config = uvicorn.Config(
        "main:app", port=8000, log_level="info", host="0.0.0.0"
    )
    server = uvicorn.Server(config)
    server.run()
