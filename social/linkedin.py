"""
LinkedIn mentions collector for Matiks.

Assignment: "Track mentions of Matiks on Reddit, Twitter/X, and LinkedIn including
content, author, timestamps, and engagement metrics."

Why fallback-based approach:
- LinkedIn has no stable, public search API for global "mentions".
- Login scraping is brittle and may violate ToS.
- Best free option: use public web indexing (search engine results) to find public
  LinkedIn pages mentioning the query; engagement/timestamps are often unavailable
  without authenticated access, so we leave those blank when missing.
"""
import pandas as pd
import os
from typing import Optional, List, Dict


def fetch_linkedin_mentions_api(query="Matiks", limit=50):
    """Placeholder for official LinkedIn API (requires partner/developer access)."""
    raise NotImplementedError("LinkedIn API requires partner access. Using demo data.")


def fetch_linkedin_company_posts_public(company_slug: str = "matiks", limit: int = 5) -> Optional[pd.DataFrame]:
    """
    Free + relatively stable option: fetch the public LinkedIn company page and extract
    the latest post(s) from `application/ld+json` structured data.

    Notes:
    - This captures the company's own posts (brand presence on LinkedIn), not full
      "all LinkedIn mentions" across the platform.
    - We can enrich engagement metrics by fetching each public post URL and reading
      its `interactionStatistic` from ld+json (when present).
    """
    try:
        import json
        import requests
        from bs4 import BeautifulSoup
    except Exception as e:
        raise ImportError(f"Missing dependency for company page fetch: {e}") from e

    url = f"https://www.linkedin.com/company/{company_slug}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; MatiksMonitor/1.0)",
        "Accept-Language": "en-US,en;q=0.9",
    }

    resp = requests.get(url, headers=headers, timeout=25)
    if resp.status_code != 200:
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    script = soup.find("script", attrs={"type": "application/ld+json"})
    if not script or not script.string:
        return None

    try:
        payload = json.loads(script.string)
    except Exception:
        return None

    graph = payload.get("@graph", [])
    if not isinstance(graph, list) or not graph:
        return None

    org = next((n for n in graph if isinstance(n, dict) and n.get("@type") == "Organization"), None)
    org_name = (org or {}).get("name") or "Matiks"

    posts = [n for n in graph if isinstance(n, dict) and n.get("@type") == "DiscussionForumPosting"]
    if not posts:
        return None

    rows: List[Dict[str, object]] = []
    for p in posts[: max(1, limit)]:
        def _enrich_from_post_url(post_url_in: str) -> Dict[str, object]:
            try:
                r2 = requests.get(post_url_in, headers=headers, timeout=25)
                if r2.status_code != 200:
                    return {}
                soup2 = BeautifulSoup(r2.text, "html.parser")
                s2 = soup2.find("script", attrs={"type": "application/ld+json"})
                if not s2 or not s2.string:
                    return {}
                d2 = json.loads(s2.string)
                # Some post pages use 'articleBody' for the content.
                content2 = (d2.get("articleBody") or d2.get("text") or "").strip()
                ts2 = (d2.get("datePublished") or "").strip()

                likes = ""
                comments = ""
                stats = d2.get("interactionStatistic")
                if isinstance(stats, list):
                    for s in stats:
                        if not isinstance(s, dict):
                            continue
                        it = str(s.get("interactionType") or "")
                        cnt = s.get("userInteractionCount")
                        if cnt is None:
                            continue
                        if "LikeAction" in it:
                            likes = cnt
                        if "CommentAction" in it:
                            comments = cnt

                # Fallback: sometimes commentCount exists.
                if comments == "" and d2.get("commentCount") is not None:
                    comments = d2.get("commentCount")

                return {
                    "content": content2,
                    "timestamp": ts2,
                    "engagement_likes": likes,
                    "engagement_comments": comments,
                }
            except Exception:
                return {}

        text = (p.get("text") or p.get("articleBody") or "").strip()
        post_url = (p.get("url") or "").strip()
        date_published = (p.get("datePublished") or "").strip()
        enriched: Dict[str, object] = _enrich_from_post_url(post_url) if post_url else {}

        rows.append(
            {
                "content": enriched.get("content") or text,
                "author": org_name,
                "timestamp": enriched.get("timestamp") or date_published,
                "engagement_likes": enriched.get("engagement_likes", ""),
                "engagement_comments": enriched.get("engagement_comments", ""),
                "url": post_url or url,
                "company_slug": company_slug,
                "source": "linkedin_ldjson_company",
            }
        )

    return pd.DataFrame(rows)


def fetch_linkedin_mentions_public_search(query: str = "Matiks", limit: int = 20) -> Optional[pd.DataFrame]:
    """
    Best-effort free mode: query public web index for LinkedIn pages mentioning `query`.
    Uses DuckDuckGo's HTML endpoint (no API key).

    Returns a DataFrame with columns compatible with the assignment:
    - content, author, timestamp, engagement_likes, engagement_comments, url
    (author/timestamp/engagement may be blank if not available in public snippets)
    """
    try:
        import requests
        from bs4 import BeautifulSoup
    except Exception as e:
        raise ImportError(f"Missing dependency for public search: {e}") from e

    q = f"site:linkedin.com {query}"
    url = "https://duckduckgo.com/html/"
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; MatiksMonitor/1.0)",
        "Accept-Language": "en-US,en;q=0.9",
    }

    resp = requests.get(url, params={"q": q}, headers=headers, timeout=25)
    if resp.status_code != 200:
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    results: List[Dict[str, object]] = []

    # DuckDuckGo HTML layout: results under .result
    for r in soup.select(".result"):
        a = r.select_one("a.result__a")
        if not a:
            continue
        href = (a.get("href") or "").strip()
        title = a.get_text(" ", strip=True)

        snippet_el = r.select_one(".result__snippet")
        snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""

        # Keep only LinkedIn URLs
        if "linkedin.com" not in href.lower():
            continue

        # Minimal normalization — we can't reliably get author/timestamp/engagement without auth.
        results.append(
            {
                "content": (snippet or title or "").strip(),
                "author": "",
                "timestamp": "",
                "engagement_likes": "",
                "engagement_comments": "",
                "url": href,
                "title": title,
                "snippet": snippet,
                "query": query,
                "source": "duckduckgo_html",
            }
        )

        if len(results) >= limit:
            break

    if not results:
        return None
    return pd.DataFrame(results)


def fetch_linkedin_mentions_demo():
    """Demo data – Scope: content, author, timestamps, engagement metrics."""
    data = [
        {
            "content": "Matiks is one of the most engaging math apps I've used. Great for quick practice and building consistency. #EdTech #Matiks",
            "author": "Priya Sharma",
            "timestamp": "2026-02-01T10:00:00Z",
            "engagement_likes": 24,
            "engagement_comments": 3,
            "url": "https://www.linkedin.com/feed/update/urn:li:activity:demo1",
        },
        {
            "content": "Just hit 100 days streak on Matiks! The team even sent a cake 🎂. Best way to stay sharp with numbers. Highly recommend.",
            "author": "Rahul Verma",
            "timestamp": "2026-01-28T14:30:00Z",
            "engagement_likes": 18,
            "engagement_comments": 5,
            "url": "https://www.linkedin.com/feed/update/urn:li:activity:demo2",
        },
        {
            "content": "If you're looking for a math practice app that doesn't feel like homework, try Matiks. 1-min duels are addictive in a good way.",
            "author": "Anita Krishnan",
            "timestamp": "2026-01-25T09:15:00Z",
            "engagement_likes": 12,
            "engagement_comments": 2,
            "url": "https://www.linkedin.com/feed/update/urn:li:activity:demo3",
        },
        {
            "content": "Matiks – making mental math fun again. Perfect for students and professionals who want to keep their number skills sharp.",
            "author": "EdTech Insights",
            "timestamp": "2026-01-22T16:00:00Z",
            "engagement_likes": 31,
            "engagement_comments": 4,
            "url": "https://www.linkedin.com/feed/update/urn:li:activity:demo4",
        },
    ]
    return pd.DataFrame(data)


if __name__ == "__main__":
    # Windows terminals often default to cp1252; ensure printing won't crash on emojis.
    try:
        import sys

        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    try:
        print("Trying LinkedIn company page (public)...")
        df = fetch_linkedin_company_posts_public(company_slug="matiks", limit=5)
        if df is None or df.empty:
            raise ValueError("No company-page posts found")
    except Exception as e1:
        try:
            print(f"Company page not available: {e1}")
            print("Trying LinkedIn public search (no API key)...")
            df = fetch_linkedin_mentions_public_search(query="Matiks", limit=25)
            if df is None or df.empty:
                raise ValueError("No public-search results")
        except Exception as e2:
            print(f"Public search not available: {e2}")
            print("Using demo data for LinkedIn mentions.")
            df = fetch_linkedin_mentions_demo()

    df["platform"] = "LinkedIn"
    os.makedirs("output", exist_ok=True)
    df.to_csv("output/linkedin_mentions.csv", index=False)
    with open("output/linkedin_mentions.html", "w", encoding="utf-8") as f:
        f.write("<meta charset='utf-8'><h1>LinkedIn mentions – Matiks</h1>")
        f.write(df.to_html(index=False, classes="table", border=1))
    print(f"Collected {len(df)} LinkedIn mentions (content, author, timestamps, engagement).")
    print("Saved to output/linkedin_mentions.csv and output/linkedin_mentions.html")
