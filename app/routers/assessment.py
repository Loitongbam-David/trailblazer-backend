from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database import supabase
from app.services.algorithms import HillClimbingAssessor

router = APIRouter()

# In-memory session store (replace with Redis/DB in production)
_sessions: dict = {}

class StartAssessmentPayload(BaseModel):
    user_id: str
    topic_id: str

class AnswerPayload(BaseModel):
    user_id: str
    topic_id: str
    question_id: str
    selected_option: int
    current_difficulty: int

@router.post("/start")
async def start_assessment(payload: StartAssessmentPayload):
    """Initialize a hill-climbing session for a user+topic."""
    session_key = f"{payload.user_id}:{payload.topic_id}"
    _sessions[session_key] = HillClimbingAssessor(current_difficulty=3)
    return {"session_key": session_key, "starting_difficulty": 3}

@router.get("/question/{topic_id}")
async def get_question(topic_id: str, difficulty: int = 3):
    """Fetch a question at the current difficulty level."""
    result = (
        supabase.table("questions")
        .select("*")
        .eq("topic_id", topic_id)
        .eq("difficulty", difficulty)
        .limit(1)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="No question found at this difficulty")
    return result.data[0]

@router.post("/answer")
async def submit_answer(payload: AnswerPayload):
    """Submit an answer; hill-climber returns next difficulty."""
    session_key = f"{payload.user_id}:{payload.topic_id}"

    if session_key not in _sessions:
        _sessions[session_key] = HillClimbingAssessor(payload.current_difficulty)

    assessor = _sessions[session_key]

    # Verify answer against DB
    result = (
        supabase.table("questions")
        .select("options")
        .eq("id", payload.question_id)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Question not found")

    options = result.data["options"]
    correct = options[payload.selected_option].get("is_correct", False)

    climb_result = assessor.submit_answer(correct)

    # If peak found, persist mastery score to DB
    if climb_result["peak_found"]:
        supabase.table("user_progress").upsert({
            "user_id": payload.user_id,
            "topic_id": payload.topic_id,
            "mastery_score": climb_result["mastery_score"],
            "status": "completed" if climb_result["mastery_score"] >= 60 else "in_progress"
        }).execute()
        del _sessions[session_key]

    return climb_result