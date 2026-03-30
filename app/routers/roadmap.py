from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database import supabase
from app.services.algorithms import RoadmapGenerator
from app.services.groq_service import client, MODEL
import json

router = APIRouter()

CAREER_TOPIC_MAP = {
    "frontend":      ["HTML Fundamentals","CSS Basics","CSS Flexbox & Grid","CSS Frameworks","JavaScript Fundamentals","JavaScript Advanced","React Basics","React Hooks","React Router","State Management","TypeScript","Testing Frontend","Web Performance","Frontend Build Tools"],
    "backend":       ["JavaScript Fundamentals","JavaScript Advanced","Node.js Basics","Express.js","Databases SQL","Databases NoSQL","Authentication & Auth","REST API Design","GraphQL","ORMs & Query Builders","Caching","Message Queues","Backend Testing","API Security"],
    "fullstack":     ["HTML Fundamentals","CSS Basics","CSS Flexbox & Grid","JavaScript Fundamentals","JavaScript Advanced","React Basics","React Hooks","Node.js Basics","Express.js","Databases SQL","Authentication & Auth","REST API Design","Full Stack: Next.js","Full Stack: Databases","Full Stack: Auth Patterns","Full Stack: Deployment"],
    "data":          ["Python for Data","NumPy & Pandas","Data Visualization","Statistics & Probability","SQL for Data Analysis","Machine Learning Basics","Regression & Classification","Unsupervised Learning","Feature Engineering","Model Deployment","Deep Learning Intro","Time Series Analysis"],
    "ai":            ["Python for Data","Python Advanced","NumPy & Pandas","Statistics & Probability","Machine Learning Basics","Deep Learning Fundamentals","PyTorch","NLP & Transformers","LLM Engineering","MLOps","Vector Databases","Computer Vision","Reinforcement Learning","AI System Design"],
    "mobile":        ["JavaScript Fundamentals","JavaScript Advanced","React Basics","React Hooks","React Native Basics","React Native Advanced","Mobile Navigation","Mobile State Management","Mobile APIs & Storage","Push Notifications","App Store Deployment","Mobile Testing"],
    "devops":        ["Linux & Command Line","Git & Version Control","Networking Basics","Docker","Kubernetes","CI/CD Pipelines","Cloud AWS","Infrastructure as Code","Monitoring & Logging","Security DevSecOps"],
    "cybersecurity": ["Networking Fundamentals","Linux Security","Ethical Hacking Basics","Web Application Security","Cryptography","SIEM & Threat Detection","Incident Response","Cloud Security","Capture The Flag"],
    "blockchain":    ["JavaScript Fundamentals","JavaScript Advanced","Blockchain Fundamentals","Solidity Basics","Smart Contract Security","Web3.js & Ethers.js","DeFi Protocols","NFT Development","Layer 2 Solutions"],
    "cloud":         ["Linux & Command Line","Networking Basics","Cloud Fundamentals","AWS Core Services","Cloud Networking","Serverless Architecture","AWS Advanced","Infrastructure as Code","Cloud Cost Optimization","Multi-Cloud Strategy","Cloud Certifications"],
}

EXPERIENCE_SKIP = {
    "beginner":     [],
    "intermediate": ["HTML Fundamentals","CSS Basics","JavaScript Fundamentals","Python for Data","Linux & Command Line","Git & Version Control","Networking Fundamentals","Cloud Fundamentals","Blockchain Fundamentals"],
    "advanced":     ["HTML Fundamentals","CSS Basics","CSS Flexbox & Grid","JavaScript Fundamentals","Python for Data","Linux & Command Line","Git & Version Control","Networking Fundamentals","Node.js Basics","Cloud Fundamentals","React Basics","NumPy & Pandas","Blockchain Fundamentals","React Native Basics"],
}

class GenerateRoadmapRequest(BaseModel):
    user_id: str
    career_goal: str
    experience_level: str
    weekly_hours: float

class AssessmentAnswer(BaseModel):
    user_id: str
    career_goal: str
    topic_scores: dict  # {topic_title: score 0-100}

@router.get("/{user_id}")
async def get_roadmap(user_id: str):
    topics_res = supabase.table("topics").select("*").eq("user_id", user_id).execute()
    if not topics_res.data:
        raise HTTPException(status_code=404, detail="No roadmap found. Please complete onboarding.")

    prereqs_res = supabase.table("topic_prerequisites").select("*").execute()
    progress_res = (
        supabase.table("user_progress")
        .select("topic_id, status, mastery_score")
        .eq("user_id", user_id)
        .execute()
    )

    mastered = [
        p["topic_id"] for p in (progress_res.data or [])
        if p["status"] == "completed"
    ]

    topic_ids = [t["id"] for t in topics_res.data]
    user_prereqs = [
        p for p in (prereqs_res.data or [])
        if p["topic_id"] in topic_ids and p["prerequisite_id"] in topic_ids
    ]

    generator = RoadmapGenerator(topics_res.data, user_prereqs)
    roadmap = generator.generate(mastered)

    for topic in roadmap:
        progress = next((p for p in (progress_res.data or []) if p["topic_id"] == topic["id"]), None)
        if progress:
            topic["mastery_score"] = progress.get("mastery_score", 0)

    return {
        "user_id": user_id,
        "roadmap": roadmap,
        "total_topics": len(roadmap),
        "completed": len(mastered),
        "progress_pct": round(len(mastered) / len(roadmap) * 100, 1) if roadmap else 0
    }

@router.post("/generate")
async def generate_personalized_roadmap(request: GenerateRoadmapRequest):
    career = request.career_goal.lower().replace(" ", "_").replace("/", "_")
    career_key = next((k for k in CAREER_TOPIC_MAP if k in career), "fullstack")
    relevant_titles = CAREER_TOPIC_MAP[career_key]
    skip_titles = EXPERIENCE_SKIP.get(request.experience_level, [])
    filtered_titles = [t for t in relevant_titles if t not in skip_titles]

    all_topics = supabase.table("topics").select("*").is_("user_id", "null").execute()
    if not all_topics.data:
        raise HTTPException(status_code=404, detail="No base topics found in database")

    topic_map = {t["title"]: t for t in all_topics.data}
    selected_topics = [topic_map[title] for title in filtered_titles if title in topic_map]

    if not selected_topics:
        raise HTTPException(status_code=404, detail="No matching topics found")

    # Use Groq to reorder and adjust priorities based on career + experience
    topics_for_ai = [{"title": t["title"], "difficulty": t["difficulty"], "priority": t["priority"]} for t in selected_topics]
    prompt = f"""You are a curriculum expert. Given this list of topics for a {request.career_goal} at {request.experience_level} level with {request.weekly_hours} hours/week available:

{json.dumps(topics_for_ai, indent=2)}

Return a JSON array of the same topics with adjusted priority values (1-10) optimized for this specific learner.
Rules:
- Keep all topics, just reorder priority values
- Higher priority = study sooner
- Consider the learner's experience level and time budget
- Return ONLY a JSON array with objects containing: title (string), priority (integer 1-10)
- No markdown, no explanation, just the JSON array"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1000,
        )
        raw = response.choices[0].message.content.strip().replace("```json","").replace("```","").strip()
        ai_priorities = {item["title"]: item["priority"] for item in json.loads(raw)}
    except Exception:
        ai_priorities = {}

    # Delete user's old personalized topics
    old = supabase.table("topics").select("id").eq("user_id", request.user_id).execute()
    if old.data:
        old_ids = [t["id"] for t in old.data]
        for oid in old_ids:
            supabase.table("topic_prerequisites").delete().eq("topic_id", oid).execute()
            supabase.table("topic_prerequisites").delete().eq("prerequisite_id", oid).execute()
            supabase.table("user_progress").delete().eq("topic_id", oid).execute()
            supabase.table("topics").delete().eq("id", oid).execute()

    # Insert personalized copies of selected topics
    inserted = []
    for topic in selected_topics:
        new_priority = ai_priorities.get(topic["title"], topic["priority"])
        res = supabase.table("topics").insert({
            "title": topic["title"],
            "description": topic["description"],
            "estimated_hours": topic["estimated_hours"],
            "difficulty": topic["difficulty"],
            "priority": new_priority,
            "user_id": request.user_id,
        }).execute()
        if res.data:
            inserted.append({"new": res.data[0], "original_id": topic["id"]})

    # Copy prerequisites between inserted topics
    all_prereqs = supabase.table("topic_prerequisites").select("*").execute().data or []
    original_id_map = {item["original_id"]: item["new"]["id"] for item in inserted}

    for prereq in all_prereqs:
        new_topic_id  = original_id_map.get(prereq["topic_id"])
        new_prereq_id = original_id_map.get(prereq["prerequisite_id"])
        if new_topic_id and new_prereq_id:
            supabase.table("topic_prerequisites").insert({
                "topic_id": new_topic_id,
                "prerequisite_id": new_prereq_id,
            }).execute()

    # Initialize progress — first topics with no prereqs start as unlocked
    for item in inserted:
        topic_id = item["new"]["id"]
        has_prereqs = any(
            p["topic_id"] == topic_id
            for p in all_prereqs
            if p["topic_id"] in original_id_map.values()
        )
        supabase.table("user_progress").insert({
            "user_id": request.user_id,
            "topic_id": topic_id,
            "status": "locked" if has_prereqs else "unlocked",
            "mastery_score": 0,
        }).execute()

    # Save career goal and weekly hours to profile
    supabase.table("profiles").upsert({
        "id": request.user_id,
        "career_goal": request.career_goal,
        "weekly_hours": request.weekly_hours,
        "onboarded": True,
    }).execute()

    return {
        "message": "Personalized roadmap generated",
        "topics_created": len(inserted),
        "career_goal": request.career_goal,
        "experience_level": request.experience_level,
    }

@router.post("/assess")
async def update_from_assessment(payload: AssessmentAnswer):
    """Update progress based on skill assessment questionnaire results."""
    progress_res = (
        supabase.table("user_progress")
        .select("topic_id, status")
        .eq("user_id", payload.user_id)
        .execute()
    )
    topics_res = supabase.table("topics").select("id, title").eq("user_id", payload.user_id).execute()
    title_to_id = {t["title"]: t["id"] for t in (topics_res.data or [])}

    for title, score in payload.topic_scores.items():
        topic_id = title_to_id.get(title)
        if not topic_id:
            continue
        if score >= 80:
            status = "completed"
        elif score >= 40:
            status = "in_progress"
        else:
            status = "unlocked"
        supabase.table("user_progress").upsert({
            "user_id": payload.user_id,
            "topic_id": topic_id,
            "status": status,
            "mastery_score": score,
        }).execute()

    return {"message": "Assessment applied", "topics_updated": len(payload.topic_scores)}
