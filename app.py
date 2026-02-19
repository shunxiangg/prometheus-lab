from prometheus_client import start_http_server, Gauge, Counter
import random
import time

# Define all metrics
cpu_simulation = Gauge('cpu_usage_simulated', 'Simulated CPU usage')
memory_simulation = Gauge('memory_usage_simulated', 'Simulated memory usage')
request_counter = Counter('requests_total', 'Total requests')
cpu = Gauge('cpu_usage', 'CPU usage', ['core'])

# Start the metrics HTTP server
start_http_server(8000)

# Main loop - updates all metrics
while True:
    # Update simulated CPU (random values)
    cpu_simulation.set(random.randint(0, 100))
    # Uncomment below for spike experiment (comment line above):
    # cpu_simulation.set(100)
    # time.sleep(1)
    # cpu_simulation.set(0)
    # time.sleep(1)

    # Update simulated memory
    memory_simulation.set(random.randint(100, 1000))
    
    # Increment request counter
    request_counter.inc()
    
    # Update labeled CPU metrics (multi-core simulation)
    cpu.labels(core='core1').set(random.randint(20, 50))
    cpu.labels(core='core2').set(random.randint(40, 80))
    
    time.sleep(2)
