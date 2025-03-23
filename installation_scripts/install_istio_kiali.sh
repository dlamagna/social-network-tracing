#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Namespace where Istio and Kiali should be installed
NAMESPACE="monitoring"

# Function to check the status of pods
check_pod_status() {
  NAMESPACE=$1
  RETRIES=10
  echo "Checking pod status in namespace: $NAMESPACE"
  while [ $RETRIES -gt 0 ]; do
    PODS=$(sudo kubectl get pods -n $NAMESPACE -o jsonpath='{.items[*].status.phase}')
    NOT_READY=$(echo $PODS | grep -v "Running" || true)
    if [ -z "$NOT_READY" ]; then
      echo "✅ All pods in namespace $NAMESPACE are running."
      return 0
    fi
    echo "⏳ Waiting for pods to be ready... Retries left: $RETRIES"
    sleep 10
    RETRIES=$((RETRIES-1))
  done
  echo "❌ Error: Some pods are not in Running state in namespace $NAMESPACE"
  exit 1
}

# Step 1: Add Istio Helm Repository
echo "📥 Adding Istio Helm repository..."
sudo helm repo add istio https://istio-release.storage.googleapis.com/charts || true
sudo helm repo update

# Ensure monitoring namespace exists
sudo kubectl create namespace $NAMESPACE --dry-run=client -o yaml | sudo kubectl apply -f -

# Step 2: Install or Upgrade Istio Base
echo "📦 Installing or upgrading Istio Base in $NAMESPACE namespace..."
if sudo helm list -n $NAMESPACE | grep -q "istio-base"; then
  sudo helm upgrade istio-base istio/base -n $NAMESPACE --set global.istioNamespace=$NAMESPACE
else
  sudo helm install istio-base istio/base -n $NAMESPACE --set global.istioNamespace=$NAMESPACE
fi

# Step 3: Install or Upgrade Istiod
echo "📦 Installing or upgrading Istiod in $NAMESPACE namespace..."
if sudo helm list -n $NAMESPACE | grep -q "istiod"; then
  sudo helm upgrade istiod istio/istiod -n $NAMESPACE --set global.istioNamespace=$NAMESPACE
else
  sudo helm install istiod istio/istiod -n $NAMESPACE --set global.istioNamespace=$NAMESPACE
fi

# Step 4: Install or Upgrade Istio Ingress Gateway as NodePort
echo "🌐 Installing or upgrading Istio Ingress Gateway in $NAMESPACE namespace..."
if sudo helm list -n $NAMESPACE | grep -q "istio-ingress"; then
  sudo helm upgrade istio-ingress istio/gateway -n $NAMESPACE \
    --set global.istioNamespace=$NAMESPACE \
    --set service.type=NodePort \
    --set service.ports[0].name=http2 --set service.ports[0].port=80 --set service.ports[0].nodePort=32380 \
    --set service.ports[1].name=https --set service.ports[1].port=443 --set service.ports[1].nodePort=32443
else
  sudo helm install istio-ingress istio/gateway -n $NAMESPACE \
    --set global.istioNamespace=$NAMESPACE \
    --set service.type=NodePort \
    --set service.ports[0].name=http2 --set service.ports[0].port=80 --set service.ports[0].nodePort=32380 \
    --set service.ports[1].name=https --set service.ports[1].port=443 --set service.ports[1].nodePort=32443
fi

# Step 5: Enable Automatic Sidecar Injection
echo "🔄 Enabling automatic sidecar injection in $NAMESPACE namespace..."
sudo kubectl label namespace $NAMESPACE istio-injection=enabled --overwrite

# Step 6: Check Istio Pod Status
check_pod_status "$NAMESPACE"

# Step 7: Deploy Kiali with NodePort
echo "📡 Deploying Kiali in $NAMESPACE namespace with NodePort..."
curl -LO https://raw.githubusercontent.com/istio/istio/release-1.18/samples/addons/kiali.yaml
sed -i "s/namespace: istio-system/namespace: $NAMESPACE/g" kiali.yaml
sed -i "s/type: ClusterIP/type: NodePort/g" kiali.yaml  # Ensure NodePort
sudo kubectl apply -f kiali.yaml

# Step 8: Check Kiali Pod Status
check_pod_status "$NAMESPACE"

# Step 9: Get Node IP and NodePorts for Kiali and Istio Ingress
echo "🌍 Retrieving Node IP and NodePorts for Kiali and Istio Ingress Gateway..."

# Get Node IP
NODE_IP=$(sudo kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')

# Get Kiali NodePort
KIALI_PORT=$(sudo kubectl get svc kiali -n $NAMESPACE -o jsonpath='{.spec.ports[?(@.port==20001)].nodePort}')
KIALI_URL="http://${NODE_IP}:${KIALI_PORT}"

# Get Istio Ingress Gateway NodePort
ISTIO_INGRESS_PORT=$(sudo kubectl get svc istio-ingress -n $NAMESPACE -o jsonpath='{.spec.ports[?(@.port==80)].nodePort}')
ISTIO_INGRESS_URL="http://${NODE_IP}:${ISTIO_INGRESS_PORT}"

# Print URLs
echo "✅ Kiali Dashboard: ${KIALI_URL}"
echo "✅ Istio Ingress Gateway: ${ISTIO_INGRESS_URL}"
