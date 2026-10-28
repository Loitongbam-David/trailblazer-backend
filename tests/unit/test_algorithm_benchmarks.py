import pytest

from app.services.algorithms import RoadmapGenerator, knapsack_scheduler, quicksort_resources


@pytest.mark.parametrize("size", [100, 1000])
def test_roadmap_generation_benchmark(benchmark, size):
    topics = [
        {"id": str(index), "estimated_hours": 1, "difficulty": 1, "priority": 1}
        for index in range(size)
    ]
    prerequisites = [
        {"topic_id": str(index), "prerequisite_id": str(index - 1)}
        for index in range(1, size)
    ]
    benchmark(RoadmapGenerator(topics, prerequisites).generate)


def test_scheduler_benchmark(benchmark):
    topics = [{"estimated_hours": 1, "priority": index % 10 + 1} for index in range(100)]
    benchmark(knapsack_scheduler, topics, 40)


def test_resource_sort_benchmark(benchmark):
    resources = [{"relevance_score": index % 100} for index in range(1000)]
    benchmark(quicksort_resources, resources)
