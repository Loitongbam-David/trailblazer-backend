# Trailblazer Backend Software Test Plan

## Document Control

| Field | Value |
|---|---|
| Document ID | TB-BE-STP-001 |
| Version | 1.0 |
| Status | Draft for review |
| System | Trailblazer Backend API |
| Repository | `Loitongbam-David/trailblazer-backend` |
| Branch | `loitongbam-david-add-comprehensive-tests` |
| Date | 2026-10-28 |
| Test framework | Pytest, pytest-asyncio, pytest-benchmark |
| Load framework | Locust |
| CI platform | GitHub Actions |

This document follows the structure and intent of IEEE 829-style test documentation. IEEE 829 has been superseded by ISO/IEC/IEEE 29119; this document uses the familiar IEEE test-plan and test-case organization for practical project use.

## 1. Purpose

The purpose of this document is to define the functional, integration, performance, load, and continuous-integration test coverage for the Trailblazer backend. It identifies the test items, test objectives, test cases, execution environments, acceptance criteria, risks, and traceability required to evaluate the API before release.

## 2. Scope

### 2.1 In scope

- FastAPI application startup and health checks.
- Assessment session creation, question retrieval, answer submission, and adaptive difficulty.
- User progress creation, update, retrieval, and prerequisite unlocking.
- Personalized roadmap retrieval, generation, and assessment-based updates.
- Weekly schedule generation.
- AI study-guide synthesis and tutor conversation persistence.
- Algorithmic services:
  - Hill-climbing assessment.
  - Prerequisite-aware roadmap generation.
  - Knapsack scheduling.
  - Resource relevance sorting.
- API behavior with mocked Supabase and Groq dependencies.
- Algorithm benchmarks.
- Locust load-test scenarios.
- GitHub Actions installation and test execution.

### 2.2 Out of scope

- Production Supabase availability and query-plan optimization.
- Actual Groq model quality evaluation.
- Browser or mobile client testing.
- Security penetration testing.
- Disaster recovery and backup restoration.
- Deployment validation against a live hosting provider.
- Real external API load testing.

## 3. System Under Test

The system under test is a Python 3.11 FastAPI service exposing the following route groups:

| Route group | Responsibility |
|---|---|
| `/health` | Service health status |
| `/api/assessment` | Adaptive knowledge assessment |
| `/api/progress` | User learning progress |
| `/api/roadmap` | Roadmap generation and progress-aware learning paths |
| `/api/scheduler` | Weekly topic scheduling |
| `/api/ai` | Study-guide synthesis and tutor conversations |

The backend uses:

- Supabase for persistence.
- Groq for AI generation.
- An in-memory dictionary for assessment sessions.
- Algorithmic services in `app/services/algorithms.py`.

## 4. References and Test Assets

| Reference | Location |
|---|---|
| Application entry point | `app/main.py` |
| Database client | `app/database.py` |
| Assessment routes | `app/routers/assessment.py` |
| Progress routes | `app/routers/progress.py` |
| Roadmap routes | `app/routers/roadmap.py` |
| Scheduler routes | `app/routers/scheduler.py` |
| AI routes | `app/routers/ai.py` |
| Algorithms | `app/services/algorithms.py` |
| AI service | `app/services/groq_service.py` |
| Automated tests | `tests/` |
| Pytest configuration | `pytest.ini` |
| Development dependencies | `requirements-dev.txt` |
| Load-test scenario | `tests/load/locustfile.py` |
| CI workflow | `.github/workflows/ci.yml` |

## 5. Test Strategy

### 5.1 Test levels

1. **Unit testing** validates algorithms in isolation.
2. **API testing** validates HTTP status codes, response contracts, persistence behavior, and error handling with fake dependencies.
3. **Benchmark testing** measures algorithm execution time at representative data sizes.
4. **Load testing** exercises the service through HTTP using Locust.
5. **CI testing** verifies that the complete automated suite runs on pushes and pull requests.

### 5.2 Test doubles

Automated API tests use:

- `FakeSupabase` in `tests/conftest.py`.
- Monkeypatched router-level Supabase clients.
- Monkeypatched Groq service functions.

No production Supabase, service key, or Groq API key is required for the automated suite.

### 5.3 Test classifications

| Classification | Meaning |
|---|---|
| Automated | Implemented in the repository and executed by Pytest |
| Benchmark | Implemented using pytest-benchmark |
| Load | Implemented as a Locust scenario; requires a running server |
| Planned | Defined here for future implementation or environment validation |

## 6. Test Environment

### 6.1 Automated test environment

| Component | Requirement |
|---|---|
| Operating system | Windows for local execution; Ubuntu latest in CI |
| Python | 3.11, defined by `runtime.txt` |
| Test command | `python -m pytest` |
| Dependencies | `pip install -r requirements-dev.txt` |
| External services | Mocked |
| Test data | In-memory fixtures |

### 6.2 Load-test environment

The load tests require:

1. A running backend.
2. A test Supabase project or a seeded test environment.
3. Non-production test credentials.
4. Locust installed from `requirements-dev.txt`.

Example:

```bash
locust -f tests/load/locustfile.py --host http://localhost:8000
```

### 6.3 CI environment

GitHub Actions runs on `ubuntu-latest` and:

1. Checks out the repository.
2. Sets up the Python version from `runtime.txt`.
3. Caches pip dependencies.
4. Installs `requirements-dev.txt`.
5. Runs Pytest and writes `test-results.xml`.
6. Uploads the JUnit result as a workflow artifact.

## 7. Entry and Exit Criteria

### 7.1 Entry criteria

- Source code is available in the target branch.
- Python 3.11 is available.
- Development dependencies can be installed.
- Test environment variables are present or mocked.
- Test fixtures are deterministic.

### 7.2 Exit criteria

The test cycle is complete when:

- All automated functional tests pass.
- No benchmark test fails due to an implementation error.
- The CI workflow completes successfully.
- Known failures are documented and approved.
- Load-test results are recorded for the agreed workload.
- No release-blocking defect remains open.

## 8. Functional Test Cases

The following cases are the authoritative functional test catalog. Test cases marked **Automated** are currently implemented in `tests/`.

### 8.1 Health and routing

| ID | Test case | Preconditions | Steps | Expected result | Status |
|---|---|---|---|---|---|
| FT-HEALTH-001 | Health endpoint returns service status | API application can start | Send `GET /health` | HTTP `200`; body is `{"status":"ok","service":"trailblazer-api"}` | Automated |
| FT-HEALTH-002 | Unknown route returns not found | API is running | Send `GET /unknown-route` | HTTP `404` | Planned |
| FT-HEALTH-003 | All route groups are registered | API is running | Inspect OpenAPI routes or call representative endpoints | Assessment, progress, roadmap, scheduler, and AI routes are registered | Planned |

### 8.2 Assessment API

| ID | Test case | Preconditions | Steps | Expected result | Status |
|---|---|---|---|---|---|
| FT-ASSESS-001 | Start a new assessment | User and topic identifiers are available | `POST /api/assessment/start` with `user_id` and `topic_id` | HTTP `200`; session key is `<user_id>:<topic_id>`; starting difficulty is `3` | Automated |
| FT-ASSESS-002 | Restart an existing assessment | An assessment exists for the same user/topic | Start the same assessment again | Existing session is replaced with a fresh assessor at difficulty `3` | Planned |
| FT-ASSESS-003 | Retrieve a question at a difficulty | Matching question exists | `GET /api/assessment/question/{topic_id}?difficulty=3` | HTTP `200`; matching question is returned | Automated |
| FT-ASSESS-004 | Retrieve a missing question | No matching question exists | Request an unavailable topic or difficulty | HTTP `404`; detail states no question was found | Automated |
| FT-ASSESS-005 | Submit a correct answer | Question and options exist | Submit a valid option marked correct | HTTP `200`; next difficulty increases unless at maximum | Automated |
| FT-ASSESS-006 | Submit an incorrect answer | Question and options exist | Submit a valid incorrect option | HTTP `200`; next difficulty decreases unless at minimum | Planned |
| FT-ASSESS-007 | Submit answer for unknown question | No matching question exists | Submit an unknown `question_id` | HTTP `404`; detail states question was not found | Automated |
| FT-ASSESS-008 | Submit answer without a prior session | Question exists | Submit an answer for a new user/topic | A session is initialized from `current_difficulty`; response is valid | Planned |
| FT-ASSESS-009 | Confirm maximum-difficulty peak | Session is at difficulty `5` | Submit a correct answer | `peak_found` is true and `peak_difficulty` is `5` | Unit automated |
| FT-ASSESS-010 | Confirm minimum-difficulty failure | Session is at difficulty `1` | Submit an incorrect answer | `peak_found` is true and `peak_difficulty` is `0` | Unit automated |
| FT-ASSESS-011 | Reject invalid option index | Question has fewer options than selected index | Submit an out-of-range `selected_option` | Request is rejected with a controlled client error; no unhandled exception | Planned |
| FT-ASSESS-012 | Persist peak progress | Assessment reaches a confirmed peak | Submit the answer that confirms the peak | `user_progress` is upserted; completed status is used for mastery score at least `60`; session is removed | Planned |
| FT-ASSESS-013 | Preserve independent user sessions | Two users assess the same topic | Interleave answers from both users | Each user receives independent difficulty and history | Planned |

### 8.3 Progress API

| ID | Test case | Preconditions | Steps | Expected result | Status |
|---|---|---|---|---|---|
| FT-PROG-001 | Insert progress for a new topic | No existing progress row | `POST /api/progress/update` | HTTP `200`; one progress row is inserted | Automated |
| FT-PROG-002 | Update existing progress | Existing user/topic progress row | Post a new status and score | Existing row is updated rather than duplicated | Planned |
| FT-PROG-003 | Clamp score above database maximum | No existing progress row | Submit `mastery_score=120` | Stored score is `99.99` | Automated |
| FT-PROG-004 | Accept default mastery score | Request omits mastery score | Post a valid status | Default score is applied and stored within the supported range | Planned |
| FT-PROG-005 | Complete a prerequisite | Dependent topic is locked and prerequisite relation exists | Mark prerequisite completed | Dependent topic becomes `unlocked` when all prerequisites are complete | Automated |
| FT-PROG-006 | Keep dependent topic locked | Dependent topic has multiple prerequisites | Complete only one prerequisite | Dependent topic remains locked | Planned |
| FT-PROG-007 | Retrieve user progress | Progress rows exist | `GET /api/progress/{user_id}` | HTTP `200`; response contains user ID and all matching progress rows | Automated |
| FT-PROG-008 | Retrieve empty progress | User has no rows | Request progress | HTTP `200`; `progress` is an empty list | Planned |
| FT-PROG-009 | Handle completed topic without dependents | Topic has no dependent topics | Mark it completed | Update succeeds without unnecessary dependent updates | Planned |
| FT-PROG-010 | Validate negative score behavior | API accepts the request schema | Submit a negative mastery score | Behavior is explicitly defined and tested; negative persisted scores should be rejected or normalized | Planned |

### 8.4 Roadmap API

| ID | Test case | Preconditions | Steps | Expected result | Status |
|---|---|---|---|---|---|
| FT-ROADMAP-001 | Return missing-roadmap error | User has no personalized topics | `GET /api/roadmap/{user_id}` | HTTP `404`; onboarding message is returned | Automated |
| FT-ROADMAP-002 | Return roadmap with progress | User topics and progress exist | Request roadmap | HTTP `200`; roadmap includes statuses, mastery, totals, and progress percentage | Automated |
| FT-ROADMAP-003 | Mark completed topics | A topic has completed progress | Request roadmap | Topic status is `completed`; completed count is incremented | Automated |
| FT-ROADMAP-004 | Calculate zero progress safely | Roadmap exists with no completed topics | Request roadmap | Progress percentage is `0` | Planned |
| FT-ROADMAP-005 | Generate beginner roadmap | Base topics exist | Post career goal, beginner experience, and weekly hours | Personalized topics are created; profile is marked onboarded | Planned |
| FT-ROADMAP-006 | Generate intermediate roadmap | Base topics exist | Generate with intermediate experience | Experience-specific introductory topics are skipped | Planned |
| FT-ROADMAP-007 | Generate advanced roadmap | Base topics exist | Generate with advanced experience | Advanced skip list is applied | Planned |
| FT-ROADMAP-008 | Handle unknown career goal | Base topics exist | Generate an unsupported career | Full-stack fallback is used according to the current implementation | Planned |
| FT-ROADMAP-009 | Handle missing base topics | No base topics exist | Generate a roadmap | HTTP `404`; base-topic error is returned | Planned |
| FT-ROADMAP-010 | Handle no matching topic titles | Base topics do not match selected career list | Generate a roadmap | HTTP `404`; matching-topic error is returned | Planned |
| FT-ROADMAP-011 | Handle valid AI priority response | Groq returns valid JSON | Generate a roadmap | Returned priorities are applied to inserted topics | Planned |
| FT-ROADMAP-012 | Handle malformed AI priority response | Groq returns malformed JSON | Generate a roadmap | Generation continues using original priorities | Planned |
| FT-ROADMAP-013 | Copy prerequisites correctly | Selected topics have prerequisite relations | Generate a roadmap | Relations between inserted topic copies are preserved | Planned |
| FT-ROADMAP-014 | Initialize progress states | Generated topics include root and dependent topics | Generate a roadmap | Root topics are unlocked; dependent topics are locked | Planned |
| FT-ROADMAP-015 | Apply assessment scores | Personalized topics exist | Post topic scores | Scores under `40` become unlocked, `40–79` become in progress, and `80+` become completed | Automated |
| FT-ROADMAP-016 | Ignore unknown assessment titles | Assessment contains a title not in the user's roadmap | Post assessment | Unknown title is skipped; known topics are updated | Planned |

### 8.5 Scheduler API

| ID | Test case | Preconditions | Steps | Expected result | Status |
|---|---|---|---|---|---|
| FT-SCHED-001 | Reject missing profile | No profile exists | `GET /api/scheduler/{user_id}` | HTTP `404`; profile-not-found error is returned | Automated |
| FT-SCHED-002 | Generate weekly schedule | Profile and topics exist | Request schedule | HTTP `200`; selected topics and totals are returned | Automated |
| FT-SCHED-003 | Respect weekly-hour budget | Topics exceed available hours | Request schedule | Selected total hours do not exceed weekly hours | Automated |
| FT-SCHED-004 | Exclude completed topics | Completed progress rows exist | Request schedule | Completed topics are not returned as available topics | Planned |
| FT-SCHED-005 | Handle zero weekly hours | Profile has zero hours | Request schedule | Empty selection and zero totals are returned | Planned |
| FT-SCHED-006 | Handle empty topic list | User has no available topics | Request schedule | Empty selection is returned without an error | Planned |

### 8.6 AI API

| ID | Test case | Preconditions | Steps | Expected result | Status |
|---|---|---|---|---|---|
| FT-AI-001 | Synthesize study guide | Topic exists; Groq is mocked | `POST /api/ai/synthesize` | HTTP `200`; response includes topic ID, title, markdown, and model | Automated |
| FT-AI-002 | Synthesize missing topic | Topic does not exist | Post synthesis request | HTTP `404`; topic-not-found error is returned | Automated |
| FT-AI-003 | Convert Groq failure to API error | Topic exists; Groq raises an exception | Post synthesis request | HTTP `500`; Groq error is surfaced through the API error response | Planned |
| FT-AI-004 | Tutor with new conversation | Topic exists; tutor is mocked | `POST /api/ai/tutor` with a message | HTTP `200`; assistant reply and topic title are returned | Planned |
| FT-AI-005 | Tutor persists both messages | Tutor returns a reply | Send tutor message | User and assistant messages are inserted | Automated |
| FT-AI-006 | Tutor limits context history | More than ten history messages are supplied | Send tutor message | Only the latest ten history messages are sent to the AI service | Planned |
| FT-AI-007 | Tutor missing topic | Topic does not exist | Send tutor request | HTTP `404` | Planned |
| FT-AI-008 | Retrieve ordered chat history | Chat messages exist | `GET /api/ai/history/{user_id}/{topic_id}` | HTTP `200`; messages are returned in creation order | Planned |
| FT-AI-009 | Retrieve empty chat history | No messages exist | Request history | HTTP `200`; `messages` is an empty list | Planned |

## 9. Unit Test Cases

### 9.1 Hill-climbing assessor

| ID | Test case | Expected result | Status |
|---|---|---|---|
| UT-ALG-001 | Initialize below minimum difficulty | Difficulty is clamped to `1` | Automated |
| UT-ALG-002 | Initialize above maximum difficulty | Difficulty is clamped to `5` | Automated |
| UT-ALG-003 | Correct answer below maximum | Difficulty increases by one | Automated |
| UT-ALG-004 | Incorrect answer above minimum | Difficulty decreases by one | Planned |
| UT-ALG-005 | Correct answer at maximum | Peak is found at `5` | Automated |
| UT-ALG-006 | Incorrect answer at minimum | Peak is found at `0` | Automated |
| UT-ALG-007 | Correct answer after failure at next level | Existing peak is confirmed | Automated |
| UT-ALG-008 | Mastery score calculation | Score is numeric and remains between `0` and `100` | Automated |
| UT-ALG-009 | Empty history mastery | Score is `0.0` | Planned |

### 9.2 Roadmap generator

| ID | Test case | Expected result | Status |
|---|---|---|---|
| UT-ROAD-001 | Generate independent topics | All topics are returned in a valid order | Planned |
| UT-ROAD-002 | Respect prerequisite order | Prerequisite precedes dependent topic | Automated |
| UT-ROAD-003 | Mark mastered topic | Mastered topic is `completed` | Automated |
| UT-ROAD-004 | Unlock topic with mastered prerequisites | Topic is `unlocked` | Automated |
| UT-ROAD-005 | Lock topic with incomplete prerequisites | Topic is `locked` | Automated |
| UT-ROAD-006 | Detect cyclic graph | `ValueError` with cycle message is raised | Automated |
| UT-ROAD-007 | Limit next topics | `get_next_topics()` returns no more than requested limit | Planned |
| UT-ROAD-008 | Handle empty topic list | Empty roadmap is returned | Planned |

### 9.3 Knapsack scheduler

| ID | Test case | Expected result | Status |
|---|---|---|---|
| UT-SCHED-001 | Empty topic list | Empty selection and zero totals | Automated |
| UT-SCHED-002 | Zero capacity | Empty selection and zero totals | Automated |
| UT-SCHED-003 | Fractional hour values | Capacity calculation supports half-hour increments | Planned |
| UT-SCHED-004 | Budget constraint | Selected hours do not exceed capacity | Automated |
| UT-SCHED-005 | Priority optimization | Highest-value feasible combination is selected | Automated |
| UT-SCHED-006 | Utilization calculation | Returned utilization percentage is correct | Planned |

### 9.4 Resource sorting

| ID | Test case | Expected result | Status |
|---|---|---|---|
| UT-SORT-001 | Sort descending relevance | Highest score appears first | Automated |
| UT-SORT-002 | Empty input | Empty list is returned | Planned |
| UT-SORT-003 | Single-item input | Same item is returned | Planned |
| UT-SORT-004 | Equal scores | All equal-score items are retained | Planned |
| UT-SORT-005 | Missing key | Error behavior is explicit and controlled | Planned |

## 10. Performance and Load Test Cases

### 10.1 Benchmark cases

| ID | Test case | Workload | Expected result | Status |
|---|---|---|---|---|
| PT-BENCH-001 | Roadmap generation at 100 topics | 100 nodes and 99 prerequisite edges | Benchmark completes and result is valid | Benchmark |
| PT-BENCH-002 | Roadmap generation at 1,000 topics | 1,000 nodes and 999 prerequisite edges | Benchmark completes without excessive memory use | Benchmark |
| PT-BENCH-003 | Scheduler benchmark | 100 topics and 40 weekly hours | Benchmark completes and output respects budget | Benchmark |
| PT-BENCH-004 | Resource sorting benchmark | 1,000 resources | Benchmark completes with sorted output | Benchmark |
| PT-BENCH-005 | Roadmap generation at 10,000 topics | 10,000-node graph | Establish upper-bound latency and memory behavior | Planned |
| PT-BENCH-006 | Scheduler with large capacity | Large topic list and high weekly-hour capacity | Identify dynamic-programming memory growth | Planned |

### 10.2 Load cases

| ID | Test case | Workload | Measurements | Acceptance target | Status |
|---|---|---|---|---|---|
| PT-LOAD-001 | Baseline load | 1–5 users for 5 minutes | Throughput, P50, P95, errors | Establish baseline; no unexpected errors | Planned |
| PT-LOAD-002 | Expected concurrent load | 25–50 users | P50, P95, P99, CPU, memory | P95 under `500 ms` for non-AI endpoints; error rate under `1%` | Planned |
| PT-LOAD-003 | Stress test | Increase users until threshold breach | Maximum sustainable throughput | Threshold and failure mode are recorded | Planned |
| PT-LOAD-004 | Spike test | Increase rapidly from 5 to 100 users | Recovery time and errors | Service recovers without restart | Planned |
| PT-LOAD-005 | Soak test | Normal traffic for 1–4 hours | Memory, errors, latency drift | No material memory leak or latency drift | Planned |
| PT-LOAD-006 | Assessment concurrency | Concurrent answers for same and different users | Session consistency | No cross-user state contamination | Planned |
| PT-LOAD-007 | Roadmap generation load | Concurrent generation requests | Database writes, duration, failures | No partial or orphaned roadmap state | Planned |
| PT-LOAD-008 | AI isolation load | Stubbed slow, fast, timeout, and rate-limit responses | API latency and error handling | AI failures do not crash unrelated endpoints | Planned |

The current Locust scenario covers health, progress, roadmap, and scheduler reads with weighted tasks. It does not call real AI endpoints and should not be used against production services without a dedicated test plan.

## 11. CI/CD Test Cases

| ID | Test case | Trigger | Expected result | Status |
|---|---|---|---|---|
| CI-001 | CI on push to main | Push commit to `main` | Workflow starts and runs the test job | Implemented |
| CI-002 | CI on feature branch push | Push to `loitongbam-david-*` branch | Workflow starts and runs the test job | Implemented |
| CI-003 | CI on pull request | Open or update PR targeting `main` | Workflow starts and must pass before merge | Implemented |
| CI-004 | Python version selection | Workflow starts | Python version is read from `runtime.txt` | Implemented |
| CI-005 | Dependency installation | Workflow reaches install step | `requirements-dev.txt` installs successfully | Implemented |
| CI-006 | Test execution | Install succeeds | Pytest completes successfully and writes JUnit XML | Implemented |
| CI-007 | Test result artifact | Test job succeeds or fails | `test-results.xml` is uploaded using `if: always()` | Implemented |
| CI-008 | Failing test blocks CI | Introduce a controlled failing test | Job fails and PR cannot be treated as passing | Planned |
| CI-009 | Dependency cache reuse | Run workflow twice | Pip cache is restored on the second run when dependency files are unchanged | Planned |

## 12. Defect Classification

| Severity | Definition | Example |
|---|---|---|
| Critical | Prevents service startup, data integrity, or core user flow | API cannot start or progress data is corrupted |
| High | Breaks a major feature with no practical workaround | Roadmap generation always fails |
| Medium | Breaks a secondary path or produces incorrect isolated behavior | Incorrect progress percentage |
| Low | Cosmetic, wording, logging, or minor non-blocking issue | Inconsistent error text |

## 13. Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Assessment sessions are process-local | Sessions may disappear or diverge across workers | Add multi-worker tests; migrate session state to Redis or persistent storage before horizontal scaling |
| Supabase queries are sequential | Roadmap generation and progress updates may have high latency | Add query-count instrumentation and load tests with realistic data volumes |
| AI responses are nondeterministic | Tests may be flaky if they call Groq directly | Mock Groq for CI; maintain separate model-quality evaluation |
| AI output may be malformed | Roadmap priority parsing may fall back to defaults | Keep malformed JSON test and monitor fallback rate |
| Large knapsack capacity increases memory usage | Scheduler may exhaust memory | Benchmark high capacities and enforce input limits |
| External service outages | AI and persistence endpoints may fail | Add timeout, retry, and controlled-failure tests |
| Unbounded request content | Large prompts or histories may increase latency and cost | Add request-size validation and boundary tests |

## 14. Traceability Matrix

| Requirement area | Unit tests | API tests | Performance/load | CI |
|---|---|---|---|---|
| Service health | — | FT-HEALTH-001 | — | CI-001–CI-007 |
| Adaptive assessment | UT-ALG-001–009 | FT-ASSESS-001–013 | PT-LOAD-006 | CI-006 |
| Progress tracking | — | FT-PROG-001–010 | PT-LOAD-002 | CI-006 |
| Roadmap generation | UT-ROAD-001–008 | FT-ROADMAP-001–016 | PT-BENCH-001, PT-BENCH-002, PT-LOAD-007 | CI-006 |
| Weekly scheduler | UT-SCHED-001–006 | FT-SCHED-001–006 | PT-BENCH-003, PT-BENCH-006 | CI-006 |
| AI features | — | FT-AI-001–009 | PT-LOAD-008 | CI-006 |
| Resource sorting | UT-SORT-001–005 | — | PT-BENCH-004 | CI-006 |

## 15. Execution Instructions

### 15.1 Install dependencies

```bash
python -m pip install -r requirements-dev.txt
```

### 15.2 Run all tests

```bash
python -m pytest
```

### 15.3 Run only API tests

```bash
python -m pytest tests/api
```

### 15.4 Run only unit tests

```bash
python -m pytest tests/unit/test_algorithms.py
```

### 15.5 Run benchmarks

```bash
python -m pytest tests/unit/test_algorithm_benchmarks.py
```

### 15.6 Generate JUnit results

```bash
python -m pytest --junitxml=test-results.xml
```

### 15.7 Run Locust

```bash
locust -f tests/load/locustfile.py --host http://localhost:8000
```

## 16. Current Test Execution Record

The automated suite currently contains:

- 23 functional and algorithm tests.
- 4 benchmark tests.
- 27 total passing tests in the validated local run.

The CI workflow is configured to execute the same complete Pytest suite and publish the JUnit XML result. Load tests are available but are intentionally executed separately because they require a running service and seeded test data.

## 17. Approval

| Role | Name | Signature | Date |
|---|---|---|---|
| Test owner | TBD | TBD | TBD |
| Development owner | TBD | TBD | TBD |
| Product owner | TBD | TBD | TBD |
