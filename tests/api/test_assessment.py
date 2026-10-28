def test_start_and_answer_assessment(client, fake_supabase):
    fake_supabase.tables["questions"] = [
        {"id": "q1", "topic_id": "python", "difficulty": 3, "options": [{"is_correct": True}]}
    ]
    assert client.post("/api/assessment/start", json={"user_id": "u1", "topic_id": "python"}).status_code == 200
    question = client.get("/api/assessment/question/python?difficulty=3")
    assert question.status_code == 200
    response = client.post(
        "/api/assessment/answer",
        json={
            "user_id": "u1",
            "topic_id": "python",
            "question_id": "q1",
            "selected_option": 0,
            "current_difficulty": 3,
        },
    )
    assert response.status_code == 200
    assert response.json()["next_difficulty"] == 4


def test_assessment_returns_404_for_missing_question(client):
    assert client.get("/api/assessment/question/missing").status_code == 404


def test_assessment_rejects_unknown_question(client):
    response = client.post(
        "/api/assessment/answer",
        json={
            "user_id": "u1",
            "topic_id": "python",
            "question_id": "missing",
            "selected_option": 0,
            "current_difficulty": 3,
        },
    )
    assert response.status_code == 404
