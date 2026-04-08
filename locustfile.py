from locust import HttpUser, task, between

class ENStartupUser(HttpUser):
    wait_time = between(0.5, 2)

    @task
    def load_homepage(self):
        self.client.get("/")