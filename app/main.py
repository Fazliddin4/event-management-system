from fastapi import FastAPI
from app.middlewares import origins
from fastapi.middleware.cors import CORSMiddleware
from app.routers.auth import router as auth_router
from app.routers.events import router as events_router

app = FastAPI(
    title="Event Management System",
    description="An API for managing events, users, and registrations.",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Welcome to the Event Management System API!"}

app.include_router(auth_router)
app.include_router(events_router)