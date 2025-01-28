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
BASE_URL = "https://moodle.calvin.ac.id/user/profile.php?id="
COOKIE = "MoodleSession=poglrsc7gnum9ermf590fprbt9"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    'Cookie': COOKIE
}

# Create output directory
OUTPUT_DIR = "moodle_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

class MoodleScraper:
    def __init__(self, start_id, end_id, threads=5, delay=0.5):
        self.start_id = start_id
        self.end_id = end_id
        self.threads = threads
        self.delay = delay
        self.profiles = []
        self.found_count = 0
        self.errors = []
        self.start_time = None

    def decode_url_email(self, encoded_str):
        """Decode URL-encoded email string."""
        return unquote(encoded_str)

    def get_user_profile(self, user_id):
        """Fetch user profile details with enhanced error handling."""
        try:
            # Add random delay to avoid detection
            time.sleep(self.delay + random.uniform(0, 0.5))
            
            response = requests.get(
                f"{BASE_URL}{user_id}", 
                headers=HEADERS, 
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
                self.errors.append(f"Access forbidden - Check cookie validity! ID: {user_id}")
                
            return None
            
        except Exception as e:
            self.errors.append(f"Error fetching ID {user_id}: {str(e)}")
            return None

    def save_results(self):
        """Save results in multiple formats."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create timestamp directory
        result_dir = os.path.join(OUTPUT_DIR, timestamp)
        os.makedirs(result_dir, exist_ok=True)
        
        # Save detailed profiles
        detailed_path = os.path.join(result_dir, "detailed_profiles.txt")
        with open(detailed_path, "w", encoding='utf-8') as f:
            f.write("MOODLE PROFILE SCAN RESULTS\n")
            f.write(f"Scan Range: {self.start_id} - {self.end_id}\n")
            f.write(f"Total Profiles: {len(self.profiles)}\n")
            f.write(f"Scan Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Duration: {time.time() - self.start_time:.2f} seconds\n")
            f.write("=" * 50 + "\n\n")
            
            for profile in self.profiles:
                for key, value in profile.items():
                    if value:
                        f.write(f"{key.title()}: {value}\n")
                f.write("─" * 50 + "\n\n")

        # Save JSON format
        json_path = os.path.join(result_dir, "profiles.json")
        with open(json_path, "w", encoding='utf-8') as f:
            json.dump(self.profiles, f, indent=2, ensure_ascii=False)

        # Save emails only
        emails_path = os.path.join(result_dir, "emails.txt")
        with open(emails_path, "w", encoding='utf-8') as f:
            for profile in self.profiles:
                if profile['email']:
                    f.write(f"{profile['email']}\n")

        # Save error log
        if self.errors:
            error_path = os.path.join(result_dir, "errors.log")
            with open(error_path, "w", encoding='utf-8') as f:
                f.write("\n".join(self.errors))

        return result_dir

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
    args = parser.parse_args()

    print(BANNER)
    print(Fore.YELLOW + "Enhanced Moodle Profile Scraper - Use Responsibly!\n" + Fore.RESET)

    scraper = MoodleScraper(args.start, args.end, args.threads, args.delay)
    scraper.scan_profiles()


if __name__ == "__main__":
    main()