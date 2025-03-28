# Social Network Tracing & Metrics Collector

This repository provides a full tracing and metrics pipeline for benchmarking the [DeathStarBench Social Network](https://github.com/delimitrou/DeathStarBench/tree/master/socialNetwork) microservices application, running in a Kubernetes environment with Istio and Prometheus. It is designed to collect, process, and visualize pod-level metrics and inter-service traces using `wrk2`, Prometheus, and Jaeger. Additional metrics are then collected with Istio and Kiali

---

## Repository Structure

```
social-network-tracing/
├── tracer.py               # Main driver script: runs load tests, extracts traces, collects metrics, saves visualizations
├── prom_queries.py         # Dictionary of standard Prometheus queries for HTTP, CPU, memory, network metrics
├── data/                   # Output folder for raw CSV metric data (auto-generated)
├── visualizations/         # Output folder for visualizations per service (auto-generated)
├── istio-system-installation/
│   └── ...                 # Manifests/scripts to install Istio and supporting components
```

---

## Features

- **Service Dependency Mapping** via Jaeger `/api/dependencies`
- **Dynamic Metric Querying** from Prometheus using auto-generated PromQL per service
- **Pod-Level Resource Usage**: CPU, memory, network in/out
- **wrk2 Integration** to run performance tests and collect aligned metrics
- **Visualization**: Auto-generates per-service graphs and exports them as PNG
- **Organized Outputs**: Saves data to `data/<service>/metric.csv` and `visualizations/<service>/metric.png`

---

## Quickstart

### 1. Clone and Set Up
```bash
git clone https://github.com/dlamagna/social-network-tracing.git
cd social-network-tracing
```

### 2. Prerequisites

- Kubernetes cluster with Istio and Prometheus installed
- [DeathStarBench Social Network](https://github.com/delimitrou/DeathStarBench/tree/master/socialNetwork) deployed
- Prometheus and Jaeger must be exposed locally (port-forward or SSH tunnel)
- Python 3.10+ environment

Install dependencies:
```bash
pip install -r requirements.txt
```

> Optional: ensure Istio and telemetry stack are installed using manifests in `istio-system-installation/`

---

### 3. Run the Tracing Script

```bash
python3 tracer.py
```

This will:

1. Connect sto configured nodeports int he kubernetes cluster
2. Run a `wrk2` test.
3. Extract the Jaeger dependency graph.
4. Generate service-aware Prometheus queries.
5. Collect metrics during the test time window.
6. Save CSV data and plots for each service/pod metric.

---

## Output Example

```
data/
  └── user-service/
        ├── cpu_usage_per_pod.csv
        └── memory_usage_per_pod.csv

visualizations/
  └── user-service/
        ├── cpu_usage_per_pod.png
        └── memory_usage_per_pod.png
```

---

## Prometheus Queries

Defined in `prom_queries.py`. Includes:

- HTTP request success/4xx/5xx/error rates
- CPU & memory usage per pod
- Network transmit/receive bandwidth
- Custom latency or percentile queries

---

## Customization

### Change Query Window
In `tracer.py`, adjust the `start_time` and `end_time` logic to change the metrics window.

### Add Custom Metrics
Add new entries to `PROMETHEUS_QUERIES` in `prom_queries.py` using valid PromQL.

---

## Cluster Setup (Istio + Prometheus)

To install Istio and dependencies:
```bash
chmod +x istio-system-installation/reinstall_deathstar.sh
./istio-system-installation/reinstall_deathstar.sh

```

Ensure Prometheus is scraping:
- `kubelet`
- `cadvisor`
- `istio-proxy`
- `kube-state-metrics` (if used for replica/capacity metrics)

---

## Author

Created by [Davide Lamagna](https://github.com/dlamagna)