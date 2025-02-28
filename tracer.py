from prometheus_api_client import PrometheusConnect
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import subprocess
import json
import os
from typing import Dict
import time

from utils import (
    verify_prometheus_connection, 
    get_current_utc_timestamp, 
    get_jaeger_network_map,
    visualize_network_map
)
from ssh_utils import manage_tunnels_with_port_forward
from keys import SSH_TUNNELS, SSH_USER, SSH_HOST

BEFORE_AFTER_QUERY_LAG = 20

# PREREQUISITES:
# 1. install wrk
# 2. have jaeger, prometheus, nginx port forward terminals open

wrk2_dir = "~/projects/DeathStarBench/wrk2/wrk2/"
wrk2_script = "~/projects/DeathStarBench/socialNetwork/wrk2/scripts/social-network/compose-post.lua"

nginx_url = "http://172.20.0.4:30221"
prometheus_url = f"http://172.20.0.4:31721"
jaeger_url = f"http://172.20.0.4:31354"

test_params = {
    "threads": 1,
    "connections": 10,
    "duration": "60s",
    "rate": 80,
    "url": f"{nginx_url}/wrk2-api/post/compose"
}

visualisation_output_dir = "visualizations"
metrics_output_dir = "data"

for output_dir in metrics_output_dir, visualisation_output_dir:
    os.makedirs(output_dir, exist_ok=True)

from prom_queries import PROMETHEUS_QUERIES

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
        # "-D exp",
        "-L",
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
    print(f"Serving fat http://{nginx_ip}:{port}",flush=True)
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
    return network_map

def save_wrk2_outputs():
    print(f"[{get_current_utc_timestamp()}] Running wrk2 test with {test_params}... ", end="",flush=True)
    wrk2_output = run_wrk2_test(test_params)

    with open(f"{visualisation_output_dir}/wrk2_output.json", "w") as f:
        json.dump(wrk2_output, f)
    print("Complete, output saved to ",f"{visualisation_output_dir}/wrk2_output.json",flush=True)
    return wrk2_output

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

def extract_services_from_network_map(network_map):
    """
    Extracts unique service names from the Jaeger network map.
    :param network_map: JSON object containing service dependency information.
    :return: A set of unique service names.
    """
    services = set()
    for dependency in network_map.get("data", []):
        services.add(dependency["parent"])
        services.add(dependency["child"])
    return services

def generate_prometheus_queries_for_services(services, base_queries):
    """
    Generates Prometheus queries for each service.
    :param services: Set of service names.
    :param base_queries: Dictionary of base Prometheus queries.
    :return: A dictionary where keys are service names and values are their queries.
    """
    service_queries = {}
    for service in services:
        service_queries[service] = {}
        for metric_name, base_query in base_queries.items():
            # Replace the placeholder "pod" with the actual service name
            service_queries[service][metric_name] = base_query.replace("pod=~", f'pod=~"{service}"')
    return service_queries

def save_metrics_and_visualizations(prom, service_queries, start_time, end_time):
    """
    Fetches metrics for each service and saves data and visualizations.
    :param prom: Prometheus connection object.
    :param service_queries: Dictionary of Prometheus queries per service.
    :param start_time: Start time for the metrics query.
    :param end_time: End time for the metrics query.
    """
    for service, queries in service_queries.items():
        # Create directories for data and visualizations
        data_dir = f"data/{service}"
        viz_dir = f"visualizations/{service}"
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(viz_dir, exist_ok=True)

        for metric_name, query in queries.items():
            print(f"Fetching metrics for service '{service}', metric '{metric_name}'...", flush=True)
            metrics, msg = fetch_metrics(prom, query, start_time, end_time)

            try:
                metrics_df = process_metrics(metrics, msg)
                if metrics_df is not None:
                    # Save data as CSV
                    csv_path = os.path.join(data_dir, f"{metric_name}.csv")
                    metrics_df.to_csv(csv_path, index=False)
                    print(f"Metrics data saved to {csv_path}", flush=True)

                    # Create visualization
                    plt.figure(figsize=(10, 6))
                    sns.lineplot(x="timestamp", y="value", data=metrics_df, label="Metric Value")
                    plt.title(f"{metric_name.replace('_', ' ').title()} - {service}")
                    plt.xlabel("Timestamp")
                    plt.ylabel("Value")
                    plt.grid(True)
                    plot_path = os.path.join(viz_dir, f"{metric_name}.png")
                    plt.savefig(plot_path)
                    plt.close()
                    print(f"Visualization saved to {plot_path}", flush=True)
                else:
                    print(f"No metrics found for service '{service}', metric '{metric_name}'.", flush=True)
            except Exception as e:
                print(f"Error processing metrics for service '{service}', metric '{metric_name}': {e}", flush=True)
            
            time.sleep(1)

def main():
    # Connect to Prometheus
    prom = connect_to_prometheus()
    
    # Run wrk2 tests 
    start_time = datetime.now() - timedelta(seconds=BEFORE_AFTER_QUERY_LAG)
    output_str = save_wrk2_outputs()
    end_time = datetime.now() + timedelta(seconds=BEFORE_AFTER_QUERY_LAG)
    print("Completed! \n", output_str[:326])
    print(f"Now waiting for {BEFORE_AFTER_QUERY_LAG}s to allow time for prometheus scraping..")
    time.sleep(BEFORE_AFTER_QUERY_LAG)
    # Collect Jaeger map
    network_dict = save_jaeger_network_map()
    # Extract services from Jaeger network map
    services = extract_services_from_network_map(network_dict)
    print(f"Services extracted: {services}", flush=True)
    
    service_queries = generate_prometheus_queries_for_services(services, PROMETHEUS_QUERIES)

    save_metrics_and_visualizations(prom, service_queries, start_time, end_time)


# Main workflow
if __name__ == "__main__":
    main()
    
