#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Function to check the status of pods
check_pod_status() {
  NAMESPACE=$1
  RETRIES=10
  echo "Checking pod status in namespace: $NAMESPACE"
  while [ $RETRIES -gt 0 ]; do
    PODS=$(sudo kubectl get pods -n $NAMESPACE -o jsonpath='{.items[*].status.phase}')
    NOT_READY=$(echo $PODS | grep -v "Running" || true)
    if [ -z "$NOT_READY" ]; then
      echo "All pods in namespace $NAMESPACE are running."
      return 0
    fi
    echo "Waiting for pods to be ready... Retries left: $RETRIES"
    sleep 10
    RETRIES=$((RETRIES-1))
  done
  echo "Error: Some pods are not in Running state in namespace $NAMESPACE"
  exit 1
}

# Step 1: Add Istio Helm Repository
echo "Adding Istio Helm repository..."
sudo helm repo add istio https://istio-release.storage.googleapis.com/charts
sudo helm repo update

# Step 2: Install Istio Base
echo "Installing Istio Base..."
sudo helm install istio-base istio/base -n istio-system --create-namespace

# Step 3: Install Istio Control Plane (Istiod)
echo "Installing Istiod..."
sudo helm install istiod istio/istiod -n istio-system

# Step 4: Install Istio Ingress Gateway as NodePort
echo "Installing Istio Ingress Gateway as NodePort..."
sudo helm install istio-ingress istio/gateway -n istio-system \
  --set service.type=NodePort \
  --set service.ports[0].name=http2 \
  --set service.ports[0].port=80 \
  --set service.ports[0].nodePort=32380 \
  --set service.ports[1].name=https \
  --set service.ports[1].port=443 \
  --set service.ports[1].nodePort=32443

# Step 5: Enable Automatic Sidecar Injection
echo "Enabling automatic sidecar injection in default namespace..."
sudo kubectl label namespace default istio-injection=enabled --overwrite

# Step 6: Check Istio Pod Status
check_pod_status "istio-system"

# Step 7: Deploy Kiali as NodePort
echo "Deploying Kiali with NodePort configuration..."
sudo kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.18/samples/addons/kiali.yaml

# Change Kiali service to NodePort
echo "Updating Kiali Service to NodePort..."
sudo kubectl patch svc kiali -n istio-system -p '{"spec": {"type": "NodePort"}}'

# Step 8: Check Kiali Pod Status
check_pod_status "istio-system"

# Step 9: Get Node IP and NodePort for Prometheus, Grafana, Kiali, and Istio Ingress
echo "Retrieving Node IP and NodePorts for Prometheus, Grafana, Kiali, and Istio Ingress Gateway..."

# Get Node IP
NODE_IP=$(sudo kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')

# Get Prometheus NodePort
PROMETHEUS_PORT=$(sudo kubectl get svc prometheus-server -n monitoring -o jsonpath='{.spec.ports[0].nodePort}')
PROMETHEUS_URL="http://${NODE_IP}:${PROMETHEUS_PORT}"

# Get Grafana NodePort
GRAFANA_PORT=$(sudo kubectl get svc grafana -n monitoring -o jsonpath='{.spec.ports[0].nodePort}')
GRAFANA_URL="http://${NODE_IP}:${GRAFANA_PORT}"

# Get Kiali NodePort
KIALI_PORT=$(sudo kubectl get svc kiali -n istio-system -o jsonpath='{.spec.ports[?(@.port==20001)].nodePort}')
KIALI_URL="http://${NODE_IP}:${KIALI_PORT}"

# Get Istio Ingress Gateway NodePort
ISTIO_INGRESS_PORT=$(sudo kubectl get svc istio-ingress -n istio-system -o jsonpath='{.spec.ports[?(@.port==80)].nodePort}')
ISTIO_INGRESS_URL="http://${NODE_IP}:${ISTIO_INGRESS_PORT}"

# Step 10: Output Access URLs
echo "=========================================="
echo "Istio and Kiali Installation Complete!"
echo "Access URLs:"
echo "Prometheus: ${PROMETHEUS_URL}"
echo "Grafana: ${GRAFANA_URL}"
echo "Kiali: ${KIALI_URL}"
echo "Istio Ingress Gateway: ${ISTIO_INGRESS_URL}"
echo "=========================================="
