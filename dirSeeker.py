import argparse
import os
import queue
import random
import re
import requests
import sys
import threading
from urllib.parse import urljoin


class DirSeeker:
    def __init__(self):
        self.args = None
        self.directories = []
        self.responses = []
        self.extensions = None
        self.queue = queue.Queue()
        self.threads = []
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.79 Safari/537.36 Edge/14.14393"
        ]

    # Setup argument parser
    def setup_parser(self):
        parser = argparse.ArgumentParser(description="Advance DirSeeker Tool")
        parser.add_argument('--target', help='Target URL', required=True)
        parser.add_argument(
            '--wordlist', help='Path to wordlist file', required=True)
        parser.add_argument(
            '--filter-codes', help='Only show status codes separated by comma (e.g., "200,301,302")')
        parser.add_argument(
            '--exclude-codes', help='Exclude status codes separated by comma (e.g., "403,404")')
        parser.add_argument(
            '--extensions', help='Comma separated list of extensions to check (e.g., "php,txt")')
        parser.add_argument(
            '--random-agent', help='Use random user agent strings for each request', action='store_true')
        parser.add_argument(
            '--threads', help='Number of threads to use', type=int, default=20)
        parser.add_argument(
            '--recursive', help='Enable recursive scan of sub-directories', action='store_true')
        parser.add_argument(
            '--color', help='Display color results', action='store_true')
        self.args = parser.parse_args()

    # Load the wordlist file
    def load_wordlist(self):
        try:
            with open(self.args.wordlist, 'r') as wordlist_file:
                self.directories = [line.rstrip() for line in wordlist_file]
        except FileNotFoundError:
            print("Wordlist file not found.")
            sys.exit()

    # Filter response status codes
    def filter_codes(self, response):
        if self.args.filter_codes:
            codes = [int(code.strip())
                     for code in self.args.filter_codes.split(',')]
            if response.status_code not in codes:
                return False

        if self.args.exclude_codes:
            codes = [int(code.strip())
                     for code in self.args.exclude_codes.split(',')]
            if response.status_code in codes:
                return False

        return True

    # Check if extension match
    def check_extension(self, url):
        if self.extensions:
            for ext in self.extensions:
                if url.endswith(ext):
                    return True
            return False
        else:
            return True

    # Send request to the target URL
    def send_request(self):
        while True:
            directory = self.queue.get()
            if not directory:
                break

            url = urljoin(self.args.target, directory)
            headers = {}
            if self.args.random_agent:
                user_agent = random.choice(self.user_agents)
                headers = {"User-Agent": user_agent}

            try:
                response = requests.get(url, headers=headers, timeout=10)
                self.responses.append((url, response))
                if self.filter_codes(response) and self.check_extension(url):
                    if self.args.color:
                        print(f"\033[92m[{response.status_code}] {url}\033[0m")
                    else:
                        print(f"[{response.status_code}] {url}")
            except (requests.exceptions.RequestException, requests.exceptions.Timeout):
                pass
            finally:
                self.queue.task_done()

    # Start scanning directories
    def scan_directories(self):
        # Start threads
        for i in range(self.args.threads):
            thread = threading.Thread(target=self.send_request)
            thread.start()
            self.threads.append(thread)

        # Add directories to queue
        for directory in self.directories:
            self.queue.put(directory)

        # Wait for all directories to be scanned
        self.queue.join()

        # Stop threads
        for i in range(self.args.threads):
            self.queue.put(None)
        for thread in self.threads:
            thread.join()

    # Enable recursive scan of sub-directories
    def recursive_scan(self, url):
        headers = {}
        if self.args.random_agent:
            user_agent = random.choice(self.user_agents)
            headers = {"User-Agent": user_agent}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            self.responses.append((url, response))
            if self.filter_codes(response) and self.check_extension(url):
                if self.args.color:
                    print(f"\033[92m[{response.status_code}] {url}\033[0m")
                else:
                    print(f"[{response.status_code}] {url}")
        except (requests.exceptions.RequestException, requests.exceptions.Timeout):
            pass

        if response.headers.get("Content-Type", "").startswith("text/html"):
            links = re.findall(r'href="(.*?)"', response.text)
            for link in links:
                if link.startswith(('/', 'http://', 'https://')):
                    if link.startswith('/'):
                        link = urljoin(url, link)
                    if link not in (x[0] for x in self.responses):
                        self.recursive_scan(link)

    # Start scanning directories recursively
    def scan_recursive_directories(self):
        base_url = self.args.target.rstrip('/')
        for url, response in self.responses:
            if response.status_code == 200:
                relative_url = url[len(base_url):]
                if relative_url.endswith('/'):
                    relative_url = relative_url[:-1]
                self.queue.put(relative_url)

        while not self.queue.empty():
            directory = self.queue.get()
            url = urljoin(base_url, directory)
            self.recursive_scan(url)
            self.queue.task_done()

    # Run the program
    def run(self):
        self.setup_parser()

        if self.args.extensions:
            self.extensions = [ext.strip()
                               for ext in self.args.extensions.split(',')]

        self.load_wordlist()

        if self.args.recursive:
            self.scan_recursive_directories()
        else:
            self.scan_directories()


if __name__ == '__main__':
    try:
        dir_search = DirSeeker()
        dir_search.run()
    except KeyboardInterrupt:
        print("\nExiting program...\n")
        sys.exit()
