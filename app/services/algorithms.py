from typing import List, Dict, Optional, Tuple
from collections import defaultdict, deque

# ─────────────────────────────────────────────
# 1. HILL CLIMBING — Adaptive Knowledge Assessment
# ─────────────────────────────────────────────

class HillClimbingAssessor:
    """
    Finds a user's knowledge peak for a topic by adjusting
    question difficulty based on correct/incorrect answers.

    Difficulty scale: 1 (easiest) → 5 (hardest)
    Climbs up on correct, descends on wrong.
    Stops when the peak is confirmed (correct at level N,
    wrong at level N+1) or boundaries are hit.
    """

    MIN_DIFFICULTY = 1
    MAX_DIFFICULTY = 5

    def __init__(self, current_difficulty: int = 3):
        self.difficulty = max(
            self.MIN_DIFFICULTY,
            min(self.MAX_DIFFICULTY, current_difficulty)
        )
        self.history: List[Dict] = []
        self.peak_found = False
        self.peak_difficulty = None

    def submit_answer(self, correct: bool) -> Dict:
        """
        Process an answer and return the next difficulty level.
        Returns a dict with next_difficulty, peak_found, mastery_score.
        """
        self.history.append({
            "difficulty": self.difficulty,
            "correct": correct
        })

        previous = self.difficulty

        if correct:
            if self.difficulty == self.MAX_DIFFICULTY:
                # Topped out — peak is at max
                self.peak_found = True
                self.peak_difficulty = self.MAX_DIFFICULTY
            else:
                # Check if we already failed the next level (peak confirmed)
                next_level = self.difficulty + 1
                failed_next = any(
                    h["difficulty"] == next_level and not h["correct"]
                    for h in self.history
                )
                if failed_next:
                    self.peak_found = True
                    self.peak_difficulty = self.difficulty
                else:
                    self.difficulty += 1
        else:
            if self.difficulty == self.MIN_DIFFICULTY:
                # Failed the easiest — peak is zero
                self.peak_found = True
                self.peak_difficulty = 0
            else:
                # Check if we already passed the level below (peak confirmed)
                prev_level = self.difficulty - 1
                passed_prev = any(
                    h["difficulty"] == prev_level and h["correct"]
                    for h in self.history
                )
                if passed_prev:
                    self.peak_found = True
                    self.peak_difficulty = prev_level
                else:
                    self.difficulty -= 1

        return {
            "previous_difficulty": previous,
            "next_difficulty": self.difficulty,
            "peak_found": self.peak_found,
            "peak_difficulty": self.peak_difficulty,
            "mastery_score": self._compute_mastery(),
            "total_questions": len(self.history)
        }

    def _compute_mastery(self) -> float:
        """
        Mastery score 0–100 based on peak difficulty
        and consistency of correct answers.
        """
        if not self.history:
            return 0.0
        correct_count = sum(1 for h in self.history if h["correct"])
        accuracy = correct_count / len(self.history)
        peak = self.peak_difficulty or self.difficulty
        # Weight: 70% from peak difficulty, 30% from accuracy
        difficulty_score = (peak / self.MAX_DIFFICULTY) * 70
        accuracy_score = accuracy * 30
        return round(difficulty_score + accuracy_score, 2)


# ─────────────────────────────────────────────
# 2. TOPOLOGICAL SORT / DFS — Roadmap Generation
# ─────────────────────────────────────────────

class RoadmapGenerator:
    """
    Models the curriculum as a Directed Acyclic Graph (DAG).
    Nodes = topics, edges = prerequisites.
    Uses DFS-based topological sort to produce a linear study path,
    then filters out topics the user has already mastered.
    """

    def __init__(self, topics: List[Dict], prerequisites: List[Dict]):
        """
        topics: list of {id, title, estimated_hours, difficulty, priority}
        prerequisites: list of {topic_id, prerequisite_id}
        """
        self.topics = {t["id"]: t for t in topics}
        self.graph: Dict[str, List[str]] = defaultdict(list)
        self.in_degree: Dict[str, int] = defaultdict(int)

        for t in topics:
            self.graph[t["id"]]  # ensure every node exists in graph
            self.in_degree[t["id"]]

        for edge in prerequisites:
            # prerequisite_id → topic_id (must learn prereq first)
            self.graph[edge["prerequisite_id"]].append(edge["topic_id"])
            self.in_degree[edge["topic_id"]] += 1

    def generate(self, mastered_topic_ids: List[str] = None) -> List[Dict]:
        """
        Returns an ordered list of topics the user should study,
        skipping already-mastered ones while respecting prerequisites.

        Uses Kahn's algorithm (BFS topological sort) for cycle safety.
        """
        mastered = set(mastered_topic_ids or [])

        # Kahn's: start with all nodes that have no prerequisites
        in_degree = dict(self.in_degree)
        queue = deque(
            node for node, deg in in_degree.items() if deg == 0
        )
        ordered: List[str] = []

        while queue:
            node = queue.popleft()
            ordered.append(node)
            for neighbor in self.graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(ordered) != len(self.topics):
            raise ValueError("Cycle detected in curriculum graph — check prerequisites")

        # Build result: include all topics in order, mark status
        result = []
        unlocked = set(
            node for node, deg in self.in_degree.items() if deg == 0
        )

        for topic_id in ordered:
            topic = self.topics[topic_id]
            if topic_id in mastered:
                status = "completed"
            elif topic_id in unlocked:
                status = "unlocked"
            else:
                # Check if all prerequisites are mastered → unlocked
                prereqs = [
                    n for n, neighbors in self.graph.items()
                    if topic_id in neighbors
                ]
                status = "unlocked" if all(p in mastered for p in prereqs) else "locked"

            result.append({**topic, "status": status})

            # Unlock neighbors if this topic is mastered
            if topic_id in mastered:
                for neighbor in self.graph[topic_id]:
                    unlocked.add(neighbor)

        return result

    def get_next_topics(
        self, mastered_topic_ids: List[str], limit: int = 3
    ) -> List[Dict]:
        """Returns the next N unlocked-but-not-mastered topics."""
        roadmap = self.generate(mastered_topic_ids)
        return [t for t in roadmap if t["status"] == "unlocked"][:limit]


# ─────────────────────────────────────────────
# 3. 0/1 KNAPSACK — Weekly Study Scheduler
# ─────────────────────────────────────────────

def knapsack_scheduler(
    topics: List[Dict],
    weekly_hours: float
) -> Dict:
    """
    Selects the optimal set of topics to study this week.

    Each topic has:
      - estimated_hours  (weight)
      - priority         (value, 1–10)

    Converts hours to integer units (×10) for the DP table.
    Returns the selected topics and total hours/priority.
    """
    # Convert to integer capacity (×10 to handle 0.5h increments)
    capacity = int(weekly_hours * 10)
    n = len(topics)

    if n == 0 or capacity == 0:
        return {"selected_topics": [], "total_hours": 0, "total_priority": 0}

    weights = [int(t["estimated_hours"] * 10) for t in topics]
    values  = [t["priority"] for t in topics]

    # DP table: dp[i][w] = max priority using first i items, capacity w
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        w = weights[i - 1]
        v = values[i - 1]
        for c in range(capacity + 1):
            if w > c:
                dp[i][c] = dp[i - 1][c]
            else:
                dp[i][c] = max(dp[i - 1][c], dp[i - 1][c - w] + v)

    # Backtrack to find which topics were selected
    selected = []
    c = capacity
    for i in range(n, 0, -1):
        if dp[i][c] != dp[i - 1][c]:
            selected.append(topics[i - 1])
            c -= weights[i - 1]

    selected.reverse()
    total_hours = sum(t["estimated_hours"] for t in selected)
    total_priority = sum(t["priority"] for t in selected)

    return {
        "selected_topics": selected,
        "total_hours": round(total_hours, 1),
        "total_priority": total_priority,
        "weekly_budget_hours": weekly_hours,
        "utilization_pct": round((total_hours / weekly_hours) * 100, 1)
    }


# ─────────────────────────────────────────────
# 4. QUICKSORT — Resource Relevance Ranking
# ─────────────────────────────────────────────

def quicksort_resources(
    resources: List[Dict],
    key: str = "relevance_score"
) -> List[Dict]:
    """
    Sorts resources by relevance_score descending using Quicksort.
    Returns the sorted list (highest score first).
    """
    if len(resources) <= 1:
        return resources

    pivot = resources[len(resources) // 2][key]
    left   = [r for r in resources if r[key] >  pivot]
    middle = [r for r in resources if r[key] == pivot]
    right  = [r for r in resources if r[key] <  pivot]

    return quicksort_resources(left, key) + middle + quicksort_resources(right, key)