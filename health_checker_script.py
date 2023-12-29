import requests
import yaml
import time
import signal
from collections import defaultdict
import sys

# Function to read YAML configuration file
def read_config(file_path):
    try:
        with open(file_path, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print("File not found. Please provide a valid YAML configuration file.")
        sys.exit(1)
    except yaml.YAMLError as exc:
        print(f"Error in YAML file: {exc}")
        sys.exit(1)

# Function to perform health checks
def check_health(endpoints):
    availability = defaultdict(lambda: {'total': 0, 'up': 0})
    while True:
        for endpoint in endpoints:
            url = endpoint.get('url') 
            method = endpoint.get('method', None)
            headers = endpoint.get('headers', {})
            body = endpoint.get('body', None)

            try:
                if method == 'GET':
                    response = requests.get(url, headers=headers, timeout=5)
                elif method == 'POST':
                    response = requests.post(url, headers=headers, json=body, timeout=5)
                else:
                    raise ValueError('Invalid HTTP method')

                if 200 <= response.status_code < 300 and response.elapsed.total_seconds() * 1000 < 500:
                    availability[url]['up'] += 1
                availability[url]['total'] += 1

            except requests.RequestException:
                availability[url]['total'] += 1

        print_results(availability)
        time.sleep(15)

# Function to calculate and log availability percentages
def print_results(availability):
    print("Availability Percentage:")
    for url, data in availability.items():
        total = data['total']
        up = data['up']
        percentage = 0 if total == 0 else round((up / total) * 100)
        print(f"{url} has {percentage}% availability")

# Signal handler for graceful exit
def exit_gracefully(signum, frame):
    print("\nExiting...")
    sys.exit(0)

# Main program
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python health_checker_script.py <config_file.yaml>")
        sys.exit(1)

    file_path = sys.argv[1]
    endpoints = read_config(file_path)

    # Register signal handler for graceful exit
    signal.signal(signal.SIGINT, exit_gracefully)

    # Start health checks
    check_health(endpoints)
