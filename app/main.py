from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import assessment, roadmap, scheduler, ai, progress

app = FastAPI(title="Trailblazer API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://*.vercel.app",
        "*"  # tighten this after deployment
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(assessment.router, prefix="/api/assessment", tags=["Assessment"])
app.include_router(roadmap.router,    prefix="/api/roadmap",    tags=["Roadmap"])
app.include_router(scheduler.router,  prefix="/api/scheduler",  tags=["Scheduler"])
app.include_router(ai.router,         prefix="/api/ai",         tags=["AI"])
app.include_router(progress.router,   prefix="/api/progress",   tags=["Progress"])

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "trailblazer-api"}
