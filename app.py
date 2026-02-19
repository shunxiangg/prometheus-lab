from prometheus_client import start_http_server, Gauge
import random
import time

cpu_simulation = Gauge('cpu_usage_simulated', 'Simulated CPU usage')
memory_simulation = Gauge('memory_usage_simulated', 'Simulated memory usage')

start_http_server(8000)

while True:
    cpu_simulation.set(random.randint(0, 100))
    # cpu_simulation.set(100)
    # time.sleep(1)
    # cpu_simulation.set(0)
    # time.sleep(1)

    memory_simulation.set(random.randint(100, 1000))
    time.sleep(2)
