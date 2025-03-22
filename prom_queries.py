## original: -----------
# PROMETHEUS_QUERIES = {
#     # HTTP Request Success Rate per Pod (percentage of successful requests)
#     "http_request_success_rate": 'sum(rate(http_requests_total{status!~"5.."}[5m])) by (pod) / sum(rate(http_requests_total[5m])) by (pod) * 100',
    
#     # Total HTTP Requests per Pod (number of requests per second)
#     "total_http_requests": 'sum(rate(http_requests_total[5m])) by (pod)',
    
#     # HTTP 2xx Success Rate per Pod (percentage of successful responses)
#     "http_2xx_success_rate": 'sum(rate(http_requests_total{status=~"2.."}[5m])) by (pod) / sum(rate(http_requests_total[5m])) by (pod) * 100',
    
#     # HTTP 4xx Client Errors Rate per Pod (percentage of client-side errors)
#     "http_4xx_error_rate": 'sum(rate(http_requests_total{status=~"4.."}[5m])) by (pod) / sum(rate(http_requests_total[5m])) by (pod) * 100',
    
#     # HTTP 5xx Server Errors Rate per Pod (percentage of server-side errors)
#     "http_5xx_error_rate": 'sum(rate(http_requests_total{status=~"5.."}[5m])) by (pod) / sum(rate(http_requests_total[5m])) by (pod) * 100',
    
#     # 95th Percentile HTTP Request Latency per Pod (high latency indicator)
#     "http_request_latency_95th": 'histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, pod))',
    
#     # CPU Usage per Pod (CPU cores used by each pod)
#     "cpu_usage_per_pod": 'sum(rate(container_cpu_usage_seconds_total[5m])) by (pod)',
    
#     # Memory Usage per Pod (Memory in bytes used by each pod)
#     "memory_usage_per_pod": 'sum(container_memory_usage_bytes) by (pod)',
    
#     # Network Traffic Received per Pod (Bytes received)
#     "network_receive": 'sum(rate(container_network_receive_bytes_total[5m])) by (pod)',
    
#     # Network Traffic Transmitted per Pod (Bytes sent)
#     "network_transmit": 'sum(rate(container_network_transmit_bytes_total[5m])) by (pod)',
    
#     # CPU Consumption by Service
#     "cpu_consumption_compose": 'sum by (service) (rate(container_cpu_usage_seconds_total{namespace="socialnetwork", container=~"compose.*"}[2m]))',
#     "cpu_consumption_nginx": 'sum by (service) (rate(container_cpu_usage_seconds_total{namespace="socialnetwork", container=~"nginx.*"}[2m]))',
#     "cpu_consumption_text": 'sum by (service) (rate(container_cpu_usage_seconds_total{namespace="socialnetwork", container=~"text.*"}[2m]))',
#     "cpu_consumption_user_mention": 'sum by (service) (rate(container_cpu_usage_seconds_total{namespace="socialnetwork", container=~"user-mention.*"}[2m]))',
    
#     # CPU Utilization per Service
#     "cpu_utilization_compose": 'sum(rate(container_cpu_usage_seconds_total{namespace="socialnetwork", container=~"compose.*"}[2m])) / sum(kube_pod_container_resource_limits{resource="cpu", namespace="socialnetwork", container=~"compose.*", service="kube-state-metrics"}) * 100',
#     "cpu_utilization_nginx": 'sum(rate(container_cpu_usage_seconds_total{namespace="socialnetwork", container=~"nginx.*"}[2m])) / sum(kube_pod_container_resource_limits{resource="cpu", namespace="socialnetwork", container=~"nginx.*", service="kube-state-metrics"}) * 100',
#     "cpu_utilization_text": 'sum(rate(container_cpu_usage_seconds_total{namespace="socialnetwork", container=~"text-service.*"}[2m])) / sum(kube_pod_container_resource_limits{resource="cpu", namespace="socialnetwork", container=~"text-service.*", service="kube-state-metrics"}) * 100',
#     "cpu_utilization_user_mention": 'sum(rate(container_cpu_usage_seconds_total{namespace="socialnetwork", container=~"user-mention.*"}[2m])) / sum(kube_pod_container_resource_limits{resource="cpu", namespace="socialnetwork", container=~"user-mention.*", service="kube-state-metrics"}) * 100',
    
#     # Replicas per Service
#     "replicas_compose": 'count by (app) (kube_pod_info{pod=~"compose.*", app_kubernetes_io_instance="kube-state-metrics"})',
#     "replicas_nginx": 'count by (app) (kube_pod_info{pod=~"nginx.*", app_kubernetes_io_instance="kube-state-metrics"})',
#     "replicas_text": 'count by (app) (kube_pod_info{pod=~"text-service.*", app_kubernetes_io_instance="kube-state-metrics"})',
#     "replicas_user_mention": 'count by (app) (kube_pod_info{pod=~"user-mention.*", app_kubernetes_io_instance="kube-state-metrics"})'
# }

# # nginxplus_upstream_server_response_time
# # nginxplus_upstream_server_header_time

# -----------

def build_query(service_name):
    return f'count(kube_pod_info{{pod=~"{service_name}.*", namespace="socialnetwork"}})'

PROMETHEUS_QUERIES = {
    # HTTP Request Success Rate per Pod
    "http_request_success_rate": r'sum(rate(http_requests_total{status!~"5.."}[5m])) by (pod) / sum(rate(http_requests_total[5m])) by (pod) * 100',

    # Total HTTP Requests per Pod
    "total_http_requests": r'sum(rate(http_requests_total[5m])) by (pod)',

    # HTTP 2xx Success Rate per Pod
    "http_2xx_success_rate": r'sum(rate(http_requests_total{status=~"2.."}[5m])) by (pod) / sum(rate(http_requests_total[5m])) by (pod) * 100',

    # HTTP 4xx Client Errors Rate per Pod
    "http_4xx_error_rate": r'sum(rate(http_requests_total{status=~"4.."}[5m])) by (pod) / sum(rate(http_requests_total[5m])) by (pod) * 100',

    # HTTP 5xx Server Errors Rate per Pod
    "http_5xx_error_rate": r'sum(rate(http_requests_total{status=~"5.."}[5m])) by (pod) / sum(rate(http_requests_total[5m])) by (pod) * 100',

    # 95th Percentile HTTP Request Latency per Pod
    "http_request_latency_95th": r'histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, pod))',

    # CPU Usage per Pod
    "cpu_usage_per_pod": r'sum(rate(container_cpu_usage_seconds_total[5m])) by (pod)',

    # Memory Usage per Pod
    "memory_usage_per_pod": 'avg_over_time(container_memory_usage_bytes[5m]) by (pod)',

    # Network Traffic Received per Pod
    "network_receive": r'sum(rate(container_network_receive_bytes_total[5m])) by (pod)',

    # Network Traffic Transmitted per Pod
    "network_transmit": r'sum(rate(container_network_transmit_bytes_total[5m])) by (pod)',

    # CPU Consumption by Service
    "cpu_consumption_compose": r'sum by (service) (rate(container_cpu_usage_seconds_total{namespace="socialnetwork", container=~"compose.*"}[2m]))',
    "cpu_consumption_nginx": r'sum by (service) (rate(container_cpu_usage_seconds_total{namespace="socialnetwork", container=~"nginx.*"}[2m]))',
    "cpu_consumption_text": r'sum by (service) (rate(container_cpu_usage_seconds_total{namespace="socialnetwork", container=~"text.*"}[2m]))',
    "cpu_consumption_user_mention": r'sum by (service) (rate(container_cpu_usage_seconds_total{namespace="socialnetwork", container=~"user-mention.*"}[2m]))',

    # CPU Utilization per Service (using Requests instead of Limits)
    "cpu_utilization_compose": r'sum(rate(container_cpu_usage_seconds_total{namespace="socialnetwork", container=~"compose.*"}[2m])) / sum(kube_pod_container_resource_requests{resource="cpu", namespace="socialnetwork", container=~"compose.*"}) * 100',
    "cpu_utilization_nginx": r'sum(rate(container_cpu_usage_seconds_total{namespace="socialnetwork", container=~"nginx.*"}[2m])) / sum(kube_pod_container_resource_requests{resource="cpu", namespace="socialnetwork", container=~"nginx.*"}) * 100',
    "cpu_utilization_text": r'sum(rate(container_cpu_usage_seconds_total{namespace="socialnetwork", container=~"text-service.*"}[2m])) / sum(kube_pod_container_resource_requests{resource="cpu", namespace="socialnetwork", container=~"text-service.*"}) * 100',
    "cpu_utilization_user_mention": r'sum(rate(container_cpu_usage_seconds_total{namespace="socialnetwork", container=~"user-mention.*"}[2m])) / sum(kube_pod_container_resource_requests{resource="cpu", namespace="socialnetwork", container=~"user-mention.*"}) * 100',

    # Replicas per Service
    "replicas_compose": build_query("compose"),
    "replicas_nginx": build_query("nginx"),
    "replicas_text": build_query("text-service"),
    "replicas_user_mention": build_query("user-mention")
}
