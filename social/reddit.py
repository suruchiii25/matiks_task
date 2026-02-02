import requests
import pandas as pd
import os

def fetch_reddit_mentions_json(query="Matiks", limit=10):
    url = f"https://www.reddit.com/search.json"
    params = {"q": query, "limit": limit}
    headers = {"User-Agent": "brand-monitor-bot/0.1 by intern"}
    response = requests.get(url, headers=headers, params=params, timeout=10)
    response.raise_for_status()
    posts = response.json()["data"]["children"]
    results = []
    for post in posts:
        data = post["data"]
        results.append({
            "title": data["title"],
            "content": data.get("selftext", ""),
            "author": data["author"],
            "created_utc": data["created_utc"],
            "score": data["score"],
            "url": f"https://reddit.com{data['permalink']}",
            "num_comments": data["num_comments"],
        })
    return pd.DataFrame(results)

def fetch_reddit_mentions_demo():
    # Demo fallback, in case /search.json fails
    data = [
        {
            "title": "Matiks launches new feature",
            "author": "startupfan2026",
            "created_utc": 1705516800,
            "score": 42,
            "url": "https://reddit.com/r/startups/comments/abc123",
            "num_comments": 11
        }
    ]
    return pd.DataFrame(data)

if __name__ == "__main__":
    try:
        df = fetch_reddit_mentions_json()
    except Exception as e:
        print(f"Reddit JSON endpoint failed: {e}")
        print("Using fallback demo data for pipeline.")
        df = fetch_reddit_mentions_demo()
    print(df.head())
    os.makedirs("output", exist_ok=True)
    df.to_csv("output/reddit_mentions.csv", index=False)
    html_path = "output/reddit_mentions.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write("<meta charset='utf-8'><h1>Reddit mentions – Matiks</h1>")
        f.write(df.to_html(index=False, classes="table", border=1))

    print("Saved Reddit results to output/reddit_mentions.csv")
    print("Open output/reddit_mentions.html in a browser to view as a table.")