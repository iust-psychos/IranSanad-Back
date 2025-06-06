from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 2)

    @task
    def get_posts(self):
        self.client.get("/api/v1/hello-world")
        