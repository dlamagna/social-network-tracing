import os
import csv
import json
import matplotlib.pyplot as plt

def load_network_map(network_map_path="visualizations/network_map.json"):
    """
    Loads a JSON file that contains a list of {parent, child, callCount}.
    Returns a dict that organizes child info under each parent:
    
    {
      "compose-post-service": [
        {"child": "media-service", "callCount": 1124},
        {"child": "post-storage-service", "callCount": 1124},
        ...
      ],
      "text-service": [
        {"child": "user-mention-service", "callCount": 1124},
        ...
      ],
      ...
    }
    """
    print(f"Loading network structure from {network_map_path} ...")

    with open(network_map_path, "r") as f:
        raw_map = json.load(f)
    
    # raw_map["data"] is assumed to be a list of {parent, child, callCount}
    parent_child_dict = {}

    for entry in raw_map["data"]:
        parent = entry["parent"]
        child = entry["child"]
        call_count = entry["callCount"]

        if parent not in parent_child_dict:
            parent_child_dict[parent] = []
        
        parent_child_dict[parent].append({
            "child": child,
            "callCount": call_count
        })

    return parent_child_dict


def load_all_service_metrics(data_path="data"):
    """
    Scans the given data_path for subdirectories (each representing a service),
    then reads all CSV files within each subdirectory.
    
    Returns a dictionary of the form:
    {
        "social-graph-service": {
            "cpu_consumption_compose": [
                {"timestamp": "2025-03-22 21:16:42", "value": 0.05360663539330211},
                {"timestamp": "2025-03-22 21:16:57", "value": 0.05360663539330211},
                ...
            ],
            "cpu_consumption_nginx": [...],
            ...
        },
        "text-service": {
            "cpu_consumption_text": [...],
            "cpu_consumption_user_mention": [...],
            ...
        },
        ...
    }
    """
    print(f"Loading data from {data_path} ...")
    services_data = {}

    # Loop over each service folder in data_path
    for service_dir in os.listdir(data_path):
        service_path = os.path.join(data_path, service_dir)
        
        # Only proceed if this is a directory (not a file)
        if os.path.isdir(service_path):
            metrics_dict = {}

            # Look for CSV files in this service directory
            for file_name in os.listdir(service_path):
                if file_name.endswith(".csv"):
                    metric_name = file_name.replace(".csv", "")
                    file_path = os.path.join(service_path, file_name)

                    # Read CSV data
                    data_points = []
                    with open(file_path, "r", newline="") as f:
                        reader = csv.DictReader(f)  # expects columns: timestamp, value
                        
                        for row in reader:
                            # Convert the "value" to float, keep timestamp as string
                            data_points.append({
                                "timestamp": row["timestamp"],
                                "value": float(row["value"])
                            })
                    
                    # Store the list of data points under this metric
                    metrics_dict[metric_name] = data_points

            # Store all metrics for this service
            services_data[service_dir] = metrics_dict

    return services_data


if __name__ == "__main__":
    # 1) Load all CSV metrics from each service
    services_data = load_all_service_metrics("data")

    # 2) Load the parent-child network map
    network_map = load_network_map("visualizations/network_map.json")

    # Create the "aggregate" folder if it doesn't exist
    if not os.path.exists("aggregate"):
        os.makedirs("aggregate")

    # 3) Save the entire services_data to a single JSON for reference
    aggregated_data_path = os.path.join("aggregate", "all_services_data.json")
    with open(aggregated_data_path, "w") as f:
        json.dump(services_data, f, indent=2)

    # 4) Save the network_map as well
    aggregated_network_map_path = os.path.join("aggregate", "network_map.json")
    with open(aggregated_network_map_path, "w") as f:
        json.dump(network_map, f, indent=2)

    # 5) For each service, save a separate JSON and create plots for each metric
    for service_dir, metrics_dict in services_data.items():
        # a) Save each service's data to a JSON file
        output_json_path = os.path.join("aggregate", f"{service_dir}.json")
        with open(output_json_path, "w") as f:
            json.dump(metrics_dict, f, indent=2)
        
        # b) Generate and save plots for each metric
        for metric_name, data_points in metrics_dict.items():
            if not data_points:
                continue

            timestamps = [dp["timestamp"] for dp in data_points]
            values = [dp["value"] for dp in data_points]

            plt.figure(figsize=(8, 4))
            plt.plot(timestamps, values, marker='o')
            plt.title(f"{service_dir} - {metric_name}")
            plt.xlabel("Timestamp")
            plt.ylabel("Value")
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()

            # Save plot to the aggregate folder
            output_plot_path = os.path.join("aggregate", f"{service_dir}_{metric_name}.png")
            plt.savefig(output_plot_path)
            plt.close()

    # 6) Example usage of the data
    print("\n--- Example Usage / Verification ---")
    for parent_service, children_info in network_map.items():
        if parent_service in services_data:
            # You can get the parent's metrics here
            parent_metrics = services_data[parent_service]
            # For example, CPU consumption data (if any)
            cpu_data = parent_metrics.get("cpu_consumption_compose", [])
            
            print(f"Parent service: {parent_service}")
            print(f"Children: {children_info}")
            print(f"CPU data sample: {cpu_data[:3]}")
        else:
            print(f"No metrics found for {parent_service}")
