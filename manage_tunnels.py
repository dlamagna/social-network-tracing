import subprocess
import os
import time

# Global variables for SSH configuration
SSH_HOST = "147.83.130.183"
SSH_USER = "dlamagna"

from keys import SSH_TUNNELS

import subprocess
import os
import time

SSH_HOST = "147.83.130.183"
SSH_USER = "dlamagna"

SSH_TUNNELS = [
    {
        "local_port": 16687,
        "remote_host": "localhost",
        "remote_port": 16686,
        "server_port": 22,
        "k8s_port_forward": {
            "resource_name": "jaeger",
            "resource_type": "service",
            "namespace": "socialnetwork",
        },
    },
    {
        "local_port": 8082,
        "remote_host": "localhost",
        "remote_port": 8080,
        "server_port": 22,
        "k8s_port_forward": {
            "resource_name": "nginx-thrift",
            "resource_type": "service",
            "namespace": "socialnetwork",
        },
    },
    {
        "local_port": 9091,
        "remote_host": "localhost",
        "remote_port": 9090,
        "server_port": 22,
        "k8s_port_forward": {
            "resource_name": "prometheus",
            "resource_type": "service",
            "namespace": "monitoring",
        },
    },
]

def is_port_free(port):
    """
    Checks if a port is free to use.
    :param port: The port to check.
    :return: True if the port is free, False otherwise.
    """
    result = subprocess.run(
        ["lsof", "-i", f"tcp:{port}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return not result.stdout  # Port is free if no output

def wait_for_port_release(port, timeout=10):
    """
    Waits for a port to be released.
    :param port: Port number to check.
    :param timeout: Maximum time to wait for the port to be released.
    """
    start_time = time.time()
    while not is_port_free(port):
        if time.time() - start_time > timeout:
            raise TimeoutError(f"Port {port} did not become free within {timeout} seconds.")
        time.sleep(1)
    print(f"Port {port} is now free.")

def kill_process_on_port(port):
    """
    Kills the process using a specific port.
    :param port: Port number to free.
    """
    try:
        result = subprocess.run(
            ["lsof", "-ti", f"tcp:{port}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.stdout:
            pid = result.stdout.strip()
            print(f"Killing process {pid} using port {port}...")
            os.kill(int(pid), 9)
            wait_for_port_release(port)
        else:
            print(f"Port {port} is not in use.")
    except Exception as e:
        print(f"Failed to kill process on port {port}: {e}")

def manage_tunnels_with_port_forward(tunnels, ssh_user, ssh_host):
    """
    Manages SSH tunnels and Kubernetes port-forwarding.
    """
    for tunnel in tunnels:
        local_port = tunnel["local_port"]
        kill_process_on_port(local_port)

    for tunnel in tunnels:
        local_port = tunnel["local_port"]
        remote_host = tunnel["remote_host"]
        remote_port = tunnel["remote_port"]
        server_port = tunnel["server_port"]
        k8s_port_forward = tunnel.get("k8s_port_forward")
        
        # Open SSH tunnel
        if not is_port_free(local_port):
            print(f"Port {local_port} is still in use. Skipping SSH tunnel setup.")
            continue

        try:
            command = [
                "ssh",
                "-p", f"{server_port}",
                "-L", f"{local_port}:{remote_host}:{remote_port}",
                f"{ssh_user}@{ssh_host}",
                "-f",  # Run SSH in the background
                "tmux", "new-session", "-d", f"echo Tunnel established on {local_port}"  # Simple tmux command
            ]
            print(f"Opening SSH tunnel: {local_port} -> {remote_host}:{remote_port}")
            subprocess.run(command, check=True)
            print(f"SSH tunnel opened successfully on port {local_port}.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to open SSH tunnel on port {local_port}: {e}")
            continue

        # Handle Kubernetes port-forwarding
        if k8s_port_forward:
            if not is_port_free(local_port):
                print(f"Port {local_port} is still in use. Skipping Kubernetes port-forward.")
                continue

            resource_name = k8s_port_forward["resource_name"]
            resource_type = k8s_port_forward.get("resource_type", "service")
            namespace = k8s_port_forward.get("namespace", "default")
            k8s_command = [
                "sudo", "kubectl", "port-forward",
                f"{resource_type}/{resource_name}",
                f"{local_port}:{remote_port}",
                "-n", namespace
            ]

            print(f"Setting up Kubernetes port-forward: {local_port} -> {resource_name}:{remote_port}")
            try:
                success = run_k8s_port_forward(k8s_command, check_port=local_port)
                if not success:
                    print(f"Failed to set up port-forward for {resource_name}.")
            except TimeoutError as e:
                print(f"Timeout while setting up Kubernetes port-forward for {resource_name}: {e}")

def run_k8s_port_forward(k8s_command, check_port=None):
    """
    Runs a kubectl port-forward command in the background and verifies success.
    """
    try:
        # Start the subprocess
        print(f"Executing: {' '.join(k8s_command)}")
        process = subprocess.Popen(
            k8s_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        # Wait briefly to allow the process to initialize
        time.sleep(2)

        # Check if the port is active
        if check_port:
            wait_for_port_release(check_port)

        print("Port-forward command executed successfully.")
        return True

    except Exception as e:
        print(f"Error running port-forward: {e}")
        return False

if __name__ == "__main__":
    # Manage tunnels and port-forwards
    manage_tunnels_with_port_forward(SSH_TUNNELS, SSH_USER, SSH_HOST)
