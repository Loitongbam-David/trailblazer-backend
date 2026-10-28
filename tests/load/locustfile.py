from locust import HttpUser, between, task


class TrailblazerUser(HttpUser):
    wait_time = between(1, 3)

    @task(5)
    def health(self):
        self.client.get("/health")

    @task(3)
    def progress(self):
        self.client.get("/api/progress/load-test-user")

    @task(2)
    def roadmap(self):
        self.client.get("/api/roadmap/load-test-user")

    @task(2)
    def schedule(self):
        self.client.get("/api/scheduler/load-test-user")
