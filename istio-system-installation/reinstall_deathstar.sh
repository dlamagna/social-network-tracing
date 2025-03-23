#!/bin/bash

echo "🛠️ Starting full purge and reinstall of DeathStarBench, Istio, Prometheus, Grafana, and WRK2..."

# Set namespaces
DEATHSTAR_NAMESPACE="socialnetwork"
ISTIO_NAMESPACE="istio-system"

# 0️⃣ Uninstall WRK2 (if exists)
echo "🧹 Uninstalling existing WRK2..."
cd ~/projects/DeathStarBench/wrk2/wrk2
make clean
echo "✅ WRK2 uninstalled."

# 1️⃣ Purge DeathStarBench (Social Network)
echo "🛠️ Purging DeathStarBench..."
if sudo helm list -n $DEATHSTAR_NAMESPACE | grep -q "social-network"; then
    sudo helm uninstall social-network -n $DEATHSTAR_NAMESPACE
else
    echo "⚠️ Helm release 'social-network' not found, skipping uninstall."
fi

sudo kubectl delete all --all -n $DEATHSTAR_NAMESPACE --ignore-not-found
sudo kubectl delete pvc --all -n $DEATHSTAR_NAMESPACE --ignore-not-found
sudo kubectl delete namespace $DEATHSTAR_NAMESPACE --ignore-not-found
sudo kubectl create namespace $DEATHSTAR_NAMESPACE
sudo kubectl label namespace socialnetwork istio-injection=enabled --overwrite

echo "✅ DeathStarBench removed."

# 2️⃣ Purge Monitoring Tools (Prometheus, Grafana, nginx-exporter)
echo "🛠️ Purging Prometheus, Grafana, and monitoring tools..."
for release in prometheus grafana nginx-prometheus-exporter; do
    if sudo helm list -n $ISTIO_NAMESPACE | grep -q "$release"; then
        sudo helm uninstall "$release" -n $ISTIO_NAMESPACE
    else
        echo "⚠️ Helm release '$release' not found, skipping uninstall."
    fi
done

sudo kubectl delete all --all -n $ISTIO_NAMESPACE --ignore-not-found
sudo kubectl delete pvc --all -n $ISTIO_NAMESPACE --ignore-not-found
sudo kubectl delete namespace $ISTIO_NAMESPACE --ignore-not-found
sudo kubectl create namespace $ISTIO_NAMESPACE
echo "✅ Monitoring tools removed."

# 3️⃣ Clone or Update DeathStarBench
if [ ! -d ~/projects/DeathStarBench/.git ]; then
    echo "🚀 Cloning DeathStarBench repository..."
    git clone git@github.com:delimitrou/DeathStarBench.git ~/projects/DeathStarBench
else
    echo "🔄 Updating existing DeathStarBench repository..."
    cd ~/projects/DeathStarBench
    git checkout master && git pull
fi

# 4️⃣ Apply Pull Request #352
echo "🔄 Applying Pull Request #352..."
cd ~/projects/DeathStarBench
git reset --hard HEAD
git clean -fd
git checkout master
git pull origin master
git fetch origin pull/352/head:pr-352
git checkout pr-352
echo "✅ Pull Request #352 applied."

# 5️⃣ Deploy Istio (if not installed)
## remove existing webhooks:
sudo kubectl delete mutatingwebhookconfiguration istio-sidecar-injector || true
sudo kubectl delete mutatingwebhookconfiguration istio-revision-tag-default || true

## install istio

ISTIO_VERSION=$(curl -sL https://api.github.com/repos/istio/istio/releases/latest | jq -r ".tag_name" | sed 's/^v//')
echo "Using Istio version: $ISTIO_VERSION"
curl -L https://istio.io/downloadIstio | ISTIO_VERSION=$ISTIO_VERSION sh -
cd ~/projects/DeathStarBench/istio-$ISTIO_VERSION/bin
export PATH=$PWD:$PATH
cd ..

# Install Istio with demo profile (includes telemetry and tracing)

# Make istioctl available system wide:
sudo rm -f /usr/local/bin/istioctl
sudo ln -s ~/projects/DeathStarBench/istio-$ISTIO_VERSION/bin/istioctl /usr/local/bin/istioctl

sudo istioctl install --set profile=demo -y
sudo kubectl wait --for=condition=available --timeout=120s deployment/istiod -n $ISTIO_NAMESPACE

# 6️⃣ Deploy DeathStarBench using Helm
echo "📦 Deploying Social Network using Helm..."
cd ~/projects/DeathStarBench/socialNetwork
sudo helm install social-network ./helm-chart/socialnetwork -n $DEATHSTAR_NAMESPACE
echo "✅ DeathStarBench reinstalled."

# 7️⃣ Deploy Prometheus, Grafana, and Jaeger for Monitoring (as NodePort)
echo "📊 Deploying Prometheus, Grafana, and Jaeger..."
sudo helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
sudo helm repo add grafana https://grafana.github.io/helm-charts
sudo helm repo update

sudo helm install prometheus prometheus-community/prometheus -n $ISTIO_NAMESPACE --set server.service.type=NodePort
sudo helm install grafana grafana/grafana -n $ISTIO_NAMESPACE \
  --set adminPassword=admin \
  --set service.type=NodePort \
  --set persistence.enabled=true \
  --set persistence.size=10Gi
echo "✅ Monitoring stack deployed."

# 8️⃣ Deploy nginx-prometheus-exporter
echo "📡 Deploying nginx-prometheus-exporter..."
sudo helm install nginx-prometheus-exporter prometheus-community/prometheus-nginx-exporter -n $ISTIO_NAMESPACE
echo "✅ nginx-prometheus-exporter deployed."

# 9️⃣ Deploy Kiali and enable telemetry
sudo kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.17/samples/addons/jaeger.yaml -n $ISTIO_NAMESPACE

cat <<EOF | sudo kubectl apply -n $ISTIO_NAMESPACE -f -
apiVersion: telemetry.istio.io/v1alpha1
kind: Telemetry
metadata:
  name: telemetry-config
spec:
  accessLogging:
  - providers:
    - name: envoy
  tracing:
  - providers:
    - name: "jaeger"
EOF
echo "✅ Kiali, Jaeger, and telemetry enabled."

# 🔟 Expose Services as NodePort
for svc in kiali prometheus-server grafana istio-ingressgateway; do
  sudo kubectl patch svc $svc -n $ISTIO_NAMESPACE -p '{"spec": {"type": "NodePort"}}'
done

for svc in jaeger nginx-thrift; do
  sudo kubectl patch svc $svc -n $DEATHSTAR_NAMESPACE -p '{"spec": {"type": "NodePort"}}'
done

# 1️⃣1️⃣ Wait for Pods to Be Ready
echo "⏳ Waiting for pods to become ready..."
sleep 60

# 1️⃣2️⃣ Restart Any Stuck Pods
echo "🔍 Checking for pods stuck in 'Init' state..."
stuck_pods=$(sudo kubectl get pods -n $DEATHSTAR_NAMESPACE | grep 'Init' | awk '{print $1}')
if [ -n "$stuck_pods" ]; then
    echo "⚠️ Restarting stuck pods..."
    for pod in $stuck_pods; do
        sudo kubectl delete pod "$pod" -n $DEATHSTAR_NAMESPACE
    done
    sleep 20
else
    echo "✅ No pods stuck in 'Init' state."
fi

# 1️⃣3️⃣ Build WRK2 in the Correct Directory
echo "⚙️ Building WRK2..."
cd ~/projects/DeathStarBench/wrk2/wrk2
make
echo "✅ WRK2 built successfully."

# 1️⃣4️⃣ Get Node Ports for Monitoring
echo "🌐 Fetching NodePorts..."
NODE_IP=$(sudo kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')

# Get NodePorts for all relevant services, handling missing values gracefully
NGINX_PORT=$(sudo kubectl get svc nginx-thrift -n $DEATHSTAR_NAMESPACE -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null || echo "N/A")
PROMETHEUS_PORT=$(sudo kubectl get svc prometheus-server -n $ISTIO_NAMESPACE -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null || echo "N/A")
JAEGER_PORT=$(sudo kubectl get svc jaeger -n $DEATHSTAR_NAMESPACE -o jsonpath='{.spec.ports[?(@.port==16686)].nodePort}' 2>/dev/null || echo "N/A")

echo "🎯 Deployment Complete!"


# Print the URLs in a clean format (keeping the original output structure)
echo "NGINX_URL=http://${NODE_IP}:${NGINX_PORT}"
echo "PROMETHEUS_URL=http://${NODE_IP}:${PROMETHEUS_PORT}"
echo "JAEGER_URL=http://${NODE_IP}:${JAEGER_PORT}"

#### UPDATE kiali config with correct nodeport for prometheus

#!/bin/bash

echo "Installing Kiali via Helm with anonymous auth, Prometheus URL, and NodePort service..."
sudo helm install kiali-server \
  --namespace ${ISTIO_NAMESPACE} \
  --set auth.strategy="anonymous" \
  --set external_services.prometheus.url="http://${NODE_IP}:${PROMETHEUS_PORT}" \
  --set kiali.service.type=NodePort \
  --repo https://kiali.org/helm-charts \
  kiali-server

echo "Waiting for the Kiali pod to be ready..."
sleep 30  # Adjust the sleep duration as needed

echo "Retrieving Kiali pod status:"
sudo kubectl get pods -n ${ISTIO_NAMESPACE} -l app=kiali

SERVICE_TYPE=$(sudo kubectl get svc kiali -n "${ISTIO_NAMESPACE}" -o jsonpath='{.spec.type}')
if [ "$SERVICE_TYPE" != "NodePort" ]; then
    sudo kubectl patch svc kiali -n "${ISTIO_NAMESPACE}" -p '{"spec": {"type": "NodePort"}}'
    sleep 5
fi
SERVICE_TYPE=$(sudo kubectl get svc kiali -n "${ISTIO_NAMESPACE}" -o jsonpath='{.spec.type}')

echo "Updated Kiali service type is: ${SERVICE_TYPE}"
echo "KIALI_URL=http://${NODE_IP}:${KIALI_PORT}"

# Retrieve NodePorts for Grafana and Kiali services
GRAFANA_PORT=$(sudo kubectl get svc grafana -n ${ISTIO_NAMESPACE} -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null || echo "N/A")
KIALI_PORT=$(sudo kubectl get svc kiali -n ${ISTIO_NAMESPACE} -o jsonpath='{.spec.ports[?(@.port==20001)].nodePort}' 2>/dev/null || echo "N/A")

echo "🎯 Deployment Complete!"

# Get Istio Ingress Gateway NodePort
ISTIO_INGRESS_NAME=$(sudo kubectl get svc -n ${ISTIO_NAMESPACE} -o jsonpath='{.items[?(@.metadata.name=="istio-ingressgateway")].metadata.name}' 2>/dev/null || echo "")
if [ -z "$ISTIO_INGRESS_NAME" ]; then
    ISTIO_INGRESS_PORT="N/A"
else
    ISTIO_INGRESS_PORT=$(sudo kubectl get svc "$ISTIO_INGRESS_NAME" -n ${ISTIO_NAMESPACE} -o jsonpath='{.spec.ports[?(@.port==80)].nodePort}' 2>/dev/null || echo "N/A")
fi

# Change Local Port for Istio Ingress Gateway (Replace 80 → 8081)
LOCAL_ISTIO_PORT=8081

echo "-----"
echo "GRAFANA_URL=http://${NODE_IP}:${GRAFANA_PORT}"
echo "KIALI_URL=http://${NODE_IP}:${KIALI_PORT}"
echo "ISTIO_INGRESS_URL=http://${NODE_IP}:${LOCAL_ISTIO_PORT}"


sleep 60
source .venv/bin/activate
python3 tracer.py