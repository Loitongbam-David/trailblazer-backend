from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database import supabase
from app.services.groq_service import synthesize_study_guide, tutor_chat

router = APIRouter()


class SynthesizeRequest(BaseModel):
    topic_id: str
    raw_context: str = ""


class ChatMessage(BaseModel):
    role: str
    content: str


class TutorRequest(BaseModel):
    user_id: str
    topic_id: str
    message: str
    conversation_history: list[ChatMessage] = []


@router.post("/synthesize")
async def synthesize_content(request: SynthesizeRequest):
    topic_res = (
        supabase.table("topics")
        .select("*")
        .eq("id", request.topic_id)
        .limit(1)
        .execute()
    )
    if not topic_res.data or len(topic_res.data) == 0:
        raise HTTPException(status_code=404, detail="Topic not found")
    topic = topic_res.data[0]
    try:
        markdown = await synthesize_study_guide(
            topic_title=topic["title"],
            topic_description=topic.get("description", ""),
            raw_context=request.raw_context
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Groq API error: {str(e)}")
    return {
        "topic_id": request.topic_id,
        "topic_title": topic["title"],
        "markdown": markdown,
        "model": "llama3-70b-8192"
    }


@router.post("/tutor")
async def tutor_endpoint(request: TutorRequest):
    topic_res = (
        supabase.table("topics")
        .select("*")
        .eq("id", request.topic_id)
        .limit(1)
        .execute()
    )
    if not topic_res.data or len(topic_res.data) == 0:
        raise HTTPException(status_code=404, detail="Topic not found")
    topic = topic_res.data[0]
    history = [
        {"role": m.role, "content": m.content}
        for m in request.conversation_history
    ]
    try:
        reply = await tutor_chat(
            user_message=request.message,
            active_topic_title=topic["title"],
            active_topic_description=topic.get("description", ""),
            conversation_history=history
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Groq API error: {str(e)}")
    supabase.table("chat_messages").insert([
        {"user_id": request.user_id, "topic_id": request.topic_id, "role": "user", "content": request.message},
        {"user_id": request.user_id, "topic_id": request.topic_id, "role": "assistant", "content": reply}
    ]).execute()
    return {
        "reply": reply,
        "topic_title": topic["title"],
        "model": "llama3-70b-8192"
    }


@router.get("/history/{user_id}/{topic_id}")
async def get_chat_history(user_id: str, topic_id: str):
    result = (
        supabase.table("chat_messages")
        .select("*")
        .eq("user_id", user_id)
        .eq("topic_id", topic_id)
        .order("created_at")
        .execute()
    )
    return {
        "user_id": user_id,
        "topic_id": topic_id,
        "messages": result.data or []
    }
