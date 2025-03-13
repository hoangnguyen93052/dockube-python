import os
import subprocess
import json
import time
import sys
import yaml

class DockerManager:
    def __init__(self):
        self.images = []
        self.containers = []

    def list_images(self):
        try:
            result = subprocess.run(['docker', 'images', '--format', '{{json .}}'], 
                                    stdout=subprocess.PIPE, text=True, check=True)
            images = result.stdout.strip().split('\n')
            self.images = [json.loads(image) for image in images if image]
            return self.images
        except Exception as e:
            print(f"Error listing images: {e}")
            return []

    def build_image(self, dockerfile_path, tag):
        try:
            subprocess.run(['docker', 'build', '-t', tag, dockerfile_path], check=True)
            print(f"Image {tag} built successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to build image: {e}")

    def run_container(self, image, name, ports=None):
        command = ['docker', 'run', '-d', '--name', name]
        if ports:
            command.extend(['-p', ports])
        command.append(image)
        try:
            result = subprocess.run(command, check=True)
            print(f"Container {name} started successfully.")
            self.containers.append(name)
            return result.returncode
        except subprocess.CalledProcessError as e:
            print(f"Failed to run container: {e}")
            return None

    def stop_container(self, name):
        try:
            subprocess.run(['docker', 'stop', name], check=True)
            print(f"Container {name} stopped successfully.")
            self.containers.remove(name)
        except subprocess.CalledProcessError as e:
            print(f"Failed to stop container: {e}")

    def remove_container(self, name):
        try:
            subprocess.run(['docker', 'rm', name], check=True)
            print(f"Container {name} removed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to remove container: {e}")

class KubernetesManager:
    def __init__(self, kubeconfig):
        self.kubeconfig = kubeconfig
        os.environ['KUBECONFIG'] = kubeconfig

    def apply_yaml(self, yaml_file):
        try:
            subprocess.run(['kubectl', 'apply', '-f', yaml_file], check=True)
            print(f"Applied configuration from {yaml_file}.")
        except subprocess.CalledProcessError as e:
            print(f"Error applying YAML file: {e}")

    def get_pods(self):
        try:
            result = subprocess.run(['kubectl', 'get', 'pods', '-o', 'json'], 
                                    stdout=subprocess.PIPE, text=True, check=True)
            pods = json.loads(result.stdout).get('items', [])
            return [pod['metadata']['name'] for pod in pods]
        except Exception as e:
            print(f"Error getting pods: {e}")
            return []

    def delete_pod(self, pod_name):
        try:
            subprocess.run(['kubectl', 'delete', 'pod', pod_name], check=True)
            print(f"Deleted pod {pod_name}.")
        except subprocess.CalledProcessError as e:
            print(f"Error deleting pod: {e}")

class DockerKubernetesManager:
    def __init__(self, kubeconfig):
        self.docker_manager = DockerManager()
        self.k8s_manager = KubernetesManager(kubeconfig)

    def deploy_docker_image(self, dockerfile_path, tag, container_name, ports):
        self.docker_manager.build_image(dockerfile_path, tag)
        self.docker_manager.run_container(tag, container_name, ports)

    def deploy_kubernetes(self, yaml_file):
        self.k8s_manager.apply_yaml(yaml_file)

    def manage_containers_and_pods(self):
        containers_info = self.docker_manager.list_images()
        print("Docker Images:")
        for info in containers_info:
            print(info)

        print("Kubernetes Pods:")
        pods = self.k8s_manager.get_pods()
        for pod in pods:
            print(pod)

def main():
    kubeconfig = os.getenv('KUBECONFIG', 'path/to/your/kubeconfig.yaml')
    manager = DockerKubernetesManager(kubeconfig)

    # Deploy Docker image
    dockerfile_path = './Dockerfile'
    docker_image_tag = 'my_app_image:latest'
    container_name = 'my_app_container'
    ports = '8080:80'
    manager.deploy_docker_image(dockerfile_path, docker_image_tag, container_name, ports)

    # Deploy Kubernetes resources
    k8s_yaml_file = './kubernetes-deployment.yaml'
    manager.deploy_kubernetes(k8s_yaml_file)

    # Manage containers and pods
    manager.manage_containers_and_pods()

    # Wait for user input to stop and remove containers
    input("Press Enter to stop and remove the Docker container...")
    manager.docker_manager.stop_container(container_name)
    manager.docker_manager.remove_container(container_name)

if __name__ == "__main__":
    main()