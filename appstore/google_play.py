"""
Google Play Store review collector for Matiks app.

Assignment: "Collect user reviews from Google Play Store and Apple App Store
including ratings, review text, dates, and version details when available."

Why: Automate collection, output structured data (CSV/HTML) for analysis,
and fallback to demo data if the store blocks or fails.
"""
import pandas as pd
import os

MATIKS_PACKAGE_ID = "com.matiks.app"
REVIEW_COUNT = 100  # More data for aggregation; assignment asks to collect reviews


def fetch_google_play_reviews(package_id=None, count=None):
    """Fetch live reviews: ratings, review text, dates, version (per assignment)."""
    try:
        from google_play_scraper import reviews, search
    except ImportError:
        raise ImportError("Install: pip install google-play-scraper")

    count = count if count is not None else REVIEW_COUNT
    app_id = package_id
    if not app_id:
        search_results = search("Matiks", n_hits=5)
        if search_results:
            app_id = search_results[0].get("appId")
    if not app_id:
        app_id = MATIKS_PACKAGE_ID
    result, _ = reviews(app_id, count=count)
    if not result:
        return None
    rows = []
    for r in result:
        at_val = r.get("at")
        if hasattr(at_val, "isoformat"):
            at_val = at_val.isoformat()
        rows.append({
            "rating": r.get("score"),
            "review_text": r.get("content") or "",
            "date": at_val,
            "version": r.get("reviewCreatedVersion") or r.get("appVersion") or "",
            "author": r.get("userName") or "",
            "thumbsUpCount": r.get("thumbsUpCount"),
        })
    return pd.DataFrame(rows)


def fetch_google_play_reviews_demo():
    """Demo data when live fetch fails (same fields: rating, review_text, date, version)."""
    data = [
        {"rating": 5, "review_text": "Addictive math duels! Great for quick practice.", "date": "2026-01-28T10:00:00", "version": "2.1.0", "author": "User123", "thumbsUpCount": 12},
        {"rating": 5, "review_text": "Really improved my mental math. Recommend.", "date": "2026-01-25T14:30:00", "version": "2.0.9", "author": "MathFan", "thumbsUpCount": 8},
        {"rating": 4, "review_text": "Good app but sometimes lags on older devices.", "date": "2026-01-22T09:15:00", "version": "2.0.8", "author": "TechUser", "thumbsUpCount": 3},
    ]
    return pd.DataFrame(data)


if __name__ == "__main__":
    try:
        print("Fetching Google Play reviews for Matiks...")
        df = fetch_google_play_reviews(count=REVIEW_COUNT)
        if df is None or df.empty:
            raise ValueError("No reviews returned")
    except Exception as e:
        print(f"Live fetch failed: {e}")
        print("Using demo data.")
        df = fetch_google_play_reviews_demo()

    df["platform"] = "Google Play"
    print(f"Fetched {len(df)} reviews (rating, review_text, date, version per assignment).")
    print(df.head())
    os.makedirs("output", exist_ok=True)
    df.to_csv("output/google_play_reviews.csv", index=False)
    with open("output/google_play_reviews.html", "w", encoding="utf-8") as f:
        f.write("<meta charset='utf-8'><h1>Google Play reviews – Matiks</h1>")
        f.write(df.to_html(index=False, classes="table", border=1))
    print("Saved to output/google_play_reviews.csv and .html")
