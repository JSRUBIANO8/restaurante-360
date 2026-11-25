from datetime import date, timedelta
from locust import HttpUser, task, between

class Visitor(HttpUser):
    wait_time = between(0.1, 0.3)
    @task(2)
    def menu(self):
        self.client.get('/api/menu')
    @task(2)
    def availability(self):
        self.client.get('/api/availability', params={'day':str(date.today()+timedelta(days=1)), 'slot':'18:00'}, name='/api/availability')
    @task(1)
    def health(self):
        self.client.get('/health')
