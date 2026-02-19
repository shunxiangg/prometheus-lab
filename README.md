# prometheus-lab

Small local lab to learn Prometheus from scratch on macOS.

Architecture:

`Python app (exporter) -> /metrics on :8000 -> Prometheus scrape -> query on :9090`

## Prerequisites (macOS)

- Python 3 (`python3`)
- Docker Desktop
- VS Code (optional but recommended)

Check tools:

```bash
python3 --version
docker --version
```

## Project Files

- `app.py`: simple app exporting fake CPU/memory metrics
- `prometheus.yml`: Prometheus scrape config

## 1) Install Python dependency

From this project folder:

```bash
python3 -m pip install prometheus_client
```

## 2) Run the metric app (exporter)

```bash
python3 app.py
```

Leave it running. In another terminal, verify metrics endpoint:

```bash
curl http://localhost:8000/metrics
```

Or open in browser: http://localhost:8000/metrics

## 3) Run Prometheus in Docker

From the same project folder:

```bash
docker run --rm -p 9090:9090 \
	-v "$PWD/prometheus.yml:/etc/prometheus/prometheus.yml" \
	prom/prometheus
```

Open Prometheus UI: http://localhost:9090

Check target status:

- `Status -> Targets`
- `my_app` should be `UP`

## 4) Query metrics

In the Prometheus expression box:

```promql
cpu_usage_simulated
```

```promql
avg_over_time(cpu_usage_simulated[30s])
```

You should see raw values vs smoothed values.

## 5) Create spikes (experiment)

In `app.py`, replace random CPU update with:

```python
cpu_simulation.set(100)
time.sleep(1)
cpu_simulation.set(0)
time.sleep(1)
```

Restart app:

1. Stop old app with `Ctrl+C`
2. Run `python3 app.py` again

Watch graph in Prometheus for spikes and smoothing.

## 6) Break it intentionally (sampling effect)

In `prometheus.yml`, change:

```yaml
scrape_interval: 5s
```

to:

```yaml
scrape_interval: 30s
```

Then restart Prometheus container (stop with `Ctrl+C`, rerun `docker run ...`).

Result: short spikes may disappear because scrape interval misses them.

## What Changes Between Parts

Use this to understand exactly what is different at each stage:

- **After Step 1 (install dependency)**
	- Change: Python environment now has `prometheus_client`.
	- Why it matters: `app.py` can expose Prometheus-format metrics.

- **After Step 2 (run app)**
	- Change: A local process starts and opens metrics endpoint on `:8000`.
	- Why it matters: You now have an exporter producing live metric values.

- **After Step 3 (run Prometheus)**
	- Change: Prometheus server starts on `:9090` and begins scraping `:8000`.
	- Why it matters: Metrics move from app-only to time-series stored in Prometheus.

- **After Step 4 (query metrics)**
	- Change: You are analyzing stored series with PromQL.
	- Why it matters: You can compare raw signal (`cpu_usage_simulated`) vs smoothing (`avg_over_time(...)`).

- **After Step 5 (create spikes)**
	- Change: Metric pattern changes from random values to sharp high/low bursts.
	- Why it matters: You can observe how short events appear (or blur) in graphs.

- **After Step 6 (increase scrape interval)**
	- Change: Sampling frequency becomes slower (`5s` -> `30s`).
	- Why it matters: Short spikes can be missed entirely, causing discrepancies between real behavior and observed metrics.

Summary: each part changes one layer only (producer, scraper, query, or sampling), so you can isolate cause-and-effect clearly.

## Stop everything

- App terminal: `Ctrl+C`
- Prometheus terminal: `Ctrl+C`

## Troubleshooting (macOS)

- If `python` fails, use `python3` everywhere.
- If `pip` fails, use `python3 -m pip ...`.
- Ensure Docker Desktop is running before `docker run`.
- If target is `DOWN`, confirm app is still running on port `8000`.