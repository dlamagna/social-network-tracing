#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "🌐 Fetching Node IPs and NodePorts..."

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
    echo "⚠️  Istio Ingress Gateway not found. Skipping this service."
    ISTIO_INGRESS_PORT="N/A"
else
    ISTIO_INGRESS_PORT=$(sudo kubectl get svc "$ISTIO_INGRESS_NAME" -n istio-system -o jsonpath='{.spec.ports[?(@.port==80)].nodePort}')
fi

# Output SSH command for port forwarding
echo ""
echo "=========================================="
echo ""
echo "Use the following SSH command to access the services from your laptop:"
echo ""
echo "ssh -L 8080:${NODE_IP}:${NGINX_PORT} -L 9090:${NODE_IP}:${PROMETHEUS_PORT} -L 16686:${NODE_IP}:${JAEGER_PORT} -L 3000:${NODE_IP}:${GRAFANA_PORT} -L 20001:${NODE_IP}:${KIALI_PORT} -L 80:${NODE_IP}:${ISTIO_INGRESS_PORT} your-username@your-server-ip"
echo ""
echo "=========================================="

# Output NodePort Access URLs
echo ""
echo "Access the services directly using Node IP and NodePort:"
echo ""
echo "NGINX: http://${NODE_IP}:${NGINX_PORT}"
echo "Prometheus: http://${NODE_IP}:${PROMETHEUS_PORT}"
echo "Jaeger: http://${NODE_IP}:${JAEGER_PORT}"
echo "Grafana: http://${NODE_IP}:${GRAFANA_PORT}"
echo "Kiali: http://${NODE_IP}:${KIALI_PORT}"
echo "Istio Ingress Gateway: http://${NODE_IP}:${ISTIO_INGRESS_PORT}"
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
echo "Istio Ingress Gateway: http://localhost:80"
echo ""
echo "=========================================="
