from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database import supabase

router = APIRouter()

class UpdateProgressRequest(BaseModel):
    user_id: str
    topic_id: str
    status: str
    mastery_score: float = 100.0

@router.post("/update")
async def update_progress(request: UpdateProgressRequest):
    # Clamp mastery score to max 99.99 for numeric(5,2)
    score = min(float(request.mastery_score), 99.99)

    existing = (
        supabase.table("user_progress")
        .select("id")
        .eq("user_id", request.user_id)
        .eq("topic_id", request.topic_id)
        .limit(1)
        .execute()
    )

    if existing.data:
        supabase.table("user_progress").update({
            "status": request.status,
            "mastery_score": score,
        }).eq("user_id", request.user_id).eq("topic_id", request.topic_id).execute()
    else:
        supabase.table("user_progress").insert({
            "user_id": request.user_id,
            "topic_id": request.topic_id,
            "status": request.status,
            "mastery_score": score,
        }).execute()

    if request.status == "completed":
        prereqs = (
            supabase.table("topic_prerequisites")
            .select("topic_id")
            .eq("prerequisite_id", request.topic_id)
            .execute()
        )
        for prereq in (prereqs.data or []):
            dependent_id = prereq["topic_id"]
            all_prereqs = (
                supabase.table("topic_prerequisites")
                .select("prerequisite_id")
                .eq("topic_id", dependent_id)
                .execute()
            )
            all_completed = True
            for p in (all_prereqs.data or []):
                prog = (
                    supabase.table("user_progress")
                    .select("status")
                    .eq("user_id", request.user_id)
                    .eq("topic_id", p["prerequisite_id"])
                    .limit(1)
                    .execute()
                )
                if not prog.data or prog.data[0]["status"] != "completed":
                    all_completed = False
                    break
            if all_completed:
                current = (
                    supabase.table("user_progress")
                    .select("status")
                    .eq("user_id", request.user_id)
                    .eq("topic_id", dependent_id)
                    .limit(1)
                    .execute()
                )
                if current.data and current.data[0]["status"] == "locked":
                    supabase.table("user_progress").update({
                        "status": "unlocked"
                    }).eq("user_id", request.user_id).eq("topic_id", dependent_id).execute()

    return {"message": "Progress updated", "status": request.status}

@router.get("/{user_id}")
async def get_progress(user_id: str):
    result = (
        supabase.table("user_progress")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )
    return {"user_id": user_id, "progress": result.data or []}
