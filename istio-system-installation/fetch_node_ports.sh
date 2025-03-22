#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "🌐 Fetching Node IPs and NodePorts..."

# Set correct namespaces
DEATHSTAR_NAMESPACE="socialnetwork"
ISTIO_NAMESPACE="istio-system"

# Get the Node IP
NODE_IP=$(sudo kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')

# Get NodePorts for all relevant services
NGINX_PORT=$(sudo kubectl get svc nginx-thrift -n $DEATHSTAR_NAMESPACE -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null || echo "N/A")
PROMETHEUS_PORT=$(sudo kubectl get svc prometheus-server -n $ISTIO_NAMESPACE -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null || echo "N/A")
JAEGER_PORT=$(sudo kubectl get svc jaeger  -n $DEATHSTAR_NAMESPACE -o jsonpath='{.spec.ports[?(@.port==16686)].nodePort}' 2>/dev/null || echo "N/A")
GRAFANA_PORT=$(sudo kubectl get svc grafana -n $ISTIO_NAMESPACE -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null || echo "N/A")

# Ensure Kiali is exposed correctly
KIALI_PORT=$(sudo kubectl get svc kiali -n $ISTIO_NAMESPACE -o jsonpath='{.spec.ports[?(@.port==20001)].nodePort}' 2>/dev/null || echo "N/A")

if [ "$KIALI_PORT" == "N/A" ]; then
    echo "⚠️ Kiali is not exposed as a NodePort! Patching service..."
    sudo kubectl patch svc kiali -n $ISTIO_NAMESPACE -p '{"spec": {"type": "NodePort"}}'
    sleep 3  # Wait for the patch to take effect
    KIALI_PORT=$(sudo kubectl get svc kiali -n $ISTIO_NAMESPACE -o jsonpath='{.spec.ports[?(@.port==20001)].nodePort}' 2>/dev/null || echo "N/A")
fi

# Get Istio Ingress Gateway NodePort
ISTIO_INGRESS_NAME=$(sudo kubectl get svc -n $ISTIO_NAMESPACE -o jsonpath='{.items[?(@.metadata.name=="istio-ingressgateway")].metadata.name}' 2>/dev/null || echo "")

if [ -z "$ISTIO_INGRESS_NAME" ]; then
    echo "⚠️  Istio Ingress Gateway not found. Skipping this service."
    ISTIO_INGRESS_PORT="N/A"
else
    ISTIO_INGRESS_PORT=$(sudo kubectl get svc "$ISTIO_INGRESS_NAME" -n $ISTIO_NAMESPACE -o jsonpath='{.spec.ports[?(@.port==80)].nodePort}' 2>/dev/null || echo "N/A")
fi

# Change Local Port for Istio Ingress Gateway (Replace 80 → 8081)
LOCAL_ISTIO_PORT=8081

# Export Environment Variables for Node IP and NodePort Combos
echo ""
echo "=========================================="
echo "Exporting Node IP and NodePort combinations as environment variables..."
export NGINX_URL="http://${NODE_IP}:${NGINX_PORT}"
export PROMETHEUS_URL="http://${NODE_IP}:${PROMETHEUS_PORT}"
export JAEGER_URL="http://${NODE_IP}:${JAEGER_PORT}"
export GRAFANA_URL="http://${NODE_IP}:${GRAFANA_PORT}"
export KIALI_URL="http://${NODE_IP}:${KIALI_PORT}"
export ISTIO_INGRESS_URL="http://${NODE_IP}:${ISTIO_INGRESS_PORT}"

echo "export NGINX_URL=${NGINX_URL}"
echo "export PROMETHEUS_URL=${PROMETHEUS_URL}"
echo "export JAEGER_URL=${JAEGER_URL}"
echo "export GRAFANA_URL=${GRAFANA_URL}"
echo "export KIALI_URL=${KIALI_URL}"
echo "export ISTIO_INGRESS_URL=${ISTIO_INGRESS_URL}"
echo ""
echo "Environment variables set for Python script integration."
echo "=========================================="

# Output SSH command for port forwarding
echo ""
echo "Use the following SSH command to access the services from your laptop:"
echo ""
echo "ssh -L 8080:${NODE_IP}:${NGINX_PORT} -L 9090:${NODE_IP}:${PROMETHEUS_PORT} -L 16686:${NODE_IP}:${JAEGER_PORT} -L 3000:${NODE_IP}:${GRAFANA_PORT} -L 20001:${NODE_IP}:${KIALI_PORT} -L ${LOCAL_ISTIO_PORT}:${NODE_IP}:${ISTIO_INGRESS_PORT} -X dlamagna@147.83.130.183 -p 13000"
echo ""
echo "=========================================="

# Output Localhost Access URLs after SSH Port Forwarding
echo ""
echo "Access the services locally on your laptop using the following URLs:"
echo ""
echo "NGINX: http://localhost:8080"
echo "Prometheus: http://localhost:9090"
echo "Jaeger: http://localhost:16686"
echo "Grafana: http://localhost:3000"
echo "Kiali: http://localhost:20001"
echo "Istio Ingress Gateway: http://localhost:${LOCAL_ISTIO_PORT}"
echo ""
echo "=========================================="
