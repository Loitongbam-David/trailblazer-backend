import pytest

from app.services.algorithms import (
    HillClimbingAssessor,
    RoadmapGenerator,
    knapsack_scheduler,
    quicksort_resources,
)


def test_hill_climbing_moves_and_confirms_peak():
    assessor = HillClimbingAssessor(3)
    assert assessor.submit_answer(True)["next_difficulty"] == 4
    result = assessor.submit_answer(False)
    assert result["peak_found"] is True
    assert result["peak_difficulty"] == 3
    assert 0 <= result["mastery_score"] <= 100


@pytest.mark.parametrize(
    ("starting", "answer", "expected_peak"),
    [(1, False, 0), (5, True, 5)],
)
def test_hill_climbing_boundary_peaks(starting, answer, expected_peak):
    result = HillClimbingAssessor(starting).submit_answer(answer)
    assert result["peak_found"] is True
    assert result["peak_difficulty"] == expected_peak


def test_hill_climbing_clamps_initial_difficulty():
    assert HillClimbingAssessor(-10).difficulty == 1
    assert HillClimbingAssessor(99).difficulty == 5


def test_roadmap_respects_prerequisites_and_mastery():
    topics = [
        {"id": "a", "title": "A", "estimated_hours": 1, "difficulty": 1, "priority": 1},
        {"id": "b", "title": "B", "estimated_hours": 2, "difficulty": 2, "priority": 2},
        {"id": "c", "title": "C", "estimated_hours": 3, "difficulty": 3, "priority": 3},
    ]
    prerequisites = [{"topic_id": "b", "prerequisite_id": "a"}, {"topic_id": "c", "prerequisite_id": "b"}]
    roadmap = RoadmapGenerator(topics, prerequisites).generate(["a"])
    assert [topic["id"] for topic in roadmap] == ["a", "b", "c"]
    assert [topic["status"] for topic in roadmap] == ["completed", "unlocked", "locked"]


def test_roadmap_rejects_cycles():
    topics = [{"id": "a"}, {"id": "b"}]
    with pytest.raises(ValueError, match="Cycle detected"):
        RoadmapGenerator(
            topics,
            [{"topic_id": "a", "prerequisite_id": "b"}, {"topic_id": "b", "prerequisite_id": "a"}],
        ).generate()


def test_scheduler_never_exceeds_budget():
    topics = [
        {"id": "a", "estimated_hours": 2, "priority": 10},
        {"id": "b", "estimated_hours": 3, "priority": 9},
        {"id": "c", "estimated_hours": 1, "priority": 2},
    ]
    result = knapsack_scheduler(topics, 3)
    assert result["total_hours"] <= 3
    assert result["total_priority"] == 12


def test_scheduler_handles_empty_and_zero_capacity():
    assert knapsack_scheduler([], 4)["selected_topics"] == []
    assert knapsack_scheduler([{"estimated_hours": 1, "priority": 5}], 0)["selected_topics"] == []


def test_quicksort_orders_descending():
    resources = [{"relevance_score": 2}, {"relevance_score": 10}, {"relevance_score": 5}]
    assert [item["relevance_score"] for item in quicksort_resources(resources)] == [10, 5, 2]
