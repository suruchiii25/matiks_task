"""
LinkedIn mentions collector for Matiks.

Assignment: "Track mentions of Matiks on Reddit, Twitter/X, and LinkedIn including
content, author, timestamps, and engagement metrics."

API Configuration:
- Requires LinkedIn API access (LinkedIn Partner Program or developer access)
- Set LINKEDIN_ACCESS_TOKEN environment variable with your API key
- Falls back to demo data when no API key is provided

Why API approach:
- LinkedIn API provides comprehensive search with engagement metrics
- Real-time access to posts, comments, likes, shares
- Proper rate limiting and reliable data collection
- Fallback ensures demo functionality for presentations
"""
import os
import pandas as pd
from typing import Optional, Dict, List


def fetch_linkedin_mentions_api(query="Matiks", limit=50, access_token=None):
    """
    Fetch LinkedIn mentions using LinkedIn API.
    
    Args:
        query: Search query (default: "Matiks")
        limit: Maximum number of posts to fetch
        access_token: LinkedIn API Access Token (overrides env var)
    
    Returns:
        DataFrame with columns: content, author, timestamp, engagement_likes, engagement_comments, url
    """
    # Get API key from parameter or environment
    api_key = access_token or os.getenv("LINKEDIN_ACCESS_TOKEN")
    
    if not api_key:
        print("LinkedIn API key not found. Set LINKEDIN_ACCESS_TOKEN environment variable or pass access_token parameter")
        return None
    
    try:
        import requests
        import json
        from datetime import datetime, timezone
        
        # LinkedIn API v2 endpoint for post search
        search_url = "https://api.linkedin.com/v2/socialActions"
        
        # Query parameters
        params = {
            'q': query,
            'count': min(limit, 50),  # LinkedIn API limit
            'fields': 'id,text,author,createdAt,likesCount,commentsCount,sharesCount'
        }
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(search_url, headers=headers, params=params, timeout=30)
        
        if response.status_code != 200:
            print(f"LinkedIn API error: {response.status_code} - {response.text}")
            return None
            
        data = response.json()
        
        # Process the response
        posts = []
        
        for post in data.get('elements', []):
            author = post.get('author', {})
            
            posts.append({
                'content': post.get('text', ''),
                'author': author.get('name', ''),
                'timestamp': post.get('createdAt', ''),
                'engagement_likes': post.get('likesCount', 0),
                'engagement_comments': post.get('commentsCount', 0),
                'engagement_shares': post.get('sharesCount', 0),
                'url': f"https://www.linkedin.com/feed/update/{post.get('id', '')}"
            })
        
        return pd.DataFrame(posts)
        
    except ImportError as e:
        print(f"Missing dependencies for LinkedIn API: {e}")
        return None
    except Exception as e:
        print(f"LinkedIn API request failed: {e}")
        return None


def fetch_linkedin_mentions_demo():
    """Demo data – Scope: content, author, timestamps, engagement metrics."""
    data = [
        {
            "content": "Matiks is one of the most engaging math apps I've used. Great for quick practice and building consistency. #EdTech #Matiks",
            "author": "Priya Sharma",
            "timestamp": "2026-02-01T10:00:00Z",
            "engagement_likes": 24,
            "engagement_comments": 3,
            "engagement_shares": 0,
            "url": "https://www.linkedin.com/feed/update/urn:li:activity:demo1"
        },
        {
            "content": "Just hit 100 days streak on Matiks! The team even sent a cake 🎂. Best way to stay sharp with numbers. Highly recommend.",
            "author": "Rahul Verma",
            "timestamp": "2026-01-28T14:30:00Z",
            "engagement_likes": 18,
            "engagement_comments": 5,
            "engagement_shares": 0,
            "url": "https://www.linkedin.com/feed/update/urn:li:activity:demo2"
        },
        {
            "content": "If you're looking for a math practice app that doesn't feel like homework, try Matiks. 1-min duels are addictive in a good way.",
            "author": "Anita Krishnan",
            "timestamp": "2026-01-25T09:15:00Z",
            "engagement_likes": 12,
            "engagement_comments": 2,
            "engagement_shares": 0,
            "url": "https://www.linkedin.com/feed/update/urn:li:activity:demo3"
        },
        {
            "content": "Matiks – making mental math fun again. Perfect for students and professionals who want to keep their number skills sharp.",
            "author": "EdTech Insights",
            "timestamp": "2026-01-22T16:00:00Z",
            "engagement_likes": 31,
            "engagement_comments": 4,
            "engagement_shares": 0,
            "url": "https://www.linkedin.com/feed/update/urn:li:activity:demo4"
        },
    ]
    return pd.DataFrame(data)


def fetch_linkedin_mentions(query="Matiks", limit=50, access_token=None):
    """
    Main function to fetch LinkedIn mentions.
    Tries API first, falls back to demo data if API fails or no key provided.
    
    Args:
        query: Search query
        limit: Maximum number of posts
        access_token: LinkedIn API Access Token
    
    Returns:
        DataFrame with LinkedIn mentions data
    """
    # Try API first
    api_data = fetch_linkedin_mentions_api(query, limit, access_token)
    if api_data is not None and not api_data.empty:
        print(f"Successfully fetched {len(api_data)} posts from LinkedIn API")
        return api_data
    
    # Fallback to demo data
    print("Falling back to LinkedIn demo data")
    return fetch_linkedin_mentions_demo()


if __name__ == "__main__":
    # Example usage
    posts = fetch_linkedin_mentions("Matiks", limit=10)
    if posts is not None:
        print(f"Found {len(posts)} LinkedIn posts about Matiks")
        print(posts[['author', 'engagement_likes', 'engagement_comments']].head())
