SSH_HOST = "147.83.130.183"
SSH_USER = "dlamagna"

SSH_TUNNELS = [
    {
        "local_port": 16687,
        "remote_host": "localhost",
        "remote_port": 16686,
        "server_port": 13000,
        "k8s_port_forward": {
            "resource_name": "jaeger",
            "resource_type": "service",
            "namespace": "socialnetwork"
        }
    },
    {
        "local_port": 8082,
        "remote_host": "localhost",
        "remote_port": 8080,
        "server_port": 13000,
        "k8s_port_forward": {
            "resource_name": "nginx-thrift",
            "resource_type": "service",
            "namespace": "socialnetwork"
        }
    },
    {
        "local_port": 9091,
        "remote_host": "localhost",
        "remote_port": 9090,
        "server_port": 13000,
        "k8s_port_forward": {
            "resource_name": "prometheus",
            "resource_type": "service",
            "namespace": "monitoring"
        }
    }
]