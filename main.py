import os
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

# Load environment variables (if we need them later)
load_dotenv()

def setup_driver():
    """Sets up the Chrome WebDriver."""
    chrome_options = Options()
    # chrome_options.add_argument("--headless") # Comment out to see the browser
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-notifications")
    
    # This helps avoid some bot detection, though X is strict
    chrome_options.add_argument("--disable-blink-features=AutomationControlled") 
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Additional stealth setting
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """
    })
    
    return driver

def main():
    driver = setup_driver()
    try:
        print("Opening X (Twitter)...")
        driver.get("https://x.com/i/bookmarks")
        
        # Step 1: Login Check
        # Since we are starting fresh, the user will likely need to log in.
        print("Please log in to your account in the browser window.")
        print("Script will wait until you are redirected to the bookmarks page or for 60 seconds...")
        
        # Loop to ensure we get to the bookmarks page
        max_retries = 60 # 5 minutes roughly
        for i in range(max_retries):
            current_url = driver.current_url
            if "bookmarks" in current_url:
                print("On bookmarks page. Starting crawl...")
                break
            elif "login" in current_url or "flow" in current_url:
                print(f"Waiting for login... ({i}/{max_retries})")
                time.sleep(5)
            elif "home" in current_url:
                print("Detected Home page. Navigating to Bookmarks...")
                driver.get("https://x.com/i/bookmarks")
                time.sleep(5)
            else:
                print(f"Current URL: {current_url}. Waiting... ({i}/{max_retries})")
                time.sleep(5)
        else:
            print("Timed out waiting for bookmarks page.")
            return

        print("Starting to scroll and collect bookmarks...")
        
        # Set to store unique tweet URLs or IDs to avoid duplicates
        collected_tweets = set()
        bookmarks_data = []
        
        last_height = driver.execute_script("return document.body.scrollHeight")
        no_change_count = 0
        
        # Simple scrolling loop (can be refined)
        while True:
            # Find tweet elements
            articles = driver.find_elements(By.TAG_NAME, "article")
            
            new_items_found = 0
            for article in articles:
                try:
                    # Extract basic info
                    text = article.text
                    
                    # Try to find a link to the tweet
                    links = article.find_elements(By.TAG_NAME, "a")
                    tweet_url = None
                    for link in links:
                        href = link.get_attribute("href")
                        if href and "/status/" in href and "/photo/" not in href:
                            tweet_url = href
                            break
                    
                    if tweet_url and tweet_url not in collected_tweets:
                        collected_tweets.add(tweet_url)
                        bookmarks_data.append({
                            "url": tweet_url,
                            "text": text
                        })
                        # print(f"Found bookmark: {tweet_url}")
                        new_items_found += 1
                        
                except Exception as e:
                    continue 

            if new_items_found > 0:
                print(f"Collected {new_items_found} new bookmarks. Total: {len(bookmarks_data)}")
                no_change_count = 0
            else:
                no_change_count += 1
            
            # Scroll down
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(2) # Wait for content to load
            
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                if no_change_count > 5:
                    print("Reached bottom of page or no new items loading.")
                    break
            else:
                last_height = new_height
                # Reset check if we successfully scrolled logic could be here, 
                # but with infinite scroll, height changes.
            
            # Optional: Limit for testing (increased to 100)
            if len(bookmarks_data) >= 100:
                print("Collected 100 bookmarks. Stopping for test run.")
                break

        # Save to file
        with open("bookmarks.json", "w", encoding="utf-8") as f:
            json.dump(bookmarks_data, f, indent=4, ensure_ascii=False)
        print(f"Saved {len(bookmarks_data)} bookmarks to bookmarks.json")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Keep browser open for a bit or close it? 
        # Usually good to close, but maybe user wants to see it.
        # driver.quit() 
        input("Press Enter to close the browser...")
        driver.quit()

if __name__ == "__main__":
    main()
