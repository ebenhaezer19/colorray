import requests
from bs4 import BeautifulSoup
import time
from colorama import Fore, init
from urllib.parse import unquote, urljoin
from datetime import datetime
import os
import json
import random
import argparse
import concurrent.futures
import getpass

# Initialize colorama for colored console output
init()

# Banner
BANNER = Fore.CYAN + """
▓█████▄  ██▀███   ▒█████   ██▓     ██▓    ▄▄▄     ▓██   ██▓
▒██▀ ██▌▓██ ▒ ██▒▒██▒  ██▒▓██▒    ▓██▒   ▒████▄    ▒██  ██▒
░██   █▌▓██ ░▄█ ▒▒██░  ██▒▒██░    ▒██░   ▒██  ▀█▄   ▒██ ██░
░▓█▄   ▌▒██▀▀█▄  ▒██   ██░▒██░    ▒██░   ░██▄▄▄▄██  ░ ▐██▓░
░▒████▓ ░██▓ ▒██▒░ ████▓▒░░██████▒░██████▒▓█   ▓██▒ ░ ██▒▓░
 ▒▒▓  ▒ ░ ▒▓ ░▒▓░░ ▒░▒░▒░ ░ ▒░▓  ░░ ▒░▓  ░▒▒   ▓▒█░  ██▒▒▒ 
 ░ ▒  ▒   ░▒ ░ ▒░  ░ ▒ ▒░ ░ ░ ▒  ░░ ░ ▒  ░ ▒   ▒▒ ░▓██ ░▒░ 
 ░ ░  ░   ░░   ░ ░ ░ ░ ▒    ░ ░     ░ ░    ░   ▒   ▒ ▒ ░░  
   ░       ░         ░ ░      ░  ░    ░  ░     ░  ░░ ░     
 ░                                             ░  ░  ░     
""" + Fore.RESET

# Configuration
BASE_URL = "https://moodle.calvin.ac.id/"
LOGIN_URL = urljoin(BASE_URL, "/login/index.php")
PROFILE_URL = urljoin(BASE_URL, "/user/profile.php?id=")
OUTPUT_DIR = "moodle_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

class MoodleScraper:
    def __init__(self, start_id, end_id, email, password, threads=5, delay=0.5):
        self.start_id = start_id
        self.end_id = end_id
        self.threads = threads
        self.delay = delay
        self.email = email
        self.password = password
        self.session = requests.Session()
        self.profiles = []
        self.found_count = 0
        self.errors = []
        self.start_time = None
        self.logged_in = False

    def login(self):
        """Authenticate with Moodle using email and password."""
        try:
            # First get the login page to obtain the logintoken
            response = self.session.get(LOGIN_URL, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            logintoken = soup.find('input', {'name': 'logintoken'}).get('value', '')

            # Prepare login payload
            payload = {
                'anchor': '',
                'logintoken': logintoken,
                'username': self.email,
                'password': self.password
            }

            # Post login credentials
            response = self.session.post(LOGIN_URL, data=payload, timeout=10)
            
            # Check if login was successful
            if "Invalid login" in response.text:
                self.errors.append("Login failed: Invalid email or password")
                return False
                
            self.logged_in = True
            return True

        except Exception as e:
            self.errors.append(f"Login error: {str(e)}")
            return False

    def decode_url_email(self, encoded_str):
        """Decode URL-encoded email string."""
        return unquote(encoded_str)

    def get_user_profile(self, user_id):
        """Fetch user profile details with enhanced error handling."""
        if not self.logged_in:
            return None

        try:
            # Add random delay to avoid detection
            time.sleep(self.delay + random.uniform(0, 0.5))
            
            response = self.session.get(
                f"{PROFILE_URL}{user_id}", 
                timeout=10
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Enhanced data extraction
                email_link = soup.find('a', href=lambda x: x and 'mailto:' in x)
                title_tag = soup.find('title')
                img_tag = soup.find('img', class_='userpicture')
                
                # Extract additional information
                description = soup.find('div', class_='description')
                last_access = soup.find('dt', string='Last access to site')
                if last_access:
                    last_access = last_access.find_next('dd').text.strip()
                
                profile = {
                    'id': user_id,
                    'name': title_tag.text.split(':')[0].strip() if title_tag else None,
                    'email': self.decode_url_email(email_link['href'].split(':')[1]) if email_link else None,
                    'image': urljoin(BASE_URL, img_tag['src']) if img_tag else None,
                    'description': description.text.strip() if description else None,
                    'last_access': last_access
                }
                
                # Only return if we found useful information
                if any(value for value in profile.values() if value):
                    return profile
                    
            elif response.status_code == 403:
                self.errors.append(f"Access forbidden - Check your account permissions! ID: {user_id}")
                
            return None
            
        except Exception as e:
            self.errors.append(f"Error fetching ID {user_id}: {str(e)}")
            return None

    def scan_profiles(self):
        """Scan profiles using multiple threads."""
        self.start_time = time.time()
        total_ids = self.end_id - self.start_id + 1

        print(Fore.WHITE + "🚀 Starting scan with enhanced features...")
        print(Fore.MAGENTA + "═" * 50 + Fore.RESET)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = []
            for user_id in range(self.start_id, self.end_id + 1):
                futures.append(executor.submit(self.get_user_profile, user_id))

            for i, future in enumerate(concurrent.futures.as_completed(futures)):
                profile = future.result()
                progress = (i + 1) / total_ids * 100
                
                print(f"\r🔍 Progress: {progress:.1f}% | Found: {self.found_count}", end="", flush=True)
                
                if profile:
                    self.found_count += 1
                    self.profiles.append(profile)
                    print(Fore.GREEN + f"\n✓ Found: {profile['name']} ({profile['email']})" + Fore.RESET)

        result_dir = self.save_results()
        duration = time.time() - self.start_time

        # Final report
        print(Fore.MAGENTA + "\n" + "═" * 50)
        print(Fore.CYAN + f"\n✅ Scan completed!")
        print(f"📊 Statistics:")
        print(f"   - Total profiles found: {self.found_count}")
        print(f"   - Success rate: {(self.found_count/total_ids)*100:.1f}%")
        print(f"   - Duration: {duration:.2f} seconds")
        print(f"   - Average speed: {total_ids/duration:.1f} profiles/second")
        print(Fore.YELLOW + f"\n📁 Results saved in: {result_dir}")
        if self.errors:
            print(Fore.RED + f"⚠️ Encountered {len(self.errors)} errors. Check errors.log" + Fore.RESET)


def main():
    parser = argparse.ArgumentParser(description='Enhanced Moodle Profile Scraper')
    parser.add_argument('--start', type=int, default=750, help='Starting user ID')
    parser.add_argument('--end', type=int, default=1000, help='Ending user ID')
    parser.add_argument('--threads', type=int, default=5, help='Number of threads')
    parser.add_argument('--delay', type=float, default=0.5, help='Delay between requests')
    parser.add_argument('--email', type=str, help='Moodle account email')
    args = parser.parse_args()

    # Get password securely
    password = getpass.getpass("Enter your Moodle password: ")

    print(BANNER)
    print(Fore.YELLOW + "Enhanced Moodle Profile Scraper - Use Responsibly!\n" + Fore.RESET)

    scraper = MoodleScraper(args.start, args.end, args.email, password, args.threads, args.delay)
    
    if not scraper.login():
        print(Fore.RED + "❌ Login failed. Check your credentials and try again.")
        if scraper.errors:
            print(Fore.RED + "\n".join(scraper.errors))
        return
    
    scraper.scan_profiles()

if __name__ == "__main__":
    main()