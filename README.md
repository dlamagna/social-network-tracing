# Social Network Tracing and Monitoring

## Overview
This repository contains a comprehensive system for monitoring, tracing, and analyzing the performance of a social network microservices application (DeathStarBench) running on Kubernetes with Istio service mesh. The system provides detailed metrics collection, visualization, and analysis capabilities.

## Key Components

### 1. Main Components
- `tracer.py`: The core script that orchestrates the monitoring and tracing process
- `reinstall_deathstar.sh`: Installation script for setting up the entire environment
- `prom_queries.py`: Contains Prometheus queries for various metrics
- `utils.py`: Utility functions for the monitoring system
- `aggregate_data.py`: Script for aggregating collected metrics

### 2. Directory Structure
```
.
├── data/                  # Storage for collected metrics
├── visualizations/        # Generated visualizations
├── istio-system-installation/  # Istio setup scripts
├── installation_scripts/  # Additional installation scripts
├── grafana/              # Grafana configuration
└── aggregate/           # Data aggregation outputs
```

## Features

### 1. Metrics Collection
- HTTP request success rates
- Request latency (95th percentile)
- CPU and memory usage
- Network traffic metrics
- Service-specific metrics for:
  - Compose service
  - Nginx
  - Text service
  - User mention service

### 2. Visualization
- Automatic generation of metric visualizations
- Network map visualization
- Service dependency graphs
- Performance trend analysis

### 3. Monitoring Stack
- Prometheus for metrics collection
- Grafana for visualization
- Jaeger for distributed tracing
- Kiali for service mesh visualization
- WRK2 for load testing

## Prerequisites
- Kubernetes cluster
- Istio service mesh
- Python 3.x
- WRK2
- Helm

## Installation

1. Clone the repository
2. Run the installation script:
```bash
./istio-system-installation/reinstall_deathstar.sh
```

This script will:
- Install/update DeathStarBench
- Deploy Istio
- Set up monitoring tools (Prometheus, Grafana, Jaeger)
- Configure service mesh
- Deploy the social network application

## Usage

1. Start the monitoring system:
```bash
python3 tracer.py
```

2. Access the monitoring interfaces:
- Grafana: `http://<node-ip>:<grafana-port>`
- Kiali: `http://<node-ip>:<kiali-port>`
- Jaeger: `http://<node-ip>:<jaeger-port>`
- Prometheus: `http://<node-ip>:<prometheus-port>`

## Key Metrics Monitored

1. HTTP Metrics:
   - Success rates (2xx, 4xx, 5xx)
   - Request latency
   - Total request counts

2. Resource Metrics:
   - CPU usage and utilization
   - Memory usage
   - Network traffic (receive/transmit)

3. Service-specific Metrics:
   - Replica counts
   - Service-specific CPU consumption
   - Service-specific utilization rates

## Data Collection and Analysis

The system collects metrics in two main ways:
1. Real-time monitoring through Prometheus
2. Load testing through WRK2

Data is stored in:
- CSV files in the `data/` directory
- Visualizations in the `visualizations/` directory

## Dependencies
Key Python packages:
- prometheus_api_client
- pandas
- matplotlib
- seaborn
- networkx
- numpy

## Configuration
- Prometheus queries are defined in `prom_queries.py`
- Test parameters are configurable in `tracer.py`
- Installation parameters can be modified in `reinstall_deathstar.sh`

### Port Management Scripts
The repository includes two scripts for managing service endpoints, designed to work with a remote Kubernetes cluster:

1. `fetch_node_ports.sh`: A comprehensive script that:
   - Fetches NodePorts for all monitoring services (Prometheus, Grafana, Jaeger, Kiali)
   - Sets up SSH port forwarding commands for local access
   - Exports environment variables for Python integration
   - Provides localhost URLs for accessing services
   - Handles automatic patching of services if needed

2. `py_fetch_ports.sh`: A lightweight version that:
   - Focuses on collecting NodePorts for core services
   - Outputs clean URL format for Python environment variables
   - Used primarily by the Python monitoring scripts

Both scripts automatically detect and configure:
- NGINX service endpoints
- Prometheus monitoring endpoints
- Jaeger tracing endpoints
- Grafana visualization endpoints
- Kiali service mesh endpoints
- Istio ingress gateway endpoints

#### Remote Server Configuration
The scripts are designed to work with a remote Kubernetes cluster. Configuration is managed through a `.env` file with the following parameters:

```bash
# SSH Connection Details
USER=           # Your SSH username
SERVER=         # Remote server hostname/IP
PORT=           # SSH port number

# Kubernetes Namespaces
DEATHSTAR_NAMESPACE=socialnetwork    # Namespace for the social network application
ISTIO_NAMESPACE=istio-system         # Namespace for Istio and monitoring tools
```

The scripts use these parameters to:
- Connect to the remote Kubernetes cluster
- Set up SSH port forwarding for local access
- Configure the correct namespaces for service discovery
- Export environment variables for the monitoring tools

These scripts ensure proper connectivity between the monitoring tools and the services being monitored, even when working with a remote cluster.

## Notes
- The system is designed to work with the DeathStarBench social network application
- All services are exposed as NodePort for easy access
- The installation script includes automatic cleanup of previous installations
- The system supports both real-time monitoring and historical data analysis

## Contributing
Feel free to submit issues and enhancement requests!

