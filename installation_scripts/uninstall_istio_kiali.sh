#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "Uninstalling Istio and Kiali..."

# Step 1: Uninstall Kiali
echo "Deleting Kiali..."
sudo kubectl delete -f https://raw.githubusercontent.com/istio/istio/release-1.18/samples/addons/kiali.yaml || true

# Step 2: Uninstall Istio using Helm
echo "Uninstalling Istio components..."
sudo helm uninstall istio-ingress -n istio-system || true
sudo helm uninstall istiod -n istio-system || true
sudo helm uninstall istio-base -n istio-system || true

# Step 3: Delete Istio Namespaces
echo "Deleting Istio namespaces..."
sudo kubectl delete namespace istio-system || true

# Step 4: Clean up Istio CRDs
echo "Cleaning up Istio CRDs..."
sudo kubectl get crds | grep 'istio.io' | awk '{print $1}' | xargs sudo kubectl delete crd || true

# Step 5: Remove Labels from Namespaces
echo "Removing istio-injection labels..."
sudo kubectl label namespace default istio-injection- || true

echo "=========================================="
echo "Istio and Kiali Uninstallation Complete!"
echo "=========================================="
