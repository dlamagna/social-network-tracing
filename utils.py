from prometheus_api_client import PrometheusConnect
from datetime import datetime
import requests
import json
import networkx as nx
import matplotlib.pyplot as plt

def visualize_network_map(network_map, save_path=None):
    G = nx.DiGraph()
    if "dependencies" in network_map.keys():
        for dependency in network_map["dependencies"]:
            parent = dependency["parent"]
            child = dependency["child"]
            call_count = dependency.get("callCount", 0)
            G.add_edge(parent, child, weight=call_count)
    elif "data" in network_map.keys():
        for dependency in network_map["data"]:
            parent = dependency["parent"]
            child = dependency["child"]
            call_count = dependency.get("callCount", 0)
            G.add_edge(parent, child, weight=call_count)

    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_size=3000, node_color="lightblue", font_size=10, font_weight="bold")
    plt.title("Service Network Map")
    if save_path is not None:
        plt.savefig(save_path)
        print("Network map saved to ", save_path)
    else:
        plt.show()

def query_pod_metrics(prom: PrometheusConnect, namespace="socialnetwork", msg=False):
    """
    Queries pod-level metrics from Prometheus.

    :param prometheus_url: The base URL of the Prometheus server.
    :param namespace: The Kubernetes namespace to query. Defaults to "default".
    :return: A dictionary of metrics for CPU, memory, and network I/O.
    """
    queries = {
        "cpu_usage": f'rate(container_cpu_usage_seconds_total{{namespace="{namespace}"}}[1m])',
        "memory_usage": f'container_memory_usage_bytes{{namespace="{namespace}"}}',
        "network_receive": f'rate(container_network_receive_bytes_total{{namespace="{namespace}"}}[1m])',
        "network_transmit": f'rate(container_network_transmit_bytes_total{{namespace="{namespace}"}}[1m])'
    }

    metrics = {}
    for metric_name, query in queries.items():
        result = prom.custom_query(query=query)
        metrics[metric_name] = result
        if msg:
            print(f"{metric_name}: {result}")

    return metrics

def get_jaeger_network_map(jaeger_url, end_time=None, lookback="1h", msg=False):
    """
    Fetches the network map (dependencies) from Jaeger.

    :param jaeger_url: The base URL of the Jaeger server (e.g., http://localhost:16686).
    :param end_time: Optional end time for the query in milliseconds since epoch.
    :param lookback: Lookback period in a human-readable format (e.g., "1h", "30m").
    :return: A dictionary of dependencies between services.
    """
    # Convert `lookback` into milliseconds
    try:
        if lookback.endswith("h"):
            lookback_ms = int(lookback[:-1]) * 60 * 60 * 1000  # Hours to milliseconds
        elif lookback.endswith("m"):
            lookback_ms = int(lookback[:-1]) * 60 * 1000  # Minutes to milliseconds
        elif lookback.endswith("s"):
            lookback_ms = int(lookback[:-1]) * 1000  # Seconds to milliseconds
        else:
            raise ValueError("Invalid lookback format. Use 'Xs', 'Xm', or 'Xh' (e.g., '30m').")
    except ValueError as ve:
        raise ValueError(f"Error parsing lookback value: {ve}")

    # Calculate `endTs` and `startTs`
    end_time_ms = end_time or int(datetime.utcnow().timestamp() * 1000)
    start_time_ms = end_time_ms - lookback_ms

    # Jaeger dependencies API URL
    dependencies_url = f"{jaeger_url}/api/dependencies"

    # Query parameters
    params = {
        "endTs": end_time_ms,
        "startTs": start_time_ms
    }

    # Perform the HTTP GET request
    response = requests.get(dependencies_url, params=params)
    if response.status_code == 200:
        dependencies = response.json()
        if msg:
            print("Jaeger Network Map:", json.dumps(dependencies, indent=2))
        return dependencies
    else:
        raise Exception(f"Failed to fetch Jaeger network map: {response.status_code}, {response.text}")


def get_current_utc_timestamp():
    """
    Returns the current timestamp in UTC format.

    :return: A string representation of the current UTC timestamp in ISO 8601 format.
    """
    return datetime.utcnow().isoformat() + "Z"

def verify_prometheus_connection(prom: PrometheusConnect, msg=False):
    try:
        # Initialize PrometheusConnect
        # prom = PrometheusConnect(url=prometheus_url, disable_ssl=True)
        
        # Fetch active targets to verify connection
        response = prom.custom_query(query="up")
        
        if response:  # If targets are fetched, connection is successful
            if msg:
                print("Successfully connected to Prometheus.")
            return True
        else:
            if msg:
                print("No targets found, but the connection to Prometheus is established.")
            return True
    except Exception as e:
        if msg:
            print(f"Failed to connect to Prometheus: {e}")
        return False