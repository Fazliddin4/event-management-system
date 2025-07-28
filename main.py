from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.middlewares import ProcessTimeLoggerMiddleware, origins, SimplePrintLoggerMiddleware
from app.routers.jwt import router as auth_router
from app.routers.events import router as event_router


app = FastAPI(
    title="Event-Management_System",
    description="An event management system helps event planners and organizers streamline their pre-event planning, event day execution and post-event operations ",
    version="0.1.0",
)

app.add_middleware(SimplePrintLoggerMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ProcessTimeLoggerMiddleware)


@app.get("/")
async def root():
    return {"message": "Hello World"}



app.include_router(auth_router)
app.include_router(event_router)


