from fastapi import APIRouter, HTTPException
from app.database import supabase
from app.services.algorithms import knapsack_scheduler, RoadmapGenerator

router = APIRouter()

@router.get("/{user_id}")
async def get_weekly_schedule(user_id: str):
    profile_res = (
        supabase.table("profiles")
        .select("weekly_hours")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )
    if not profile_res.data or len(profile_res.data) == 0:
        raise HTTPException(status_code=404, detail="Profile not found")

    weekly_hours = profile_res.data[0]["weekly_hours"]

    topics_res = supabase.table("topics").select("*").execute()
    prereqs_res = supabase.table("topic_prerequisites").select("*").execute()
    progress_res = (
        supabase.table("user_progress")
        .select("topic_id, status")
        .eq("user_id", user_id)
        .execute()
    )

    mastered = [
        p["topic_id"] for p in (progress_res.data or [])
        if p["status"] == "completed"
    ]

    generator = RoadmapGenerator(topics_res.data or [], prereqs_res.data or [])
    available = generator.get_next_topics(mastered, limit=20)
    schedule = knapsack_scheduler(available, weekly_hours)

    return {"user_id": user_id, **schedule}
