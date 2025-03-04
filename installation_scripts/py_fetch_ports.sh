#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Get the Node IP
NODE_IP=$(sudo kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')

# Get NodePorts for all relevant services
NGINX_PORT=$(sudo kubectl get svc nginx-thrift -n socialnetwork -o jsonpath='{.spec.ports[0].nodePort}')
PROMETHEUS_PORT=$(sudo kubectl get svc prometheus-server -n monitoring -o jsonpath='{.spec.ports[0].nodePort}')
JAEGER_PORT=$(sudo kubectl get svc jaeger -n socialnetwork -o jsonpath='{.spec.ports[?(@.port==16686)].nodePort}')
GRAFANA_PORT=$(sudo kubectl get svc grafana -n monitoring -o jsonpath='{.spec.ports[0].nodePort}')
KIALI_PORT=$(sudo kubectl get svc kiali -n istio-system -o jsonpath='{.spec.ports[?(@.port==20001)].nodePort}')

# Get Istio Ingress Gateway NodePort
ISTIO_INGRESS_NAME=$(sudo kubectl get svc -n istio-system -o jsonpath='{.items[?(@.metadata.name=="istio-ingress")].metadata.name}')

if [ -z "$ISTIO_INGRESS_NAME" ]; then
    ISTIO_INGRESS_PORT="N/A"
else
    ISTIO_INGRESS_PORT=$(sudo kubectl get svc "$ISTIO_INGRESS_NAME" -n istio-system -o jsonpath='{.spec.ports[?(@.port==80)].nodePort}')
fi

# Only print the variables in a clean format
echo "NGINX_URL=http://${NODE_IP}:${NGINX_PORT}"
echo "PROMETHEUS_URL=http://${NODE_IP}:${PROMETHEUS_PORT}"
echo "JAEGER_URL=http://${NODE_IP}:${JAEGER_PORT}"
echo "GRAFANA_URL=http://${NODE_IP}:${GRAFANA_PORT}"
echo "KIALI_URL=http://${NODE_IP}:${KIALI_PORT}"
echo "ISTIO_INGRESS_URL=http://${NODE_IP}:${ISTIO_INGRESS_PORT}"
