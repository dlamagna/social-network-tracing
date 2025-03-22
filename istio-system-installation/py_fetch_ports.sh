#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Define namespaces
DEATHSTAR_NAMESPACE="socialnetwork"
ISTIO_NAMESPACE="istio-system"

# Get the Node IP
NODE_IP=$(sudo kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')

# Get NodePorts for all relevant services, handling missing values gracefully
NGINX_PORT=$(sudo kubectl get svc nginx-thrift -n $DEATHSTAR_NAMESPACE -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null || echo "N/A")
PROMETHEUS_PORT=$(sudo kubectl get svc prometheus-server -n $ISTIO_NAMESPACE -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null || echo "N/A")
JAEGER_PORT=$(sudo kubectl get svc jaeger -n $DEATHSTAR_NAMESPACE -o jsonpath='{.spec.ports[?(@.port==16686)].nodePort}' 2>/dev/null || echo "N/A")
GRAFANA_PORT=$(sudo kubectl get svc grafana -n $ISTIO_NAMESPACE -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null || echo "N/A")

# Ensure Kiali is exposed correctly
KIALI_PORT=$(sudo kubectl get svc kiali -n $ISTIO_NAMESPACE -o jsonpath='{.spec.ports[?(@.port==20001)].nodePort}' 2>/dev/null || echo "N/A")

if [ "$KIALI_PORT" == "N/A" ]; then
    sudo kubectl patch svc kiali -n $ISTIO_NAMESPACE -p '{"spec": {"type": "NodePort"}}' >/dev/null 2>&1
    sleep 3
    KIALI_PORT=$(sudo kubectl get svc kiali -n $ISTIO_NAMESPACE -o jsonpath='{.spec.ports[?(@.port==20001)].nodePort}' 2>/dev/null || echo "N/A")
fi

# Get Istio Ingress Gateway NodePort
ISTIO_INGRESS_NAME=$(sudo kubectl get svc -n $ISTIO_NAMESPACE -o jsonpath='{.items[?(@.metadata.name=="istio-ingressgateway")].metadata.name}' 2>/dev/null || echo "")

if [ -z "$ISTIO_INGRESS_NAME" ]; then
    ISTIO_INGRESS_PORT="N/A"
else
    ISTIO_INGRESS_PORT=$(sudo kubectl get svc "$ISTIO_INGRESS_NAME" -n $ISTIO_NAMESPACE -o jsonpath='{.spec.ports[?(@.port==80)].nodePort}' 2>/dev/null || echo "N/A")
fi

# Change Local Port for Istio Ingress Gateway (Replace 80 → 8081)
LOCAL_ISTIO_PORT=8081

# Print the URLs in a clean format (keeping the original output structure)
echo "NGINX_URL=http://${NODE_IP}:${NGINX_PORT}"
echo "PROMETHEUS_URL=http://${NODE_IP}:${PROMETHEUS_PORT}"
echo "JAEGER_URL=http://${NODE_IP}:${JAEGER_PORT}"
echo "GRAFANA_URL=http://${NODE_IP}:${GRAFANA_PORT}"
echo "KIALI_URL=http://${NODE_IP}:${KIALI_PORT}"
echo "ISTIO_INGRESS_URL=http://${NODE_IP}:${LOCAL_ISTIO_PORT}"
