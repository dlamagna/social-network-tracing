# Installation Scripts Documentation

This directory contains scripts for setting up and managing the social network monitoring environment. Below is a detailed breakdown of each script and its functionality.

## Scripts Overview

### 1. `reinstall_deathstar.sh`
The main installation script that sets up the entire environment.

**Features:**
- Installs/updates DeathStarBench social network application
- Deploys Istio service mesh
- Sets up monitoring stack (Prometheus, Grafana, Jaeger)
- Configures Kiali for service mesh visualization
- Exposes services as NodePorts

**Namespaces:**
- `socialnetwork`: For the social network application
- `istio-system`: For Istio and monitoring tools

**Services and Ports:**
- NGINX: NodePort (dynamic)
- Prometheus: NodePort (dynamic)
- Grafana: NodePort (dynamic)
- Jaeger: NodePort (dynamic)
- Kiali: NodePort (dynamic)
- Istio Ingress Gateway: NodePort (dynamic)

### 2. `install_istio_kiali.sh`
Installs Istio and Kiali with specific configurations.

**Features:**
- Installs latest Istio version
- Configures Istio with demo profile
- Sets up Kiali with anonymous authentication
- Enables telemetry and tracing
- Configures service mesh visualization

**Components:**
- Istio Control Plane
- Kiali Dashboard
- Jaeger Tracing
- Prometheus Integration

### 3. `uninstall_istio_kiali.sh`
Cleanup script for removing Istio and Kiali.

**Actions:**
- Removes Istio installation
- Uninstalls Kiali
- Cleans up related resources
- Removes webhook configurations

### 4. Port Management Scripts

#### a. `fetch_node_ports.sh`
Comprehensive script for managing service endpoints.

**Features:**
- Fetches all service NodePorts
- Sets up SSH port forwarding
- Exports environment variables
- Provides localhost URLs
- Handles service patching

**Environment Variables:**
```bash
NGINX_URL=http://<node-ip>:<port>
PROMETHEUS_URL=http://<node-ip>:<port>
JAEGER_URL=http://<node-ip>:<port>
GRAFANA_URL=http://<node-ip>:<port>
KIALI_URL=http://<node-ip>:<port>
ISTIO_INGRESS_URL=http://<node-ip>:<port>
```

#### b. `py_fetch_ports.sh`
Lightweight version for Python integration.

**Features:**
- Collects core service NodePorts
- Outputs clean URL format
- Used by Python monitoring scripts

#### c. `fetch_ports.sh`
Alternative port fetching script with additional features.

**Features:**
- Service endpoint discovery
- Port verification
- Environment variable setup

### 5. `kind-config.yaml`
Kubernetes in Docker (Kind) configuration file.

**Features:**
- Defines cluster configuration
- Sets up node specifications
- Configures networking

## Installation Process

1. **Initial Setup:**
   ```bash
   ./reinstall_deathstar.sh
   ```

2. **Port Configuration:**
   ```bash
   ./fetch_node_ports.sh
   ```

3. **Environment Variables:**
   Create a `.env` file with:
   ```bash
   USER=<ssh-username>
   SERVER=<remote-host>
   PORT=<ssh-port>
   DEATHSTAR_NAMESPACE=socialnetwork
   ISTIO_NAMESPACE=istio-system
   ```

## Monitoring Stack Components

### Prometheus
- Metrics collection
- Service monitoring
- Performance tracking

### Grafana
- Metrics visualization
- Dashboard creation
- Performance analysis

### Jaeger
- Distributed tracing
- Request tracking
- Service dependency mapping

### Kiali
- Service mesh visualization
- Traffic monitoring
- Configuration management

## Notes
- All services are exposed as NodePort for easy access
- Scripts include automatic cleanup of previous installations
- Remote access is configured through SSH port forwarding
- Environment variables are used for service discovery
- Monitoring tools are integrated with Istio service mesh 