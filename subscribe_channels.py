"""
YouTube Channel Mass Subscriber
Reads YouTube channel links from an Excel file and subscribes to each channel.

Usage:
    1. Create an Excel file with YouTube channel URLs in the first column
    2. Run: python subscribe_channels.py your_file.xlsx
    3. Log into your YouTube account when the browser opens
    4. Press Enter in the terminal to start subscribing
"""

import sys
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


def read_channel_links(file_path: str) -> list[str]:
    """Read YouTube channel links from an Excel or CSV file."""
    try:
        # Handle both CSV and Excel files
        if file_path.lower().endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        # Get the first column regardless of header name
        links = df.iloc[:, 0].dropna().tolist()
        # Filter to only include YouTube URLs
        youtube_links = [
            str(link).strip() 
            for link in links 
            if 'youtube.com' in str(link).lower() or 'youtu.be' in str(link).lower()
        ]
        return youtube_links
    except Exception as e:
        print(f"❌ Error reading Excel file: {e}")
        sys.exit(1)


def normalize_channel_url(url: str) -> str:
    """Convert various YouTube URL formats to channel page URL."""
    url = url.strip()
    
    # If it's already a channel URL, return as-is
    if '/channel/' in url or '/@' in url or '/c/' in url or '/user/' in url:
        return url
    
    # Handle video URLs - we can't subscribe from these directly
    if '/watch?' in url or 'youtu.be/' in url:
        print(f"⚠️  Video URL detected, will try to find channel: {url}")
        return url
    
    return url


def setup_browser() -> webdriver.Chrome:
    """Set up Chrome browser with appropriate options."""
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Keep browser open after script ends
    chrome_options.add_experimental_option("detach", True)
    
    # Use Selenium's built-in driver management (Selenium 4.6+)
    driver = webdriver.Chrome(options=chrome_options)
    
    # Make automation less detectable
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver


def wait_for_login(driver: webdriver.Chrome):
    """Open YouTube and wait for user to log in."""
    print("\n🌐 Opening YouTube...")
    driver.get("https://www.youtube.com")
    time.sleep(2)
    
    print("\n" + "=" * 60)
    print("👤 Please log into your YouTube/Google account in the browser.")
    print("   You have 60 seconds to log in...")
    print("=" * 60)
    
    # Wait 60 seconds for user to log in
    for i in range(60, 0, -1):
        print(f"\r⏳ Starting in {i} seconds... (log in now!)", end="", flush=True)
        time.sleep(1)
    print("\n")


def subscribe_to_channel(driver: webdriver.Chrome, url: str) -> bool:
    """Navigate to a channel and click subscribe."""
    try:
        print(f"\n📺 Navigating to: {url}")
        driver.get(url)
        time.sleep(4)  # Wait for page to fully load
        
        # If it's a video page, try to click on the channel name first
        if '/watch?' in url or 'youtu.be/' in url:
            try:
                # Try to find and click the channel link on video page
                channel_link = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "#owner #channel-name a, ytd-video-owner-renderer #channel-name a"))
                )
                channel_link.click()
                time.sleep(3)
            except TimeoutException:
                print("   ⚠️  Couldn't find channel link on video page")
        
        # First check if already subscribed
        try:
            page_html = driver.page_source.lower()
            # Check for subscribed state in the page
            subscribed_indicators = driver.find_elements(By.CSS_SELECTOR, 
                "#subscribe-button button, ytd-subscribe-button-renderer button, yt-button-shape button")
            for elem in subscribed_indicators:
                text = elem.text.strip().lower()
                aria = (elem.get_attribute("aria-label") or "").lower()
                if text == "subscribed" or "unsubscribe" in aria or text == "joined":
                    print("   ✅ Already subscribed to this channel!")
                    return True
        except:
            pass
        
        # Try to find and click the Subscribe button using JavaScript
        # This is more reliable for YouTube's custom elements
        subscribe_js = """
        // Find all potential subscribe buttons
        const buttons = document.querySelectorAll('button, yt-button-shape button, ytd-subscribe-button-renderer button');
        for (const btn of buttons) {
            const text = btn.innerText?.trim().toLowerCase() || '';
            const aria = btn.getAttribute('aria-label')?.toLowerCase() || '';
            
            // Check if it's a Subscribe button (not Subscribed)
            if ((text === 'subscribe' || aria.includes('subscribe to')) && 
                !text.includes('subscribed') && !aria.includes('unsubscribe')) {
                // Make sure it's visible
                const rect = btn.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0) {
                    btn.click();
                    return 'clicked';
                }
            }
        }
        
        // Also try the subscribe-button container
        const subBtn = document.querySelector('#subscribe-button button:not([aria-label*="Unsubscribe"])');
        if (subBtn) {
            const text = subBtn.innerText?.trim().toLowerCase() || '';
            if (text === 'subscribe' || text === '') {
                subBtn.click();
                return 'clicked';
            }
        }
        
        return 'not_found';
        """
        
        result = driver.execute_script(subscribe_js)
        
        if result == 'clicked':
            print("   🎉 Successfully subscribed!")
            time.sleep(2)
            return True
        
        # Fallback: Try using Selenium to find and click
        subscribe_selectors = [
            "#subscribe-button yt-button-shape button",
            "#subscribe-button button",
            "ytd-subscribe-button-renderer button",
            "yt-subscribe-button-view-model button",
            "#channel-header #subscribe-button button",
            "yt-button-shape.ytd-subscribe-button-renderer button",
        ]
        
        for selector in subscribe_selectors:
            try:
                buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                for btn in buttons:
                    text = btn.text.strip().lower()
                    aria = (btn.get_attribute("aria-label") or "").lower()
                    
                    # Skip if already subscribed
                    if "subscribed" in text or "unsubscribe" in aria:
                        print("   ✅ Already subscribed to this channel!")
                        return True
                    
                    # Click if it's a subscribe button
                    if text == "subscribe" or "subscribe" in aria:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                        time.sleep(0.5)
                        # Use JavaScript click as it's more reliable
                        driver.execute_script("arguments[0].click();", btn)
                        print("   🎉 Successfully subscribed!")
                        time.sleep(2)
                        return True
            except:
                continue
        
        print("   ❌ Could not find subscribe button")
        return False
            
    except TimeoutException:
        print(f"   ❌ Timeout while loading: {url}")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print("=" * 60)
        print("YouTube Channel Mass Subscriber")
        print("=" * 60)
        print("\nUsage: python subscribe_channels.py <excel_file.xlsx>")
        print("\nThe Excel file should have YouTube channel URLs in the first column.")
        print("\nExample Excel structure:")
        print("  ┌─────────────────────────────────────────┐")
        print("  │ Channel URLs                            │")
        print("  ├─────────────────────────────────────────┤")
        print("  │ https://youtube.com/@MrBeast            │")
        print("  │ https://youtube.com/channel/UC...       │")
        print("  │ https://youtube.com/c/ChannelName       │")
        print("  └─────────────────────────────────────────┘")
        sys.exit(1)
    
    excel_path = sys.argv[1]
    
    print("\n" + "=" * 60)
    print("🚀 YouTube Channel Mass Subscriber")
    print("=" * 60)
    
    # Read channel links
    print(f"\n📂 Reading channels from: {excel_path}")
    channels = read_channel_links(excel_path)
    
    if not channels:
        print("❌ No YouTube links found in the Excel file!")
        sys.exit(1)
    
    print(f"✅ Found {len(channels)} YouTube channel(s)")
    
    # Setup browser
    print("\n🔧 Setting up browser...")
    driver = setup_browser()
    
    try:
        # Wait for user to log in
        wait_for_login(driver)
        
        # Subscribe to each channel
        successful = 0
        failed = 0
        
        print("\n" + "=" * 60)
        print("📺 Starting subscription process...")
        print("=" * 60)
        
        for i, channel_url in enumerate(channels, 1):
            print(f"\n[{i}/{len(channels)}] Processing...")
            normalized_url = normalize_channel_url(channel_url)
            
            if subscribe_to_channel(driver, normalized_url):
                successful += 1
            else:
                failed += 1
            
            # Small delay between subscriptions to avoid rate limiting
            if i < len(channels):
                time.sleep(2)
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 SUMMARY")
        print("=" * 60)
        print(f"   ✅ Successful: {successful}")
        print(f"   ❌ Failed: {failed}")
        print(f"   📺 Total: {len(channels)}")
        print("\n🎬 Done! The browser will stay open.")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user.")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        driver.quit()
        sys.exit(1)


if __name__ == "__main__":
    main()

