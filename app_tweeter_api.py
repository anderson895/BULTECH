import os
import tweepy
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import re
import time

app = Flask(__name__)
CORS(app)

# Load Twitter API credentials from environment variable
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")  # Corrected
if not BEARER_TOKEN:
    raise ValueError("Twitter API Bearer Token is missing. Set it as an environment variable.")

# Authenticate with Twitter API
try:
    client = tweepy.Client(bearer_token=BEARER_TOKEN)
except Exception as e:
    raise ValueError(f"Failed to authenticate with Twitter API: {e}")

@app.route('/')
def index():
    """Render the HTML UI"""
    return render_template("index.html")

def extract_tweet_id(url):
    """Extract the Tweet ID from a Twitter URL"""
    match = re.search(r'/status/(\d+)', url)
    return match.group(1) if match else None

def fetch_tweets(thread_link):
    tweet_id = extract_tweet_id(thread_link)
    if not tweet_id:
        print("Invalid Tweet URL.")
        return []

    try:
        tweet_response = client.get_tweet(tweet_id, tweet_fields=["conversation_id", "author_id"])
        if not tweet_response or not tweet_response.data:
            print("Tweet not found or inaccessible.")
            return []

        conversation_id = tweet_response.data.get("conversation_id")
        if not conversation_id:
            print("Could not retrieve conversation ID.")
            return []

        query = f"conversation_id:{conversation_id}"
        tweets = []

        paginator = tweepy.Paginator(client.search_recent_tweets, query=query, tweet_fields=["text"], max_results=100)

        for tweet_page in paginator:
            if tweet_page.data:
                tweets.extend(tweet.text for tweet in tweet_page.data if tweet.text)

            if len(tweets) >= 500:
                break

            time.sleep(5)  # Wait 5 seconds between requests

        return tweets

    except tweepy.TooManyRequests:
        print("Twitter API error: Too Many Requests. Waiting 15 minutes before retrying...")
        time.sleep(900)  # Wait 15 minutes before retrying
        return []
    except tweepy.TweepyException as e:
        print(f"Twitter API error: {e}")
    except Exception as e:
        print(f"Error fetching tweets: {e}")
    return []

def analyze_cyberbullying(tweets):
    """Simple keyword-based detection (Replace with ML Model in future)"""
    harmful_words = {"stupid", "idiot", "hate", "kill", "dumb", "ugly", "trash"}

    harmful_count = sum(1 for tweet in tweets if any(word in tweet.lower() for word in harmful_words))
    percentage = round((harmful_count / len(tweets)) * 100, 2) if tweets else 0

    return {
        "message": "Analysis complete.",
        "percentage": percentage,
        "summary": "This thread contains cyberbullying content." if percentage > 50 else "This thread seems safe.",
        "chart_data": [len(tweets) - harmful_count, harmful_count]  # Example chart data for visualization
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
