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

- `app.py`: simple app exporting fake CPU/memory metrics (gauges, counters, labels)
- `prometheus.yml`: Prometheus scrape config
- `alert.rules.yml`: example alerting rules (for experiment 6)

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

![Raw metric values](01_raw_metric.heic)

```promql
avg_over_time(cpu_usage_simulated[30s])
```

![Averaged over 30s](02_avg_30s.heic)

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

![Scrape interval 1s - catches spikes](03_scrape_1s.heic)

to:

```yaml
scrape_interval: 30s
```

![Scrape interval 30s - misses spikes](04_scrape_30s.heic)

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

---

# 🔬 Advanced Experiments

After completing the basic setup, these experiments will give you deep understanding of how Prometheus works and why it fails.

## Experiment 1: Missing Data (Understand Target Status)

**What to do:**

1. Keep Prometheus running
2. Stop your Python app: `Ctrl+C`
3. In Prometheus UI, query: `up`

**What you'll see:**
- `up{job="my_app"}` becomes `0`

**What it means:**
- `up = 1` → target reachable
- `up = 0` → target unreachable
- This is how alerting detects outages in real systems

## Experiment 2: Counters vs Gauges (Critical Difference)

Your app already has a counter: `requests_total`

**Try these queries:**

```promql
requests_total
```
- Only increases (monotonic)
- Graph shows cumulative value (meaningless for analysis)

```promql
rate(requests_total[10s])
```
- Shows requests per second
- This is the RIGHT way to use counters

```promql
rate(requests_total[1m])
```
- Smoother rate over 1 minute

**Key insight:** Counters MUST use `rate()` or `increase()`. Raw counter values are useless for analysis.

## Experiment 3: Labels (Multiple Time Series)

Your app already exports `cpu_usage{core="core1"}` and `cpu_usage{core="core2"}`

**Try these queries:**

```promql
cpu_usage
```
- Shows both series separately

```promql
avg(cpu_usage)
```
- Average across all cores

```promql
sum(cpu_usage)
```
- Total across all cores

```promql
cpu_usage{core="core1"}
```
- Filter to specific core

**Key insight:** Labels create multiple time series. This is how Prometheus handles multiple GPUs, pods, or instances.

## Experiment 4: Wrong Aggregation (Common Mistake)

Compare these:

```promql
sum(cpu_usage)
```
- Adds core1 + core2 (could exceed 100%)

```promql
avg(cpu_usage)
```
- Average of core1 and core2

**Key insight:** Wrong aggregation = wrong results. This causes many production monitoring bugs.

## Experiment 5: Scrape Interval Impact (Sampling Loss)

**What to do:**

1. In `app.py`, uncomment the spike code:
   ```python
   # cpu_simulation.set(100)
   # time.sleep(1)
   # cpu_simulation.set(0)
   # time.sleep(1)
   ```
   Comment out the random line above it
2. Restart app: `python3 app.py`
3. In `prometheus.yml`, change `scrape_interval: 30s`
4. Restart Prometheus

**What you'll see:**
- Short spikes (2 seconds) disappear completely
- Prometheus misses them because it only samples every 30 seconds

**Key insight:** High-frequency events can be invisible if scrape interval is too slow.

## Experiment 6: Alerting Rules

**Setup:**

1. Update `prometheus.yml` to include alert rules:
   ```yaml
   global:
     scrape_interval: 5s
   
   rule_files:
     - "alert.rules.yml"
   
   scrape_configs:
     - job_name: 'my_app'
       static_configs:
         - targets: ['host.docker.internal:8000']
   ```

2. Restart Prometheus with both config files mounted:
   ```bash
   docker run --rm -p 9090:9090 \
     -v "$PWD/prometheus.yml:/etc/prometheus/prometheus.yml" \
     -v "$PWD/alert.rules.yml:/etc/prometheus/alert.rules.yml" \
     prom/prometheus
   ```

3. Ensure app produces high CPU (>80) to trigger alert

**Check alerts:**
- Go to `Status → Rules`
- Go to `Alerts` tab
- Alert will be `PENDING` for 10s, then `FIRING`

**Key insight:** This is how production alerts work.

## Experiment 7: Time Range Windows

Test different window sizes:

```promql
rate(requests_total[10s])
```
- Reactive, noisy

```promql
rate(requests_total[1m])
```
- Balanced

```promql
rate(requests_total[10m])
```
- Stable, slow to react

**Key insight:** Short windows = fast reaction but noisy. Long windows = stable but miss spikes.

## Experiment 8: Break It On Purpose (Debugging)

**What to do:**

1. Query a metric name that doesn't exist: `fake_metric`
2. Check `Status → Targets`
3. Check `Status → TSDB Status`
4. Switch graph to Table view

**Key insight:** Learn to debug "why is my metric missing?"

## Optional: Add Grafana

```bash
docker run -d -p 3000:3000 grafana/grafana
```

Open: http://localhost:3000 (admin/admin)

1. Add Prometheus data source: `http://host.docker.internal:9090`
2. Create dashboard
3. Add panels with your metrics

**Key insight:** This is how monitoring looks in production.

---

## What You Should Understand Now

After completing experiments:

- ✅ What is scraping and sampling
- ✅ Difference between counters (use `rate()`) and gauges (use as-is)
- ✅ How labels create multiple time series
- ✅ Why wrong aggregation causes bugs
- ✅ Why scrape interval matters (sampling loss)
- ✅ How alerting rules work
- ✅ How time windows affect query results
- ✅ How to debug missing metrics

## Stop everything

- App terminal: `Ctrl+C`
- Prometheus terminal: `Ctrl+C`

## Troubleshooting (macOS)

- If `python` fails, use `python3` everywhere.
- If `pip` fails, use `python3 -m pip ...`.
- Ensure Docker Desktop is running before `docker run`.
- If target is `DOWN`, confirm app is still running on port `8000`.