# X (Twitter) Bookmark Crawler

This tool uses Selenium to scrape your bookmarks from X.com.

## Prerequisite
- Python 3+
- Chrome Browser installed

## Installation
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
1. Run the script:
   ```bash
   python main.py
   ```
2. A Chrome window will open.
3. Log in to your X account.
4. The script will automatically detect when you reach the bookmarks page and start scrolling/saving.
5. Bookmarks will be saved to `bookmarks.json`.

## Notes
- The script waits 5 minutes (300 seconds) for you to log in.
- It is currently set to stop after collecting 50 bookmarks for testing. You can change this in `main.py`.
