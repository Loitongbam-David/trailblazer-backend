def test_get_roadmap_returns_404_without_topics(client):
    assert client.get("/api/roadmap/u1").status_code == 404


def test_get_roadmap_returns_progress(client, fake_supabase):
    fake_supabase.tables["topics"] = [
        {"id": "t1", "user_id": "u1", "title": "Basics", "estimated_hours": 1, "difficulty": 1, "priority": 1}
    ]
    fake_supabase.tables["user_progress"] = [
        {"user_id": "u1", "topic_id": "t1", "status": "completed", "mastery_score": 90}
    ]
    response = client.get("/api/roadmap/u1")
    assert response.status_code == 200
    assert response.json()["completed"] == 1
    assert response.json()["progress_pct"] == 100


def test_assessment_updates_topic_statuses(client, fake_supabase):
    fake_supabase.tables["topics"] = [
        {"id": "t1", "user_id": "u1", "title": "Python", "estimated_hours": 1, "difficulty": 1, "priority": 1}
    ]
    response = client.post(
        "/api/roadmap/assess",
        json={"user_id": "u1", "career_goal": "backend", "topic_scores": {"Python": 85}},
    )
    assert response.status_code == 200
    assert fake_supabase.tables["user_progress"][0]["status"] == "completed"
