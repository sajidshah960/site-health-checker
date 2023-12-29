import requests
import yaml
import time
from collections import defaultdict
import signal
import sys

# Global dictionary to store cumulative availability data across cycles
cumulative_availability = defaultdict(lambda: {'total': 0, 'up': 0})

# Function to log availability percentages for each domain
def log_availability():
    global cumulative_availability

    print("Availability Percentage:")
    for domain, data in cumulative_availability.items():
        if data['total'] == 0:
            percentage = 0
        else:
            percentage = round((data['up'] / data['total']) * 100)
        print(f"{domain} has {percentage}% availability")
    print("--------------------------------------------------")

# Check health of endpoints
def check_health(endpoints):
    global cumulative_availability

    availability = defaultdict(lambda: {'total': 0, 'up': 0})
    while True:
        for endpoint in endpoints:
            url = endpoint.get('url')
            method = endpoint.get('method', 'GET')
            headers = endpoint.get('headers', {})
            body = endpoint.get('body', None)

            if url:
                try:
                    if method == 'GET':
                        start_time = time.time()
                        response = requests.get(url, headers=headers, timeout=5)
                    elif method == 'POST':
                        if body is None:
                            body = {}
                        start_time = time.time()
                        response = requests.post(url, headers=headers, json=body, timeout=5)
                    else:
                        raise ValueError('Invalid HTTP method')

                    response_time = round((time.time() - start_time) * 1000, 2)  # Calculate response time in milliseconds

                    if response.status_code >= 200 and response.status_code < 300:
                        response_time_ms = round(response.elapsed.total_seconds() * 1000, 2)
                        if response_time_ms <= 1500:
                            availability[url]['up'] += 1
                        else:
                            print(f"Endpoint {url} - Response Code: {response.status_code}, Response Time: {response_time_ms} ms => DOWN (Response time exceeds 1500ms)")
                    else:
                        print(f"Endpoint {url} - Response Code: {response.status_code} => DOWN (Status code not in range 2xx)")

                    availability[url]['total'] += 1


                except requests.RequestException as e:
                    print(f"Request to {url} failed: {e}")

        # Update cumulative availability data across cycles
        for url, data in availability.items():
            domain = url.split('/')[2]
            cumulative_availability[domain]['total'] += data['total']
            cumulative_availability[domain]['up'] += data['up']

        # Calculate and log availability percentages for each domain after each cycle
        log_availability()

        # Wait for 15 seconds before starting the next cycle
        time.sleep(15)

# Read YAML configuration file
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

# Signal handler for graceful exit
def exit_gracefully(signum, frame):
    print("\nExiting...")
    sys.exit(0)

# Main function
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python health_checker_script.py <config_file.yaml>")
        sys.exit(1)

    file_path = sys.argv[1]
    endpoints = read_config("config.yaml")

    # Register signal handler for graceful exit
    signal.signal(signal.SIGINT, exit_gracefully)

    # Start health checks
    check_health(endpoints)
