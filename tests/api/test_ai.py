import pytest


@pytest.mark.asyncio
async def test_synthesize_topic(client, fake_supabase, monkeypatch):
    fake_supabase.tables["topics"] = [{"id": "t1", "title": "Python", "description": "Basics"}]
    async def fake_synthesize(**kwargs):
        return "# Python\n\n## Quick Recap\n- Syntax"
    monkeypatch.setattr("app.routers.ai.synthesize_study_guide", fake_synthesize)
    response = client.post("/api/ai/synthesize", json={"topic_id": "t1"})
    assert response.status_code == 200
    assert response.json()["markdown"].startswith("# Python")


def test_ai_returns_404_for_missing_topic(client):
    assert client.post("/api/ai/synthesize", json={"topic_id": "missing"}).status_code == 404


@pytest.mark.asyncio
async def test_tutor_persists_conversation(client, fake_supabase, monkeypatch):
    fake_supabase.tables["topics"] = [{"id": "t1", "title": "Python", "description": "Basics"}]
    async def fake_tutor(**kwargs):
        return "Use a variable to store a value."
    monkeypatch.setattr("app.routers.ai.tutor_chat", fake_tutor)
    response = client.post(
        "/api/ai/tutor",
        json={"user_id": "u1", "topic_id": "t1", "message": "What is a variable?"},
    )
    assert response.status_code == 200
    assert len(fake_supabase.tables["chat_messages"]) == 2
