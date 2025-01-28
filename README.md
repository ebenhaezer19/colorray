# Colloray | Moodle Profile Scraper

A powerful and efficient tool for scraping profile information from Moodle learning management systems. This tool is designed for educational purposes and authorized testing only.
You must log in and must a CIT People.

## Features

- Multi-threaded profile scanning
- Multiple output formats (TXT, JSON)
- Detailed error logging
- Progress tracking and statistics
- Anti-detection mechanisms
- Command-line interface
- Organized results with timestamps

![Colloray](https://github.com/user-attachments/assets/d982a53e-8678-4c3b-b8a4-eefb3b15df57)


## Installation



1. Clone the repository:
```bash
git clone https://github.com/yourusername/moodle-scraper.git
cd moodle-scraper
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

Basic usage:
```bash
python colloray.py
```

Advanced usage with custom parameters:
```bash
python colloray.py --start 1000 --end 2000 --threads 10 --delay 0.3
```

### Command Line Arguments

- `--start`: Starting user ID (default: 750)
- `--end`: Ending user ID (default: 1000)
- `--threads`: Number of concurrent threads (default: 5)
- `--delay`: Delay between requests in seconds (default: 0.5)

## Output

Results are saved in the `moodle_results` directory with timestamped folders containing:
- detailed_profiles.txt - Complete profile information
- profiles.json - Structured data format
- emails.txt - Email addresses only
- errors.log - Error reports if any

## Configuration

Update the `COOKIE` and `BASE_URL` variables in the script according to your Moodle instance.

![image](https://github.com/user-attachments/assets/16f406eb-c65f-4141-ab36-02a7d512c6be)

Ex : poglrsc7gnum9ermf590fprbt9


## Disclaimer

This tool is for educational purposes only. Ensure you have proper authorization before scanning any Moodle instance.

## License

MIT License - See LICENSE file for details
