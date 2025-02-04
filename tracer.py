from prometheus_api_client import PrometheusConnect
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import subprocess
import json
import os
from typing import Dict

from utils import (
    verify_prometheus_connection, 
    get_current_utc_timestamp, 
    get_jaeger_network_map,
    visualize_network_map
)
from ssh_utils import manage_tunnels_with_port_forward
from keys import SSH_TUNNELS, SSH_USER, SSH_HOST

wrk2_dir = "../../wrk2/"
wrk2_script = "../wrk2/scripts/social-network/compose-post.lua"
prometheus_url = "http://localhost:9091"
nginx_url = "http://localhost:8082"
jaeger_url = "http://localhost:16687"

test_params = {
    "threads": 4,
    "connections": 100,
    "duration": "60s",
    "rate": 2000,
    "url": f"{nginx_url}/wrk2/test"
}

visualisation_output_dir = "visualizations"
metrics_output_dir = "data"

for output_dir in metrics_output_dir, visualisation_output_dir:
    os.makedirs(output_dir, exist_ok=True)


# <prometheus-url> : localhost:9090
# <social-network-endpoint> : localhost:8082




# Define Prometheus queries
from prom_queries import PROMETHEUS_QUERIES



# queries = {
#     "network_receive": "rate(node_network_receive_bytes_total[1m])",
#     "network_transmit": "rate(node_network_transmit_bytes_total[1m])"
# }

# Fetch metrics
def fetch_metrics(prom:PrometheusConnect, query, start_time, end_time):
    result = prom.custom_query_range(
        query=query,
        start_time=start_time,
        end_time=end_time,
        step="15s"
    )
    msg = f"Query: {query}, Start: {start_time}, End: {end_time}"

    return result, msg

# Process data
def process_metrics(result, msg):
    if not result:
        print(msg, end="", flush=True)
        return
        # print(/)
        # raise ValueError("No data returned from Prometheus query.")
    
    data = []
    for metric in result:
        values = metric["values"]
        for timestamp, value in values:
            data.append({"timestamp": datetime.fromtimestamp(float(timestamp)), "value": float(value)})
    if data:
        return pd.DataFrame(data)
    else:
        raise ValueError("Metrics data is empty after processing.")



# Visualize metrics with advanced features
def plot_metrics(metrics_df, title, output_file=None):
    if "timestamp" not in metrics_df or "value" not in metrics_df:
        raise KeyError("Expected columns 'timestamp' and 'value' not found in the DataFrame.")
    
    sns.set(style="whitegrid")
    plt.figure(figsize=(12, 8))
    sns.lineplot(x="timestamp", y="value", data=metrics_df, label="Metric Value")
    plt.title(title, fontsize=16)
    plt.xlabel("Timestamp", fontsize=14)
    plt.ylabel("Value", fontsize=14)
    plt.legend()
    plt.xticks(rotation=45)
    
    if output_file:
        plt.savefig(output_file)
        print(f"Plot saved to {output_file}",flush=True)
    plt.show()

# Run a test with wrk2
def run_wrk2_test(test_params):
    command_list = [
        f"{wrk2_dir}/wrk",
        f"-t {test_params['threads']}",
        f"-c {test_params['connections']}",
        f"-d {test_params['duration']}",
        f"-R {test_params['rate']}",
        f"-s {wrk2_script}",
        f"{test_params['url']}",
    ]
    command = " ".join(command_list).strip()
    process = subprocess.run(command, shell=True, capture_output=True, text=True)
    if process.returncode != 0:
        raise RuntimeError(f"wrk2 test failed: {process.stderr}")
    return process.stdout

# Serve visualizations for remote access
def serve_visualizations(visualisation_output_dir, port=8082):
    import http.server
    import socketserver

    os.chdir(visualisation_output_dir)
    handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", port), handler)
    print(f"Serving at http://localhost:{port}",flush=True)
    httpd.serve_forever()

def connect_to_prometheus():
    print(f"[{get_current_utc_timestamp()}] Connecting to prometheus ... ", end="",flush=True)
    prom = PrometheusConnect(url=prometheus_url, disable_ssl=True)
    print("Connected" if verify_prometheus_connection(prom) else "Failed",flush=True)
    return prom

def save_jaeger_network_map():
    print(f"[{get_current_utc_timestamp()}] Getting network map from Jaeger...", end="")
    network_map = get_jaeger_network_map(jaeger_url)
    network_map_filename = f"{visualisation_output_dir}/network_map"
    with open(f"{network_map_filename}.json", "w") as f:
        json.dump(network_map, f, indent=4)
    visualize_network_map(network_map, f"{network_map_filename}.png")

def save_wrk2_outputs():
    print(f"[{get_current_utc_timestamp()}] Running wrk2 test with {test_params}... ", end="",flush=True)
    wrk2_output = run_wrk2_test(test_params)

    with open(f"{visualisation_output_dir}/wrk2_output.json", "w") as f:
        json.dump(wrk2_output, f)
    print("Complete, output saved to ",f"{visualisation_output_dir}/wrk2_output.json",flush=True)

def run_prom_requests(prom, prom_queries:Dict[str, str], start_time, end_time):
    # Fetch and process metrics for all queries
    for metric_name, query in prom_queries.items():
        print(f"Fetching metrics for {metric_name}...", flush=True)
        
        # Fetch metrics for the current query
        metrics, msg = fetch_metrics(prom, query, start_time, end_time)
        metrics_df = process_metrics(metrics, msg)
        if metrics_df is None:
            print("... No metrics found :(", flush=True)
            continue
        else:
            df_output_path = os.path.join(metrics_output_dir, f"{metric_name}.csv")
            metrics_df.to_csv(df_output_path)

        
        # Create visualization for each metric
        print(f"{get_current_utc_timestamp()} Creating visualizations for {metric_name}...", flush=True)
        plot_file = f"{visualisation_output_dir}/{metric_name}.png"  # Save each visualization with metric name
        plot_metrics(metrics_df, metric_name.replace('_', ' ').title(), output_file=plot_file)
        
        print(f"Visualization saved to {plot_file}.", flush=True)

def main():
    # Connect to Prometheus
    prom = connect_to_prometheus()
    
    # Collect Jaeger map
    save_jaeger_network_map()
   
    # Run wrk2 tests 
    start_time = datetime.now() - timedelta(seconds=10)
    save_wrk2_outputs()
    end_time = datetime.now() + timedelta(seconds=10)

    run_prom_requests(prom, PROMETHEUS_QUERIES, start_time, end_time)


# Main workflow
if __name__ == "__main__":
    main()
    
