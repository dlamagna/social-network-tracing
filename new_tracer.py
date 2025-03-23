import os
import json
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from prometheus_api_client import PrometheusConnect

def connect_to_prometheus():
    """
    Connect to the Prometheus server.
    """
    prom = PrometheusConnect(url="http://localhost:9090", disable_ssl=True)
    if prom.check_prometheus_connection():
        print("Connected to Prometheus.")
    else:
        raise Exception("Failed to connect to Prometheus.")
    return prom

def fetch_metrics(prom, query, start_time, end_time):
    """
    Fetch metrics from Prometheus using a query.
    :param prom: Prometheus connection object.
    :param query: PromQL query string.
    :param start_time: Start time for the query.
    :param end_time: End time for the query.
    """
    try:
        metrics_data = prom.custom_query_range(
            query=query,
            start_time=start_time,
            end_time=end_time,
            step='15s'
        )
        return metrics_data, "Success"
    except Exception as e:
        return None, f"Error fetching metrics: {e}"

def process_metrics(metrics, msg):
    """
    Process raw metrics data into a DataFrame.
    :param metrics: Raw metrics data from Prometheus.
    :param msg: Message indicating the status of the fetch.
    :return: Processed DataFrame.
    """
    if not metrics or len(metrics) == 0:
        print(f"No data returned: {msg}")
        return None

    df_list = []
    for metric in metrics:
        values = metric["values"]
        for value in values:
            df_list.append({
                "timestamp": datetime.fromtimestamp(float(value[0])),
                "value": float(value[1])
            })

    metrics_df = pd.DataFrame(df_list)
    return metrics_df

def save_wrk2_outputs():
    """
    Placeholder function for running wrk2 tests and saving results.
    Replace with actual implementation.
    """
    print("Running wrk2 tests and saving outputs...")

PROMETHEUS_QUERIES = {
    "http_request_success_rate": 'sum(rate(http_requests_total{status=~"2.."}[5m])) by (pod) / sum(rate(http_requests_total[5m])) by (pod) * 100',
    "cpu_usage_per_pod": 'sum(rate(container_cpu_usage_seconds_total[5m])) by (pod)',
    "memory_usage_per_pod": 'sum(container_memory_usage_bytes) by (pod)',
    "network_receive": 'sum(rate(container_network_receive_bytes_total[5m])) by (pod)',
    "network_transmit": 'sum(rate(container_network_transmit_bytes_total[5m])) by (pod)',
}

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

def get_jaeger_network_map(jaeger_url):
    """
    Fetches the network map from Jaeger.
    :param jaeger_url: URL of the Jaeger server.
    :return: Network map JSON.
    """
    response = requests.get(f"{jaeger_url}/api/dependencies?lookback=1h")
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch Jaeger network map: {response.status_code}, {response.text}")

def main():
    # Connect to Prometheus
    prom = connect_to_prometheus()

    # Collect Jaeger map
    jaeger_url = "http://localhost:16687"
    print(f"[{datetime.utcnow().isoformat()}] Getting network map from Jaeger...", flush=True)
    network_map = get_jaeger_network_map(jaeger_url)
    network_map_filename = "visualizations/network_map"
    with open(f"{network_map_filename}.json", "w") as f:
        json.dump(network_map, f, indent=4)
    print(f"Jaeger network map saved to {network_map_filename}.json", flush=True)

    # Extract services from Jaeger network map
    services = extract_services_from_network_map(network_map)
    print(f"Services extracted: {services}", flush=True)

    # Generate Prometheus queries dynamically
    service_queries = generate_prometheus_queries_for_services(services, PROMETHEUS_QUERIES)

    # Run wrk2 tests
    start_time = datetime.now() - timedelta(seconds=10)
    save_wrk2_outputs()
    end_time = datetime.now() + timedelta(seconds=10)

    # Fetch and visualize metrics dynamically
    save_metrics_and_visualizations(prom, service_queries, start_time, end_time)

# Main workflow
if __name__ == "__main__":
    main()
