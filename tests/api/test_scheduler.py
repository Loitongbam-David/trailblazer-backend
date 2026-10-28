def test_scheduler_requires_profile(client):
    assert client.get("/api/scheduler/u1").status_code == 404


def test_scheduler_returns_budgeted_topics(client, fake_supabase):
    fake_supabase.tables["profiles"] = [{"id": "u1", "weekly_hours": 3}]
    fake_supabase.tables["topics"] = [
        {"id": "t1", "estimated_hours": 2, "priority": 10},
        {"id": "t2", "estimated_hours": 2, "priority": 9},
    ]
    fake_supabase.tables["user_progress"] = []
    response = client.get("/api/scheduler/u1")
    assert response.status_code == 200
    assert response.json()["total_hours"] <= 3
