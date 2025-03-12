This directory contains scripts for installing, configuring, and managing DeathStarBench-related monitoring and networking components, including **Prometheus, Grafana, Istio, and Kiali**.

---

### **1. `reinstall_deathstar.sh`**
- **Purpose:** Performs a **full purge and reinstallation** of DeathStarBench and its monitoring stack (**Prometheus, Grafana, and WRK2**).
- **Key Features:**
  - **Uninstalls and reinstalls DeathStarBench** (Social Network microservices). This includes uninstallation of the loader module wrk2.
  - **Cleans and recreates the `monitoring` namespace** for Prometheus and Grafana.
  - **Deploys Prometheus and Grafana as NodePort services** for external access.
  - **Builds WRK2** (load testing tool) from source.
  - **Ensures stuck pods are restarted** to avoid initialization issues.
  - **Fetches NodePort URLs** for key services like **NGINX, Prometheus, Jaeger, and Grafana**.

---

### **2. `install_istio_kiali.sh`**
- **Purpose:** Installs **Istio** and **Kiali** in the `monitoring` namespace.
- **Key Features:**
  - Installs Istio via **Helm**.
  - Deploys Istio **Ingress Gateway** using **NodePort**.
  - Enables automatic sidecar injection for services in `monitoring`.
  - Configures **Kiali** to use **Prometheus** as its backend.
  - Ensures all pods are running before proceeding.

---

### **3. `uninstall_istio_kiali.sh`**
- **Purpose:** Uninstalls **Istio** and **Kiali** from the `monitoring` namespace.
- **Key Features:**
  - Deletes **Kiali** using its official YAML configuration.
  - Uninstalls Istio components (`istio-ingress`, `istiod`, `istio-base`) via **Helm**.
  - Cleans up Istio **Custom Resource Definitions (CRDs)**.
  - Removes Istio-related namespace labels.

---

### **4. `fetch_ports.sh`**
- **Purpose:** Retrieves **NodePort** values for key services and exports them as environment variables.
- **Key Features:**
  - Fetches **NodePort** values for:
    - **NGINX (Social Network Frontend)**
    - **Prometheus**
    - **Jaeger**
    - **Grafana**
    - **Kiali**
    - **Istio Ingress Gateway**
  - Provides an **SSH command** for port forwarding.
  - Outputs **local access URLs** for services after SSH forwarding.

---

### **5. `py_fetch_ports.sh`**
- **Purpose:** A simplified version of `fetch_ports.sh`, outputting only the **service URLs** without additional logging.
- **Key Features:**
  - Fetches and prints **NodePort** mappings for **NGINX, Prometheus, Jaeger, Grafana, Kiali, and Istio Ingress Gateway**.
  - Designed for integration with Python scripts.

---

## **How Services are Deployed**
- **Namespace:** All monitoring services (**Prometheus, Grafana, Istio, Kiali**) are installed in the **`monitoring` namespace**.
- **Access:** The services are exposed via **NodePort**, making them accessible on the cluster nodes.

## **Usage Example**
To reinstall DeathStarBench and monitoring services:
```bash
chmod +x reinstall_deathstar.sh
./reinstall_deathstar.sh
```

To fetch service URLs after installation:

```bash
source fetch_ports.sh
echo $PROMETHEUS_URL
echo $GRAFANA_URL
```
