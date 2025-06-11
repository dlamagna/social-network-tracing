#!/bin/bash

echo "🛠️ Starting full purge and reinstall of DeathStarBench, Istio, Prometheus, Grafana, and WRK2..."

# Set namespaces
DEATHSTAR_NAMESPACE="socialnetwork"
MONITORING_NAMESPACE="istio-system"  # Change to istio-system for easier integration
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
sudo kubectl delete configmap --all -n $DEATHSTAR_NAMESPACE --ignore-not-found
sudo kubectl delete secret --all -n $DEATHSTAR_NAMESPACE --ignore-not-found
sudo kubectl delete namespace $DEATHSTAR_NAMESPACE --ignore-not-found
sudo kubectl create namespace $DEATHSTAR_NAMESPACE
echo "✅ DeathStarBench removed."

# 2️⃣ Purge Monitoring Tools (Prometheus, Grafana, nginx-exporter)
echo "🛠️ Purging Prometheus, Grafana, and monitoring tools..."
for release in prometheus grafana nginx-prometheus-exporter; do
    if sudo helm list -n $MONITORING_NAMESPACE | grep -q "$release"; then
        sudo helm uninstall "$release" -n $MONITORING_NAMESPACE
    else
        echo "⚠️ Helm release '$release' not found, skipping uninstall."
    fi
done

sudo kubectl delete all --all -n $MONITORING_NAMESPACE --ignore-not-found
sudo kubectl delete pvc --all -n $MONITORING_NAMESPACE --ignore-not-found
sudo kubectl delete namespace $MONITORING_NAMESPACE --ignore-not-found
sudo kubectl create namespace $MONITORING_NAMESPACE
echo "✅ Monitoring tools removed."

# 3️⃣ Clone or Update DeathStarBench
if [ ! -d ~/projects/DeathStarBench/.git ]; then
    echo "🚀 Cloning DeathStarBench repository..."
    git clone https://github.com/delimitrou/DeathStarBench.git ~/projects/DeathStarBench
else
    echo "🔄 Updating existing DeathStarBench repository..."
    cd ~/projects/DeathStarBench
    git checkout main && git pull
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
echo "🚀 Installing Istio (1.17)..."
curl -L https://istio.io/downloadIstio | ISTIO_VERSION=1.17 sh -
cd istio-1.17.*/bin
export PATH=$PWD:$PATH
cd ..

# Install Istio with demo profile (includes telemetry and tracing)
sudo istioctl install --set profile=demo -y --set values.global.proxy.accessLogFile="/dev/stdout"

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

sudo helm install prometheus prometheus-community/prometheus -n $MONITORING_NAMESPACE --set server.service.type=NodePort
sudo helm install grafana grafana/grafana -n $MONITORING_NAMESPACE \
  --set adminPassword=admin \
  --set service.type=NodePort \
  --set persistence.enabled=true \
  --set persistence.size=10Gi
echo "✅ Monitoring stack deployed."

# 8️⃣ Deploy nginx-prometheus-exporter
echo "📡 Deploying nginx-prometheus-exporter..."
sudo helm install nginx-prometheus-exporter prometheus-community/prometheus-nginx-exporter -n $MONITORING_NAMESPACE
echo "✅ nginx-prometheus-exporter deployed."

# 9️⃣ Deploy Kiali, Jaeger, and enable telemetry
sudo kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.17/samples/addons/kiali.yaml -n $ISTIO_NAMESPACE
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
for svc in jaeger kiali prometheus grafana istio-ingressgateway; do
  sudo kubectl patch svc $svc -n $ISTIO_NAMESPACE -p '{"spec": {"type": "NodePort"}}'
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

# 1️⃣4️⃣ Navigate Back to Social Network Directory
cd ~/projects/DeathStarBench/socialNetwork
echo "✅ Returned to Social Network directory."

# 1️⃣5️⃣ Get Node IPs and NodePorts
echo "🌐 Fetching Node IPs and NodePorts..."
node_ip=$(sudo kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
nginx_port=$(sudo kubectl get svc nginx-thrift -n $DEATHSTAR_NAMESPACE -o jsonpath='{.spec.ports[0].nodePort}')
prometheus_port=$(sudo kubectl get svc prometheus-server -n $MONITORING_NAMESPACE -o jsonpath='{.spec.ports[0].nodePort}')
jaeger_port=$(sudo kubectl get svc jaeger -n $ISTIO_NAMESPACE -o jsonpath='{.spec.ports[?(@.port==16686)].nodePort}')
grafana_port=$(sudo kubectl get svc grafana -n $MONITORING_NAMESPACE -o jsonpath='{.spec.ports[0].nodePort}')

echo "✅ Node IPs and Ports:"
echo "➡️ Nginx: http://${node_ip}:${nginx_port}"
echo "➡️ Prometheus: http://${node_ip}:${prometheus_port}"
echo "➡️ Jaeger: http://${node_ip}:${jaeger_port}"
echo "➡️ Grafana: http://${node_ip}:${grafana_port} (admin/admin)"

echo "🎯 Deployment Complete!"
