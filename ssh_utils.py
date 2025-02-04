import subprocess
import os

# Global variables for SSH configuration
SSH_HOST = "147.83.130.183"
SSH_USER = "dlamagna"

from keys import SSH_TUNNELS


import subprocess
import time

def run_k8s_port_forward(k8s_command, check_port=None):
    """
    Runs a kubectl port-forward command in the background and verifies success.

    :param k8s_command: List of command arguments for kubectl port-forward.
    :param check_port: Optional port number to check if port-forward is active.
    :return: True if successful, False otherwise.
    """
    try:
        # Start the subprocess
        print(f"Executing: {' '.join(k8s_command)}")
        process = subprocess.Popen(
            k8s_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        # Wait briefly to allow the process to initialize
        time.sleep(2)

        # Check if the process is still running
        if process.poll() is not None:
            stderr_output = process.stderr.read().decode().strip()
            print(f"Port-forward failed: {stderr_output}")
            return False

        # Optionally check if the port is active
        if check_port:
            result = subprocess.run(
                ["lsof", "-i", f"tcp:{check_port}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if result.stdout:
                print(f"Port-forward active on port {check_port}.")
                return True
            else:
                print(f"Port-forward not active on port {check_port}.")
                return False

        print("Port-forward command executed successfully.")
        return True

    except Exception as e:
        print(f"Error running port-forward: {e}")
        return False


def kill_process_on_port(port):
    """
    Checks if a port is in use and kills the process using it.

    :param port: The port number to check and free.
    """
    try:
        # Find the process using the port
        result = subprocess.run(
            ["lsof", "-ti", f"tcp:{port}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.stdout:
            pid = result.stdout.strip()
            print(f"Port {port} is in use by process {pid}. Killing process...")
            os.kill(int(pid), 9)
            print(f"Process {pid} killed. Port {port} is now free.")
        else:
            print(f"Port {port} is not in use.")
    except FileNotFoundError:
        print("`lsof` is not available. Ensure it is installed to check open ports.")
    except Exception as e:
        print(f"Failed to free port {port}: {e}")

def manage_tunnels_with_port_forward(tunnels, ssh_user=SSH_USER, ssh_host=SSH_HOST):
    """
    Manages SSH tunnels and optionally sets up `kubectl port-forward` for Kubernetes services or pods.
    
    :param tunnels: List of dictionaries containing tunnel configurations.
        Each dictionary should have:
        - local_port: The local port to bind.
        - remote_host: The remote host (e.g., localhost or IP where the service is running).
        - remote_port: The remote port of the service.
        - k8s_port_forward (optional): Dictionary with `resource_name`, `resource_type`, and `namespace` for Kubernetes port-forwarding.
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
        if k8s_port_forward:
            resource_name = k8s_port_forward["resource_name"]
            resource_type = k8s_port_forward.get("resource_type", "service")  # Default to service
            namespace = k8s_port_forward.get("namespace", "default")  # Default namespace if not provided
            k8s_command = [
                "sudo", "kubectl", "port-forward",
                f"{resource_type}/{resource_name}",
                f"{local_port}:{remote_port}",
                "-n", namespace
            ]
        else:
            k8s_command = None


        # Check if the tunnel is already open
        try:
            result = subprocess.run(
                ["lsof", "-i", f"tcp:{local_port}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if result.stdout:
                print(f"Tunnel already open on port {local_port}. Skipping SSH tunnel...")
            else:
                # Open the SSH tunnel
                try:
                    command = [
                        "ssh",
                        "-p", f"{server_port}",
                        "-L", f"{local_port}:{remote_host}:{remote_port}",
                        f"{ssh_user}@{ssh_host}",
                        # "-N",  # Don't execute commands, just open the tunnel
                        "-f",   # Run SSH in the background
                        "tmux", "new-session", "-d", f"{k8s_command}",
                    ]
                    print(f"Opening SSH tunnel: {local_port} -> {remote_host}:{remote_port} via {ssh_user}@{ssh_host}")
                    subprocess.run(command, check=True)
                    print(f"Tunnel opened successfully on port {local_port}")
                except subprocess.CalledProcessError as e:
                    print(f"Failed to open SSH tunnel on port {local_port}: {e}")
        except FileNotFoundError:
            print("`lsof` is not available. Ensure it is installed to check open tunnels.")
            return

        # Handle Kubernetes port-forwarding
        if k8s_port_forward:
            kill_process_on_port(local_port)
            resource_name = k8s_port_forward["resource_name"]
            resource_type = k8s_port_forward.get("resource_type", "service")  # Default to service
            namespace = k8s_port_forward.get("namespace", "default")  # Default namespace if not provided
            k8s_command = [
                "sudo", "kubectl", "port-forward",
                f"{resource_type}/{resource_name}",
                f"{local_port}:{remote_port}",
                "-n", namespace
            ]

            # Check if port-forward is already running
            try:
                result = subprocess.run(
                    ["pgrep", "-f", f"sudo kubectl port-forward {resource_type}/{resource_name}"],
                    stdout=subprocess.PIPE,
                    text=True
                )
                if str(local_port) in result.stdout:
                    print(f"Kubernetes port-forward already running on port {local_port}. Skipping...")
                else:
                    print(f"Setting up Kubernetes port-forward: {local_port} -> {resource_name}:{remote_port} in namespace '{namespace}'...", end = "")
                    run_k8s_port_forward(k8s_command, check_port=local_port)  # Run in the background
                    print(" done.")
            except Exception as e:
                print(f"Failed to set up Kubernetes port-forward for {resource_name} in namespace '{namespace}': {e}")

if __name__ == "__main__":
    # Configuration for the tunnels


    # Manage tunnels and port-forwards
    manage_tunnels_with_port_forward(SSH_TUNNELS,SSH_USER, SSH_HOST)
