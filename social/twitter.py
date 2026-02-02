"""
Twitter/X mentions collector for Matiks.
API-ready: will use official API or snscrape when available.
Fallback: demo data (scraping can be blocked/unstable).
"""
import pandas as pd
import os
from typing import Optional, List, Dict

def fetch_twitter_mentions_api(query="Matiks", limit=50):
    """Placeholder for official Twitter API (requires paid access/credits)."""
    raise NotImplementedError("Twitter API requires paid access. Using demo data.")

def fetch_twitter_mentions_snscrape(query: str = "Matiks", limit: int = 50) -> pd.DataFrame:
    """
    Best-effort no-key mode using snscrape.

    Notes:
    - This can break if Twitter blocks scraping.
    - We keep the same schema as demo: date, content, username, name, replyCount,
      retweetCount, likeCount, url
    """
    try:
        import snscrape.modules.twitter as sntwitter
    except Exception as e:
        raise ImportError(f"snscrape not available: {e}") from e

    # A slightly more targeted query helps reduce noise.
    # (You can tune this later: include @Matiks, "matiks app", etc.)
    q = query
    scraper = sntwitter.TwitterSearchScraper(q)

    rows = []
    for i, tweet in enumerate(scraper.get_items()):
        if i >= limit:
            break
        user = getattr(tweet, "user", None)
        username = getattr(user, "username", "") if user else ""
        name = getattr(user, "displayname", "") if user else ""
        date_val = getattr(tweet, "date", None)
        if hasattr(date_val, "isoformat"):
            date_val = date_val.isoformat()

        # Metrics
        reply_count = getattr(tweet, "replyCount", None)
        retweet_count = getattr(tweet, "retweetCount", None)
        like_count = getattr(tweet, "likeCount", None)

        url = getattr(tweet, "url", "")
        content = getattr(tweet, "rawContent", None) or getattr(tweet, "content", "")

        rows.append(
            {
                "date": date_val,
                "content": content,
                "username": username,
                "name": name,
                "replyCount": reply_count,
                "retweetCount": retweet_count,
                "likeCount": like_count,
                "url": url,
            }
        )

    df = pd.DataFrame(rows)
    return df

def fetch_twitter_mentions_nitter(
    query: str = "Matiks",
    limit: int = 50,
    *,
    base_urls: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Secondary no-key mode: scrape a Nitter instance (Twitter/X alternative frontend).

    Reality check:
    - Nitter instances can be down / blocked / rate-limited.
    - HTML structure can change.

    Output schema matches the demo.
    """
    try:
        import requests
        from bs4 import BeautifulSoup
    except Exception as e:
        raise ImportError(f"Missing dependency for nitter scrape: {e}") from e

    bases = base_urls or [
        "https://nitter.net",
        "https://nitter.poast.org",
        "https://nitter.privacydev.net",
    ]
    headers = {"User-Agent": "Mozilla/5.0 (compatible; MatiksMonitor/1.0)"}

    all_rows: List[Dict[str, object]] = []
    for base in bases:
        try:
            url = f"{base.rstrip('/')}/search"
            r = requests.get(url, params={"f": "tweets", "q": query}, headers=headers, timeout=25)
            if r.status_code != 200 or not r.text:
                continue

            soup = BeautifulSoup(r.text, "html.parser")
            items = soup.select(".timeline-item")
            if not items:
                continue

            for item in items:
                # Content

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
            "content": "@Matiks has completely changed how I practice mental math. Used to hate numbers, now I do 10-minute duels daily. Highly recommend! ",
            "username": "mathgeek99",
            "name": "Math Geek",
            "date": "2026-01-30T09:15:00Z",
            "replyCount": 5,
            "retweetCount": 1,
            "likeCount": 18,
            "url": "https://twitter.com/mathgeek99/status/1234567891"
        },
        {
            "content": "The gamification in @Matiks is brilliant. My kids actually ask to practice math now. That's a win! ",
            "username": "growthhacker",
            "name": "Growth Hacker",
            "date": "2026-01-28T16:45:00Z",
            "replyCount": 1,
            "retweetCount": 0,
            "likeCount": 3,
            "url": "https://twitter.com/growthhacker/status/1234567892"
        },
        {
            "content": "Comparing @Matiks vs other math apps - the speed and accuracy focus is unmatched. The 1-minute duels are addictive! ",
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
    os.makedirs("output", exist_ok=True)
    tweets.to_csv("output/twitter_mentions.csv", index=False)

    html_path = "output/twitter_mentions.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write("<meta charset='utf-8'><h1>Twitter/X mentions – Matiks</h1>")
        f.write(tweets.to_html(index=False, classes="table", border=1))
        f.write(df.to_html(index=False, classes="table", border=1))

    print("Saved Twitter results to output/twitter_mentions.csv")
    print("Open output/twitter_mentions.html in a browser to view as a table.")
