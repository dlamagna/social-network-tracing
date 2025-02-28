#!/bin/bash

echo "🛠️ Starting full purge and reinstall of DeathStarBench, Prometheus, Grafana, and WRK2..."

# 0️⃣ Uninstall WRK2 (if exists)
echo "🧹 Uninstalling existing WRK2..."
cd ~/projects/DeathStarBench/wrk2/wrk2
make clean
echo "✅ WRK2 uninstalled."

# 1️⃣ Purge DeathStarBench (Social Network)
echo "🛠️ Purging DeathStarBench..."
if sudo helm list -n socialnetwork | grep -q "social-network"; then
    sudo helm uninstall social-network -n socialnetwork
else
    echo "⚠️ Helm release 'social-network' not found, skipping uninstall."
fi

sudo kubectl delete all --all -n socialnetwork --ignore-not-found
sudo kubectl delete pvc --all -n socialnetwork --ignore-not-found
sudo kubectl delete configmap --all -n socialnetwork --ignore-not-found
sudo kubectl delete secret --all -n socialnetwork --ignore-not-found
sudo kubectl delete namespace socialnetwork --ignore-not-found
sudo kubectl create namespace socialnetwork
echo "✅ DeathStarBench removed."

# 2️⃣ Purge Prometheus, Grafana, and nginx-prometheus-exporter
echo "🛠️ Purging Prometheus, Grafana, and monitoring tools..."
for release in prometheus grafana nginx-prometheus-exporter; do
    if sudo helm list -n monitoring | grep -q "$release"; then
        sudo helm uninstall "$release" -n monitoring
    else
        echo "⚠️ Helm release '$release' not found, skipping uninstall."
    fi
done

sudo kubectl delete all --all -n monitoring --ignore-not-found
sudo kubectl delete pvc --all -n monitoring --ignore-not-found
sudo kubectl delete namespace monitoring --ignore-not-found
sudo kubectl create namespace monitoring
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



# 5️⃣ Deploy DeathStarBench using Helm
echo "📦 Deploying Social Network using Helm..."
cd ~/projects/DeathStarBench/socialNetwork
sudo helm install social-network ./helm-chart/socialnetwork -n socialnetwork
echo "✅ DeathStarBench reinstalled."

# 6️⃣ Deploy Prometheus for Monitoring (as NodePort)
echo "📊 Deploying Prometheus as NodePort..."
sudo helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
sudo helm repo update
sudo helm install prometheus prometheus-community/prometheus -n monitoring --set server.service.type=NodePort
echo "✅ Prometheus deployed."

# 7️⃣ Deploy Grafana for Visualization
echo "📈 Deploying Grafana..."
sudo helm repo add grafana https://grafana.github.io/helm-charts
sudo helm repo update
echo "📈 Deploying Grafana with NodePort and Persistence..."
sudo helm install grafana grafana/grafana -n monitoring \
  --set adminPassword=admin \
  --set service.type=NodePort \
  --set persistence.enabled=true \
  --set persistence.size=10Gi
echo "✅ Grafana deployed with NodePort and persistence."

# 8️⃣ Deploy nginx-prometheus-exporter for Additional Metrics
echo "📡 Deploying nginx-prometheus-exporter..."
sudo helm install nginx-prometheus-exporter prometheus-community/prometheus-nginx-exporter -n monitoring
echo "✅ nginx-prometheus-exporter deployed."

# 9️⃣ Expose Jaeger as NodePort
echo "🌐 Exposing Jaeger as NodePort..."
sudo kubectl patch svc jaeger -n socialnetwork -p '{"spec": {"type": "NodePort"}}'
echo "✅ Jaeger exposed as NodePort."

# 🔟 Expose Nginx as NodePort
echo "🌐 Exposing Nginx as NodePort..."
sudo kubectl patch svc nginx-thrift -n socialnetwork -p '{"spec": {"type": "NodePort"}}'
echo "✅ Nginx exposed as NodePort."

# 1️⃣1️⃣ Wait for Pods to Be Ready
echo "⏳ Waiting for pods to become ready..."
sleep 60

# 1️⃣2️⃣ Restart Any Stuck Pods
echo "🔍 Checking for pods stuck in 'Init' state..."
stuck_pods=$(sudo kubectl get pods -n socialnetwork | grep 'Init' | awk '{print $1}')
if [ -n "$stuck_pods" ]; then
    echo "⚠️ Restarting stuck pods..."
    for pod in $stuck_pods; do
        sudo kubectl delete pod "$pod" -n socialnetwork
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

# 1️⃣5️⃣ Get Node IPs and NodePorts for Nginx, Prometheus, and Jaeger
echo "🌐 Fetching Node IPs and NodePorts..."
node_ip=$(sudo kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
nginx_port=$(sudo kubectl get svc nginx-thrift -n socialnetwork -o jsonpath='{.spec.ports[0].nodePort}')
prometheus_port=$(sudo kubectl get svc prometheus-server -n monitoring -o jsonpath='{.spec.ports[0].nodePort}')
jaeger_port=$(sudo kubectl get svc jaeger -n socialnetwork -o jsonpath='{.spec.ports[?(@.port==16686)].nodePort}')
grafana_port=$(sudo kubectl get svc grafana -n monitoring -o jsonpath='{.spec.ports[0].nodePort}')

echo "✅ Node IPs and Ports:"
echo "➡️ Nginx: http://${node_ip}:${nginx_port}"
echo "➡️ Prometheus: http://${node_ip}:${prometheus_port}"
echo "➡️ Jaeger: http://${node_ip}:${jaeger_port}"
echo "➡️ Grafana: http://${node_ip}:${grafana_port} (admin/admin)"

echo "🎯 Deployment Complete!"
