from fastapi import APIRouter, BackgroundTasks
from fastapi.params import Depends

from producer.src.services.stream_service import StreamService
from producer.src.services.stream_service_interface import StreamServiceInterface

stream_router = APIRouter(tags=["stream"])

@stream_router.get("/live")
def live(background_task: BackgroundTasks, stream_service: StreamServiceInterface = Depends(StreamService)):
    background_task.add_task(stream_service.start_trace)
    return {"status": "ok"}