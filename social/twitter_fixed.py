"""
Twitter/X mentions collector for Matiks.

Assignment: "Track mentions of Matiks on Reddit, Twitter/X, and LinkedIn including
content, author, timestamps, and engagement metrics."

API Configuration:
- Requires Twitter API v2 Bearer Token for real-time search
- Set TWITTER_BEARER_TOKEN environment variable with your API key
- Falls back to demo data when no API key is provided

Why API approach:
- Twitter API v2 provides comprehensive search with engagement metrics
- Real-time access to tweets, retweets, likes, replies
- Proper rate limiting and reliable data collection
- Fallback ensures demo functionality for presentations
"""
import os
import pandas as pd
from typing import Optional, Dict, List


def fetch_twitter_mentions_api(query="Matiks", limit=50, bearer_token=None):
    """
    Fetch Twitter/X mentions using Twitter API v2.
    
    Args:
        query: Search query (default: "Matiks")
        limit: Maximum number of tweets to fetch
        bearer_token: Twitter API v2 Bearer Token (overrides env var)
    
    Returns:
        DataFrame with columns: content, username, name, date, replyCount, retweetCount, likeCount, url
    """
    # Get API key from parameter or environment
    api_key = bearer_token or os.getenv("TWITTER_BEARER_TOKEN")
    
    if not api_key:
        print("Twitter API key not found. Set TWITTER_BEARER_TOKEN environment variable or pass bearer_token parameter")
        return None
    
    try:
        import requests
        import json
        from datetime import datetime, timezone
        
        # Twitter API v2 endpoint for recent search
        search_url = "https://api.twitter.com/2/tweets/search/recent"
        
        # Query parameters
        params = {
            'query': f"{query} -is:retweet lang:en",  # Search for Matiks, exclude retweets, English only
            'max_results': min(limit, 100),  # Twitter API limit is 100 per request
            'tweet.fields': 'created_at,author_id,public_metrics,context_annotations',
            'user.fields': 'username,name',
            'expansions': 'author_id'
        }
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(search_url, headers=headers, params=params, timeout=30)
        
        if response.status_code != 200:
            print(f"Twitter API error: {response.status_code} - {response.text}")
            return None
            
        data = response.json()
        
        # Process the response
        tweets = []
        users = {user['id']: user for user in data.get('includes', {}).get('users', [])}
        
        for tweet in data.get('data', []):
            user = users.get(tweet.get('author_id'), {})
            metrics = tweet.get('public_metrics', {})
            
            tweets.append({
                'content': tweet.get('text', ''),
                'username': user.get('username', ''),
                'name': user.get('name', ''),
                'date': tweet.get('created_at', ''),
                'replyCount': metrics.get('reply_count', 0),
                'retweetCount': metrics.get('retweet_count', 0),
                'likeCount': metrics.get('like_count', 0),
                'url': f"https://twitter.com/{user.get('username', '')}/status/{tweet.get('id', '')}"
            })
        
        return pd.DataFrame(tweets)
        
    except ImportError as e:
        print(f"Missing dependencies for Twitter API: {e}")
        return None
    except Exception as e:
        print(f"Twitter API request failed: {e}")
        return None


def fetch_twitter_mentions_demo():
    """Demo data – Scope: content, author, timestamps, engagement metrics."""
    data = [
        {
            "content": "Just hit 1500 rating on @Matiks! Anyone else finding the new update challenging? The math problems are getting harder but more rewarding. #Matiks #MathPractice",
            "username": "tech_enthusiast",
            "name": "Tech Enthusiast",
            "date": "2026-02-01T14:30:00Z",
            "replyCount": 2,
            "retweetCount": 4,
            "likeCount": 12,
            "url": "https://twitter.com/tech_enthusiast/status/1234567890"
        },
        {
            "content": "@Matiks has completely changed how I practice mental math. Used to hate numbers, now I do 10-minute duels daily. Highly recommend! 🧠✨",
            "username": "mathgeek99",
            "name": "Math Geek",
            "date": "2026-01-30T09:15:00Z",
            "replyCount": 5,
            "retweetCount": 1,
            "likeCount": 18,
            "url": "https://twitter.com/mathgeek99/status/1234567891"
        },
        {
            "content": "The gamification in @Matiks is brilliant. My kids actually ask to practice math now. That's a win! 🎯",
            "username": "growthhacker",
            "name": "Growth Hacker",
            "date": "2026-01-28T16:45:00Z",
            "replyCount": 1,
            "retweetCount": 0,
            "likeCount": 3,
            "url": "https://twitter.com/growthhacker/status/1234567892"
        },
        {
            "content": "Comparing @Matiks vs other math apps - the speed and accuracy focus is unmatched. The 1-minute duels are addictive! ⚡",
            "username": "edutech_daily",
            "name": "EduTech Daily",
            "date": "2026-01-25T11:20:00Z",
            "replyCount": 8,
            "retweetCount": 15,
            "likeCount": 45,
            "url": "https://twitter.com/edutech_daily/status/1234567893"
        },
    ]
    return pd.DataFrame(data)


def fetch_twitter_mentions(query="Matiks", limit=50, bearer_token=None):
    """
    Main function to fetch Twitter/X mentions.
    Tries API first, falls back to demo data if API fails or no key provided.
    
    Args:
        query: Search query
        limit: Maximum number of tweets
        bearer_token: Twitter API v2 Bearer Token
    
    Returns:
        DataFrame with Twitter mentions data
    """
    # Try API first
    api_data = fetch_twitter_mentions_api(query, limit, bearer_token)
    if api_data is not None and not api_data.empty:
        print(f"Successfully fetched {len(api_data)} tweets from Twitter API")
        return api_data
    
    # Fallback to demo data
    print("Falling back to Twitter demo data")
    return fetch_twitter_mentions_demo()


if __name__ == "__main__":
    # Example usage
    tweets = fetch_twitter_mentions("Matiks", limit=10)
    if tweets is not None:
        print(f"Found {len(tweets)} tweets about Matiks")
        print(tweets[['username', 'name', 'likeCount', 'retweetCount']].head())
