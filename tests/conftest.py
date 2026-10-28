import os
from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")
os.environ.setdefault("GROQ_API_KEY", "test-groq-key")


class FakeResult:
    def __init__(self, data):
        self.data = deepcopy(data)


class FakeQuery:
    def __init__(self, supabase, table):
        self.supabase = supabase
        self.table_name = table
        self.filters = []
        self.selected = None
        self.limit_value = None
        self.single_value = False
        self.operation = "select"
        self.payload = None
        self.order_field = None

    def select(self, fields="*"):
        self.selected = fields
        self.operation = "select"
        return self

    def eq(self, field, value):
        self.filters.append(("eq", field, value))
        return self

    def is_(self, field, operator, value):
        self.filters.append(("is", field, operator, value))
        return self

    def limit(self, value):
        self.limit_value = value
        return self

    def single(self):
        self.limit_value = 1
        self.single_value = True
        return self

    def order(self, field):
        self.order_field = field
        return self

    def insert(self, payload):
        self.operation = "insert"
        self.payload = payload
        return self

    def update(self, payload):
        self.operation = "update"
        self.payload = payload
        return self

    def upsert(self, payload):
        self.operation = "upsert"
        self.payload = payload
        return self

    def delete(self):
        self.operation = "delete"
        return self

    def _matches(self, row):
        for filter_type, field, *values in self.filters:
            if filter_type == "eq" and row.get(field) != values[0]:
                return False
            if filter_type == "is" and values[0] == "null" and row.get(field) is not None:
                return False
        return True

    def execute(self):
        rows = self.supabase.tables.setdefault(self.table_name, [])
        matching = [row for row in rows if self._matches(row)]

        if self.operation == "select":
            if self.order_field:
                matching.sort(key=lambda row: row.get(self.order_field, ""))
            if self.limit_value is not None:
                matching = matching[: self.limit_value]
            if self.selected and self.selected != "*":
                fields = [field.strip() for field in self.selected.split(",")]
                matching = [{field: row.get(field) for field in fields} for row in matching]
            if self.single_value:
                return FakeResult(matching[0] if matching else None)
            return FakeResult(matching)

        if self.operation in ("insert", "upsert"):
            payloads = self.payload if isinstance(self.payload, list) else [self.payload]
            inserted = []
            for payload in payloads:
                row = deepcopy(payload)
                if "id" not in row:
                    row["id"] = f"{self.table_name}-{len(rows) + 1}"
                if self.operation == "upsert":
                    existing = next(
                        (
                            current
                            for current in rows
                            if row.get("user_id") == current.get("user_id")
                            and row.get("topic_id") == current.get("topic_id")
                        ),
                        None,
                    )
                    if existing:
                        existing.update(row)
                        inserted.append(existing)
                        continue
                rows.append(row)
                inserted.append(row)
            return FakeResult(inserted)

        if self.operation == "update":
            for row in matching:
                row.update(deepcopy(self.payload))
            return FakeResult(matching)

        if self.operation == "delete":
            self.supabase.tables[self.table_name] = [
                row for row in rows if not self._matches(row)
            ]
            return FakeResult([])

        raise AssertionError(f"Unsupported fake operation: {self.operation}")


class FakeSupabase:
    def __init__(self, tables=None):
        self.tables = deepcopy(tables or {})

    def table(self, name):
        return FakeQuery(self, name)


@pytest.fixture
def fake_supabase():
    return FakeSupabase()


@pytest.fixture
def client(monkeypatch, fake_supabase):
    import app.database
    import app.routers.ai as ai_router
    import app.routers.assessment as assessment_router
    import app.routers.progress as progress_router
    import app.routers.roadmap as roadmap_router
    import app.routers.scheduler as scheduler_router

    for module in (
        app.database,
        ai_router,
        assessment_router,
        progress_router,
        roadmap_router,
        scheduler_router,
    ):
        monkeypatch.setattr(module, "supabase", fake_supabase, raising=False)

    assessment_router._sessions.clear()
    return TestClient(__import__("app.main", fromlist=["app"]).app)
