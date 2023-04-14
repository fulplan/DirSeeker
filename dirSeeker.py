import argparse
import os
import queue
import random
import re
import requests
import socket
import sys
import threading
from urllib.parse import urljoin, urlparse


class DirSeeker:
    def __init__(self):
        self.args = None
        self.directories = []
        self.responses = []
        self.extensions = {'.php', '.html', '.htm', '.txt', '.md'}
        self.queue = queue.Queue()
        self.threads = []
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.79 Safari/537.36 Edge/14.14393"
        ]
        self.color_codes = {
            200: "\033[92m",  # green
            201: "\033[92m",  # green
            202: "\033[92m",  # green
            204: "\033[92m",  # green
            301: "\033[96m",  # cyan
            302: "\033[96m",  # cyan
            307: "\033[96m",  # cyan
            308: "\033[96m",  # cyan
            401: "\033[93m",  # yellow
            403: "\033[93m",  # yellow
            404: "\033[91m",  # red
            405: "\033[91m",  # red
            500: "\033[91m",  # red
            501: "\033[91m"  # red
        }

    # Setup argument parser
    def setup_parser(self):
        parser = argparse.ArgumentParser(description="Advance DirSeeker Tool")
        parser.add_argument(
            '--target', help='Target URL or IP address', required=True)
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

    # Load the wordlist file and append extensions as files
    def load_wordlist(self):
        try:
            with open(self.args.wordlist, 'r') as wordlist_file:
                for line in wordlist_file:
                    dir_or_ext = line.rstrip()
                    if '.' not in dir_or_ext:
                        for ext in self.extensions:
                            filepath = f"{dir_or_ext}{ext}"
                            if os.path.isfile(filepath):
                                self.directories.append(filepath)
                    else:
                        if os.path.isfile(dir_or_ext):
                            self.directories.append(dir_or_ext)

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

    # Check if extension matches the specified extensions
    def check_extension(self, url):
        if not self.extensions:
            return True

        parsed_url = urlparse(url)
        path_components = os.path.splitext(parsed_url.path)

        for ext in self.extensions:
            if path_components[1] == f".{ext}":
                return True

        return False

    # Send HTTP request to the target
    def send_request(self):
        while True:
            directory = self.queue.get()
            if directory is None:
                break

            url = urlparse(self.args.target)

            if not url.scheme:
                url = url._replace(scheme='http')

            if not url.netloc:
                try:
                    socket.inet_aton(url.path)
                    url = url._replace(netloc=url.path)
                    url = url._replace(path='')
                except socket.error:
                    url = url._replace(netloc=url.path + '.com')
                    url = url._replace(path='')

            if not url.path:
                url = url._replace(path='/')

            url = urljoin(url.geturl(), directory)

            headers = {}
            if self.args.random_agent:
                user_agent = random.choice(self.user_agents)
                headers = {"User-Agent": user_agent}

            try:
                response = requests.get(url, headers=headers, timeout=10)
                self.responses.append((url, response))
                if self.filter_codes(response) and self.check_extension(url):
                    if self.args.color:
                        color_code = self.color_codes.get(
                            response.status_code, "")
                        print(
                            f"{color_code}[{response.status_code}] {url}\033[0m")
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
                    color_code = self.color_codes.get(response.status_code, "")
                    print(f"{color_code}[{response.status_code}] {url}\033[0m")
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
            self.extensions.update(ext.strip()
                                   for ext in self.args.extensions.split(','))

        self.load_wordlist()

        try:
            socket.inet_aton(self.args.target)
            self.args.target = f"http://{self.args.target}"
        except socket.error:
            parsed_url = urlparse(self.args.target)
            if not parsed_url.scheme or not parsed_url.netloc:
                self.args.target = f"http://{self.args.target}.com"

        if self.args.recursive:
            self.scan_recursive_directories()
        else:
            self.scan_directories()


if __name__ == '__main__':
    try:
        dir_search = DirSeeker()
        dir_search.run()
    except KeyboardInterrupt:
        sys.exit("\nExiting on user request.")
