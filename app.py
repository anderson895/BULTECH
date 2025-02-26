import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def extract_tweet_id(url):
    """Extract the Tweet ID from a Twitter URL"""
    match = re.search(r'/status/(\d+)', url)
    return match.group(1) if match else None

def fetch_tweets(thread_link):
    """Scrape tweets from a Twitter thread using Selenium"""
    tweet_id = extract_tweet_id(thread_link)
    if not tweet_id:
        return []

    # Set up Selenium WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode (no UI)
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(thread_link)
        time.sleep(5)  # Wait for the page to load

        # Scrape tweets
        tweets_elements = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='tweetText']")
        tweets = [tweet.text for tweet in tweets_elements if tweet.text]

        return tweets

    except Exception as e:
        print(f"Error fetching tweets: {e}")
        return []
    
    finally:
        driver.quit()  # Close browser

def analyze_cyberbullying(tweets):
    """Simple keyword-based detection (Replace with ML Model in future)"""
    harmful_words = {"stupid", "idiot", "hate", "kill", "dumb", "ugly", "trash"}

    harmful_count = sum(1 for tweet in tweets if any(word in tweet.lower() for word in harmful_words))
    percentage = round((harmful_count / len(tweets)) * 100, 2) if tweets else 0

    return {
        "message": "Analysis complete.",
        "percentage": percentage,
        "summary": "This thread contains cyberbullying content." if percentage > 50 else "This thread seems safe.",
        "chart_data": [len(tweets) - harmful_count, harmful_count]  
    }

@app.route('/analyze', methods=['POST'])
def analyze():
    """Flask route to analyze a Twitter thread"""
    data = request.get_json()
    thread_link = data.get("thread_link")

    if not thread_link:
        return jsonify({"error": "No thread link provided"}), 400

    tweets = fetch_tweets(thread_link)

    if not tweets:
        return jsonify({"error": "Could not fetch tweets. Invalid or private thread."}), 400

    result = analyze_cyberbullying(tweets)
    return jsonify(result)








@app.route('/')
def index():
    """Render the HTML UI"""
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
