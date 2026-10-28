def test_progress_insert_and_get(client):
    response = client.post(
        "/api/progress/update",
        json={"user_id": "u1", "topic_id": "t1", "status": "in_progress", "mastery_score": 120},
    )
    assert response.status_code == 200
    progress = client.get("/api/progress/u1")
    assert progress.status_code == 200
    assert progress.json()["progress"][0]["mastery_score"] == 99.99


def test_completed_prerequisite_unlocks_dependent_topic(client, fake_supabase):
    fake_supabase.tables["topic_prerequisites"] = [
        {"topic_id": "dependent", "prerequisite_id": "prerequisite"}
    ]
    fake_supabase.tables["user_progress"] = [
        {"id": "p1", "user_id": "u1", "topic_id": "dependent", "status": "locked", "mastery_score": 0}
    ]
    response = client.post(
        "/api/progress/update",
        json={"user_id": "u1", "topic_id": "prerequisite", "status": "completed"},
    )
    assert response.status_code == 200
    assert fake_supabase.tables["user_progress"][0]["status"] == "unlocked"
