from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
import string

import pandas as pd

from sentiment import add_sentiment_columns, choose_text_column


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ensure_output_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def setup_logging(output_dir: str, level: str = "INFO") -> logging.Logger:
    ensure_output_dir(output_dir)
    logger = logging.getLogger("matiks_monitor")
    if logger.handlers:
        return logger  # avoid duplicate handlers in schedule loops

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.propagate = False

    fmt = logging.Formatter("%(asctime)sZ %(levelname)s %(message)s")

    ch = logging.StreamHandler(stream=sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    fh = logging.FileHandler(os.path.join(output_dir, "monitor.log"), encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger


def retry(
    fn: Callable[[], pd.DataFrame],
    *,
    attempts: int = 3,
    base_sleep_s: float = 2.0,
    logger: Optional[logging.Logger] = None,
    label: str = "task",
) -> pd.DataFrame:
    last_err: Optional[Exception] = None
    for i in range(1, attempts + 1):
        try:
            return fn()
        except Exception as e:
            last_err = e
            if logger:
                logger.warning("%s failed (attempt %d/%d): %s", label, i, attempts, e)
            if i < attempts:
                time.sleep(base_sleep_s * i)
    raise RuntimeError(f"{label} failed after {attempts} attempts: {last_err}")


def _to_datetime_utc(val: object) -> Optional[pd.Timestamp]:
    if val is None:
        return None
    if isinstance(val, float) and pd.isna(val):
        return None
    try:
        # Unix timestamp (Reddit created_utc)
        if isinstance(val, (int, float)) and float(val) > 10_000:
            return pd.to_datetime(val, unit="s", utc=True, errors="coerce")
        return pd.to_datetime(val, utc=True, errors="coerce")
    except Exception:
        return None


def is_matiks_relevant(text: str) -> bool:
    """
    Filter out irrelevant posts that mention 'matik' but aren't about Matiks app/company.
    Returns True if content is likely about Matiks.
    """
    if not text or pd.isna(text):
        return False
    
    text_lower = str(text).lower()
    
    # Must contain "matiks" as the brand name (not just "matik")
    if "matiks" not in text_lower:
        return False
    
    # Exclude posts that are likely about other topics
    exclude_patterns = [
        "matik tuwing",  # Filipino phrase
        "matik na",      # Filipino 
        "matik ang",     # Filipino
        "matik sa",      # Filipino
        "matik mo",      # Filipino
        "matik ko",      # Filipino
        "mathematics",   # General math, not the app
        "math problem",  # Generic math problems
        "math help",     # Generic math help
    ]
    
    for pattern in exclude_patterns:
        if pattern in text_lower:
            return False
    
    # Include patterns that indicate it's about the app/company
    include_patterns = [
        "matiks app",
        "matiks application", 
        "matiks game",
        "matiks math",
        "matiks review",
        "matiks internship",
        "matiks company",
        "matiks team",
        "play matiks",
        "using matiks",
        "matiks daily",
        "matiks practice",
        "matiks learning",
        "matiks education"
    ]
    
    # If any include pattern is found, it's relevant
    for pattern in include_patterns:
        if pattern in text_lower:
            return True
    
    # If "matiks" appears multiple times, it's more likely relevant
    if text_lower.count("matiks") > 1:
        return True
    
    # If it contains app-related words with "matiks", it's likely relevant
    app_words = ["app", "application", "game", "play", "download", "install", "review", "rating", "update", "version"]
    if any(word in text_lower for word in app_words):
        return True
    
    # If it contains company/education words with "matiks", it's likely relevant  
    company_words = ["company", "team", "internship", "job", "work", "career", "education", "learning", "practice"]
    if any(word in text_lower for word in company_words):
        return True
    
    # Default: if it just mentions "matiks" once without context, exclude it
    return False


def normalize_reddit(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    
    title = df.get("title", "").fillna("").astype(str) if "title" in df.columns else ""
    content = df.get("content", "").fillna("").astype(str) if "content" in df.columns else ""
    text = (title + "\n" + content).str.strip()
    
    # Filter for Matiks-relevant content only
    relevant_mask = text.apply(is_matiks_relevant)
    df = df[relevant_mask]
    text = text[relevant_mask]
    
    if df.empty:
        return pd.DataFrame()
    
    data = {
        "platform": ["Reddit"] * len(df),
        "type": ["social"] * len(df),
        "author": df.get("author", "").fillna("").tolist(),
        "url": df.get("url", "").fillna("").tolist(),
        "timestamp": df.get("created_utc", "").apply(_to_datetime_utc).tolist(),
        "engagement_likes": df.get("score", 0).fillna(0).tolist(),  # Reddit uses score as likes
        "engagement_comments": df.get("num_comments", 0).fillna(0).tolist(),
        "engagement_shares": [0] * len(df),  # Reddit doesn't have shares
        "text": text.tolist(),
        "rating": [""] * len(df),  # Social media doesn't have ratings
        "app_version": [""] * len(df),  # Social media doesn't have app versions
    }
    return pd.DataFrame(data)


def normalize_twitter(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    
    # Filter for Matiks-relevant content only
    text = df.get("content", "").fillna("")
    relevant_mask = text.apply(is_matiks_relevant)
    df = df[relevant_mask]
    
    if df.empty:
        return pd.DataFrame()
    
    data = {
        "platform": ["Twitter/X"] * len(df),
        "type": ["social"] * len(df),
        "author": df.get("username", "").fillna("").tolist(),
        "url": df.get("url", "").fillna("").tolist(),
        "timestamp": df.get("date", "").apply(_to_datetime_utc).tolist(),
        "engagement_likes": df.get("likeCount", 0).fillna(0).tolist(),
        "engagement_comments": df.get("replyCount", 0).fillna(0).tolist(),
        "engagement_shares": df.get("retweetCount", 0).fillna(0).tolist(),
        "text": df.get("content", "").fillna("").tolist(),
        "rating": [""] * len(df),  # Social media doesn't have ratings
        "app_version": [""] * len(df),  # Social media doesn't have app versions
    }
    return pd.DataFrame(data)


def normalize_linkedin(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    
    # Filter for Matiks-relevant content only
    text = df.get("content", "").fillna("")
    relevant_mask = text.apply(is_matiks_relevant)
    df = df[relevant_mask]
    
    if df.empty:
        return pd.DataFrame()
    
    # Clean up URLs - remove DuckDuckGo redirects and keep only clean LinkedIn URLs
    def clean_url(url):
        if pd.isna(url) or not url:
            return ""
        url_str = str(url)
        # If it's a DuckDuckGo redirect (with or without http), replace with a placeholder
        if "duckduckgo.com" in url_str:
            return "https://www.linkedin.com/"
        # If it's already a clean LinkedIn URL, keep it
        if url_str.startswith('https://www.linkedin.com'):
            return url_str
        # For any other long URLs, truncate them
        if len(url_str) > 100:
            return "https://www.linkedin.com/"
        return url_str
    
    cleaned_urls = df.get("url", "").fillna("").apply(clean_url)
    
    data = {
        "platform": ["LinkedIn"] * len(df),
        "type": ["social"] * len(df),
        "author": df.get("author", "").fillna("").tolist(),
        "url": cleaned_urls.tolist(),
        "timestamp": df.get("timestamp", "").apply(_to_datetime_utc).tolist(),
        "engagement_likes": df.get("engagement_likes", 0).fillna(0).tolist(),
        "engagement_comments": df.get("engagement_comments", 0).fillna(0).tolist(),
        "engagement_shares": [0] * len(df),  # LinkedIn doesn't have share counts in posts
        "text": df.get("content", "").fillna("").tolist(),
        "rating": [""] * len(df),  # Social media doesn't have ratings
        "app_version": [""] * len(df),  # Social media doesn't have app versions
    }
    return pd.DataFrame(data)


def normalize_google_play(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    
    data = {
        "platform": ["Google Play"] * len(df),
        "type": ["review"] * len(df),
        "author": df.get("author", "").fillna("").tolist(),
        "url": [""] * len(df),  # App store reviews don't have URLs
        "timestamp": df.get("date", "").apply(_to_datetime_utc).tolist(),
        "engagement_likes": [0] * len(df),  # App store reviews don't have engagement metrics
        "engagement_comments": [0] * len(df),  # App store reviews don't have comment counts
        "engagement_shares": [0] * len(df),  # Reviews can't be shared
        "text": df.get("review_text", "").fillna("").tolist(),
        "rating": df.get("rating", "").fillna("").tolist(),
        "app_version": df.get("version", "").fillna("").tolist(),
    }
    return pd.DataFrame(data)


def normalize_apple_store(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    
    data = {
        "platform": ["Apple App Store"] * len(df),
        "type": ["review"] * len(df),
        "author": df.get("author", "").fillna("").tolist(),
        "url": [""] * len(df),  # App store reviews don't have URLs
        "timestamp": df.get("date", "").apply(_to_datetime_utc).tolist(),
        "engagement_likes": [0] * len(df),  # Apple reviews don't have like counts
        "engagement_comments": [0] * len(df),  # Apple reviews don't have comment counts
        "engagement_shares": [0] * len(df),  # Reviews can't be shared
        "text": df.get("review_text", "").fillna("").tolist(),
        "rating": df.get("rating", "").fillna("").tolist(),
        "app_version": df.get("version", "").fillna("").tolist(),
    }
    return pd.DataFrame(data)


def load_existing_combined(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
    try:
        df = pd.read_csv(path)
    except Exception:
        return pd.DataFrame()
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    return df


def dedupe(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    # Remove rows with missing platform first
    df = df.dropna(subset=["platform"])
    
    # Best-effort stable id; for reviews we often don't have a URL.
    df["__dedupe_key"] = (
        df.get("platform").astype(str)
        + "|"
        + df.get("type").astype(str)
        + "|"
        + df.get("url").fillna("").astype(str)
        + "|"
        + df.get("author").fillna("").astype(str)
        + "|"
        + df.get("timestamp").fillna("").astype(str)
        + "|"
        + df.get("text").fillna("").astype(str).str.slice(0, 200)
    )
    df = df.drop_duplicates(subset=["__dedupe_key"]).drop(columns=["__dedupe_key"])
    return df


def render_dashboard_html(df: pd.DataFrame, out_path: str, *, title: str = "Matiks Monitor") -> None:
    df2 = df.copy()
    if "timestamp" in df2.columns:
        df2["timestamp"] = pd.to_datetime(df2["timestamp"], utc=True, errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S UTC")

    # Keep columns in a predictable order.
    cols = [
        "platform",
        "type",
        "timestamp",
        "author",
        "text",
        "rating",
        "app_version",
        "engagement_likes",
        "engagement_comments",
        "engagement_shares",
        "sentiment_label",
        "sentiment_polarity",
        "url",
    ]
    for c in cols:
        if c not in df2.columns:
            df2[c] = pd.NA
    df2 = df2[cols]

    df2 = df2.rename(
        columns={
            "platform": "Platform",
            "type": "Type",
            "timestamp": "Timestamp (UTC)",
            "author": "Author",
            "text": "Content",
            "rating": "Rating",
            "app_version": "App Version",
            "engagement_likes": "Likes",
            "engagement_comments": "Comments",
            "engagement_shares": "Shares",
            "sentiment_label": "Sentiment",
            "sentiment_polarity": "Sentiment Polarity",
            "url": "URL",
        }
    )

    table_html = df2.to_html(index=False, escape=True, border=0, table_id="data")
    
    # Replace literal \n with <br> for better display
    table_html = table_html.replace('\\n', '<br>')

    html = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{TITLE}</title>
  <style>
    body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 20px; background: #fafafa; color: #111827; }}
    h1 {{ margin: 0 0 10px 0; }}
    .meta {{ color: #555; margin-bottom: 16px; }}
    .controls {{ display: grid; grid-template-columns: repeat(4, minmax(160px, 1fr)); gap: 10px; margin-bottom: 14px; }}
    .control {{ display: flex; flex-direction: column; gap: 6px; }}
    label {{ font-size: 12px; color: #444; }}
    input, select {{ padding: 10px 12px; border: 1px solid #d1d5db; border-radius: 10px; background: #fff; }}
    .card {{ background: #fff; border: 1px solid #eee; border-radius: 14px; padding: 14px; box-shadow: 0 1px 2px rgba(0,0,0,0.04); }}
    .ms {{ position: relative; }}
    .ms-btn {{ width: 100%; text-align: left; padding: 10px 12px; border: 1px solid #d1d5db; border-radius: 10px; background: #fff; cursor: pointer; }}
    .ms-btn:after {{ content: "▾"; float: right; color: #6b7280; }}
    .ms-panel {{ position: absolute; top: calc(100% + 6px); left: 0; right: 0; background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.08); padding: 8px; display: none; z-index: 5; max-height: 260px; overflow: auto; }}
    .ms.open .ms-panel {{ display: block; }}
    .ms-actions {{ display: flex; gap: 8px; padding: 6px; border-bottom: 1px solid #f3f4f6; margin-bottom: 6px; }}
    .btn {{ appearance: none; border: 1px solid #d1d5db; background: #fff; border-radius: 10px; padding: 6px 10px; font-size: 12px; cursor: pointer; }}
    .btn:hover {{ background: #f9fafb; }}
    .ms-opt {{ width: 100%; display: flex; align-items: center; justify-content: flex-start; gap: 10px; padding: 8px 10px; border-radius: 10px; border: none; background: transparent; cursor: pointer; text-align: left; }}
    .ms-opt:hover {{ background: #f9fafb; }}
    .ms-opt .name {{ font-size: 13px; color: #111827; }}
    .ms-opt .mark {{ width: 18px; height: 18px; display: inline-flex; align-items: center; justify-content: center; border-radius: 6px; border: 1px solid #e5e7eb; color: transparent; }}
    .ms-opt.selected .mark {{ background: #111827; border-color: #111827; color: #fff; }}
    table {{ width: 100%; border-collapse: separate; border-spacing: 0; table-layout: fixed; }}
    th, td {{ border-bottom: 1px solid #f1f5f9; padding: 12px 10px; vertical-align: top; word-wrap: break-word; }}
    th {{ position: sticky; top: 0; background: #fff; text-align: left; z-index: 1; font-size: 12px; color: #374151; border-bottom: 1px solid #e5e7eb; }}
    tr:hover td {{ background: #fafafa; }}
    td:nth-child(5) {{ max-width: 560px; white-space: pre-wrap; }}
    /* Fixed column widths for consistent spacing */
    th:nth-child(1), td:nth-child(1) {{ width: 140px; }}  /* Platform */
    th:nth-child(2), td:nth-child(2) {{ width: 90px; }}   /* Type */
    th:nth-child(3), td:nth-child(3) {{ width: 180px; }}  /* Timestamp */
    th:nth-child(4), td:nth-child(4) {{ width: 160px; }}  /* Author */
    th:nth-child(5), td:nth-child(5) {{ width: 400px; }}  /* Content */
    th:nth-child(6), td:nth-child(6) {{ width: 90px; }}   /* Rating */
    th:nth-child(7), td:nth-child(7) {{ width: 120px; }}  /* App Version */
    th:nth-child(8), td:nth-child(8) {{ width: 90px; }}   /* Likes */
    th:nth-child(9), td:nth-child(9) {{ width: 90px; }}   /* Comments */
    th:nth-child(10), td:nth-child(10) {{ width: 90px; }}  /* Shares */
    th:nth-child(11), td:nth-child(11) {{ width: 90px; }}  /* Sentiment */
    th:nth-child(12), td:nth-child(12) {{ width: 150px; }} /* URL */
    a.link {{ color: #2563eb; text-decoration: none; white-space: nowrap; display: inline-block; }}
    a.link:hover {{ text-decoration: underline; }}
    .pill {{ display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 12px; }}
    .pos {{ background: #e8fff0; color: #0b6b2f; }}
    .neu {{ background: #f3f4f6; color: #374151; }}
    .neg {{ background: #ffe8e8; color: #8a1f1f; }}
    .count {{ font-weight: 600; }}
  </style>
</head>
<body>
  <h1>{TITLE}</h1>
  <div class="meta">Last generated: {UTC_NOW} | Rows: <span class="count" id="rowCount">0</span></div>

  <div class="controls card">
    <div class="control">
      <label for="section">Section</label>
      <select id="section">
        <option value="social">Social Media</option>
        <option value="app">App Store Reviews</option>
      </select>
    </div>
    <div class="control" style="grid-column: 1 / -1;">
      <label for="platformBtn">Platforms</label>
      <div class="ms" id="platformMs">
        <button type="button" class="ms-btn" id="platformBtn">All Platforms</button>
        <div class="ms-panel" id="platformPanel"></div>
      </div>
    </div>
    <div class="control">
      <label for="sentiment">Sentiment</label>
      <select id="sentiment">
        <option value="">All</option>
        <option value="positive">Positive</option>
        <option value="neutral">Neutral</option>
        <option value="negative">Negative</option>
      </select>
    </div>
    <div class="control">
      <label for="startDate">Start (YYYY-MM-DD)</label>
      <input id="startDate" type="date" />
    </div>
    <div class="control">
      <label for="endDate">End (YYYY-MM-DD)</label>
      <input id="endDate" type="date" />
    </div>
    <div class="control" style="grid-column: 1 / -1;">
      <label for="q">Keyword search (matches text/author/url)</label>
      <input id="q" placeholder="matiks, bug, crash, love..." />
    </div>
  </div>

  <div class="card" style="overflow:auto;">
    {TABLE_HTML}
  </div>

  <script>
    const table = document.getElementById("data");
    const tbody = table.tBodies[0];
    const rows = Array.from(tbody.rows);

    const sectionSel = document.getElementById("section");
    const platformMs = document.getElementById("platformMs");
    const platformBtn = document.getElementById("platformBtn");
    const platformPanel = document.getElementById("platformPanel");
    const sentimentSel = document.getElementById("sentiment");
    const startDateInp = document.getElementById("startDate");
    const endDateInp = document.getElementById("endDate");
    const qInp = document.getElementById("q");
    const rowCount = document.getElementById("rowCount");

    function esc(s) {{
      return String(s || "").replace(/[&<>"']/g, (c) => ({{
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      }}[c]));
    }}

    function checkboxId(value) {{
      return "p_" + String(value || "").toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "");
    }}

    function addPlatformCheckbox(container, value) {{
      const id = checkboxId(value);
      const label = document.createElement("label");
      label.className = "check";
      label.innerHTML = `<input type="checkbox" name="platform" value="${{esc(value)}}" id="${{esc(id)}}" /> <span>${{esc(value)}}</span>`;
      container.appendChild(label);
    }}

    // Collect platforms by section using the internal type column
    const socialSet = new Set();
    const appSet = new Set();
    for (const r of rows) {{
      const platform = (r.cells[0]?.innerText || "").trim();
      const typ = (r.cells[1]?.innerText || "").trim().toLowerCase();
      if (!platform) continue;
      if (typ === "review") appSet.add(platform);
      else socialSet.add(platform);
    }}

    function renderPlatformCheckboxes() {{
      const mode = sectionSel.value;
      const items = (mode === "app" ? Array.from(appSet) : Array.from(socialSet)).sort();
      selectedPlatforms = new Set();
      platformPanel.innerHTML = "";

      const actions = document.createElement("div");
      actions.className = "ms-actions";
      const btnAll = document.createElement("button");
      btnAll.type = "button";
      btnAll.className = "btn";
      btnAll.textContent = "Select All";
      const btnClear = document.createElement("button");
      btnClear.type = "button";
      btnClear.className = "btn";
      btnClear.textContent = "Clear";
      actions.appendChild(btnAll);
      actions.appendChild(btnClear);
      platformPanel.appendChild(actions);

      function updateBtn() {{
        if (selectedPlatforms.size === 0) {{
          platformBtn.textContent = "All Platforms";
          return;
        }}
        const arr = Array.from(selectedPlatforms);
        platformBtn.textContent = arr.length <= 2 ? arr.join(", ") : `${{arr.length}} Selected`;
      }}

      function renderList() {{
        const existing = platformPanel.querySelectorAll(".ms-opt");
        existing.forEach((n) => n.remove());
        for (const p of items) {{
          const opt = document.createElement("button");
          opt.type = "button";
          opt.className = "ms-opt" + (selectedPlatforms.has(p) ? " selected" : "");
          opt.dataset.value = p;
          opt.innerHTML = `<span class="mark">✓</span><span class="name">${{esc(p)}}</span>`;
          opt.addEventListener("click", () => {{
            if (selectedPlatforms.has(p)) selectedPlatforms.delete(p);
            else selectedPlatforms.add(p);
            renderList();
            updateBtn();
            applyFilters();
          }});
          platformPanel.appendChild(opt);
        }}
      }}

      btnAll.addEventListener("click", () => {{
        selectedPlatforms = new Set(items);
        renderList();
        updateBtn();
        applyFilters();
      }});
      btnClear.addEventListener("click", () => {{
        selectedPlatforms = new Set();
        renderList();
        updateBtn();
        applyFilters();
      }});

      renderList();
      updateBtn();
    }}

    function selectedPlatformsSet() {{
      return new Set(selectedPlatforms);
    }}

    // Render sentiment pills and normalize numeric displays
    for (const r of rows) {{
      const labelCell = r.cells[10];
      const label = (labelCell?.innerText || "").trim();
      if (labelCell) {{
        let cls = "neu";
        if (label === "positive") cls = "pos";
        if (label === "negative") cls = "neg";
        labelCell.innerHTML = label ? `<span class="pill ${{cls}}">${{label}}</span>` : "";
      }}
    }}

    function setColVisible(idx, visible) {{
      const th = table.tHead?.rows?.[0]?.cells?.[idx];
      if (th) th.style.display = visible ? "" : "none";
      for (const r of rows) {{
        const td = r.cells[idx];
        if (td) td.style.display = visible ? "" : "none";
      }}
    }}

    function applySectionColumns() {{
      const mode = sectionSel.value;
      // Hide internal and non-required columns
      setColVisible(1, false);  // type
      setColVisible(11, false); // sentiment_polarity

      if (mode === "app") {{
        setColVisible(12, false);
      }} else {{
        setColVisible(12, true);
      }}

      if (mode === "app") {{
        // App store view: show rating + app version, hide engagement metrics
        setColVisible(5, true);
        setColVisible(6, true);
        setColVisible(7, false);
        setColVisible(8, false);
        setColVisible(9, false);
      }} else {{
        // Social view: show engagement metrics, hide rating + app version
        setColVisible(5, false);
        setColVisible(6, false);
        setColVisible(7, true);
        setColVisible(8, true);
        setColVisible(9, true);
      }}
    }}

    function parseYmd(s) {{
      const t = (s || "").trim();
      if (!t) return null;
      const m = t.match(/^(\\d{{4}})-(\\d{{2}})-(\\d{{2}})$/);
      if (!m) return null;
      return new Date(`${{m[1]}}-${{m[2]}}-${{m[3]}}T00:00:00Z`);
    }}

    function rowTimestampUTC(row) {{
      const ts = (row.cells[2]?.innerText || "").trim();
      // "YYYY-MM-DD HH:MM:SS UTC"
      const m = ts.match(/^(\\d{{4}})-(\\d{{2}})-(\\d{{2}}) (\\d{{2}}):(\\d{{2}}):(\\d{{2}}) UTC$/);
      if (!m) return null;
      return new Date(`${{m[1]}}-${{m[2]}}-${{m[3]}}T${{m[4]}}:${{m[5]}}:${{m[6]}}Z`);
    }}

    function applyFilters() {{
      const selectedPlatforms = selectedPlatformsSet();
      const s = sentimentSel.value;
      const q = (qInp.value || "").toLowerCase().trim();
      const start = parseYmd(startDateInp.value);
      const end = parseYmd(endDateInp.value);
      const mode = sectionSel.value;

      let visible = 0;
      for (const r of rows) {{
        const platform = (r.cells[0]?.innerText || "").trim();
        const typ = (r.cells[1]?.innerText || "").trim().toLowerCase();
        const author = (r.cells[3]?.innerText || "").toLowerCase();
        const text = (r.cells[4]?.innerText || "").toLowerCase();
        const url = (r.cells[12]?.innerText || "").toLowerCase();
        const sentiment = (r.cells[10]?.innerText || "").trim();
        const ts = rowTimestampUTC(r);

        let ok = true;
        if (mode === "app" && typ !== "review") ok = false;
        if (mode === "social" && typ === "review") ok = false;
        if (selectedPlatforms.size > 0 && !selectedPlatforms.has(platform)) ok = false;
        if (s && sentiment.toLowerCase() !== s.toLowerCase()) ok = false;
        if (q && !(author.includes(q) || text.includes(q) || url.includes(q))) ok = false;
        if (start && ts && ts < start) ok = false;
        if (end && ts) {{
          const endExclusive = new Date(end.getTime() + 24*60*60*1000);
          if (ts >= endExclusive) ok = false;
        }}

        r.style.display = ok ? "" : "none";
        if (ok) visible++;
      }}
      rowCount.textContent = visible;
    }}

    sectionSel.addEventListener("change", () => {{
      renderPlatformCheckboxes();
      applySectionColumns();
      applyFilters();
    }});
    sentimentSel.addEventListener("change", applyFilters);
    startDateInp.addEventListener("input", applyFilters);
    endDateInp.addEventListener("input", applyFilters);
    qInp.addEventListener("input", applyFilters);

    platformBtn.addEventListener("click", (e) => {{
      e.preventDefault();
      platformMs.classList.toggle("open");
    }});

    document.addEventListener("click", (e) => {{
      if (!platformMs.contains(e.target)) platformMs.classList.remove("open");
    }});

    let selectedPlatforms = new Set();
    renderPlatformCheckboxes();
    applySectionColumns();

    // Convert URL text to clickable links
    for (const r of rows) {{
      const urlCell = r.cells[12];
      if (!urlCell) continue;
      const raw = (urlCell.innerText || "").trim();
      if (!raw) continue;
      if (raw.startsWith("http://") || raw.startsWith("https://")) {{
        urlCell.innerHTML = `<a class="link" href="${{esc(raw)}}" target="_blank" rel="noopener noreferrer">Open</a>`;
      }}
    }}

    // Debug: log sample rows for verification
    console.log("Sample rows data:");
    for (let i = 0; i < Math.min(3, rows.length); i++) {{
      const r = rows[i];
      console.log({{
        platform: (r.cells[0]?.innerText || "").trim(),
        type: (r.cells[1]?.innerText || "").trim(),
        timestamp: (r.cells[2]?.innerText || "").trim(),
        author: (r.cells[3]?.innerText || "").trim(),
        text: (r.cells[4]?.innerText || "").trim().slice(0, 50),
        sentiment: (r.cells[10]?.innerText || "").trim()
      }});
    }}

    applyFilters();
  </script>
</body>
</html>
"""

    html = html.format(TITLE=title, UTC_NOW=utc_now_iso(), TABLE_HTML=table_html)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)



def main() -> int:
    parser = argparse.ArgumentParser(description="Matiks social + app store monitor (aggregator).")
    parser.add_argument("--query", default=os.getenv("MATIKS_QUERY", "Matiks"))
    parser.add_argument("--output-dir", default=os.getenv("MATIKS_OUTPUT_DIR", "output"))
    parser.add_argument("--limit", type=int, default=int(os.getenv("MATIKS_LIMIT", "50")))
    parser.add_argument("--log-level", default=os.getenv("MATIKS_LOG_LEVEL", "INFO"))
    parser.add_argument("--every-minutes", type=int, default=int(os.getenv("MATIKS_EVERY_MINUTES", "60")))
    parser.add_argument("--once", action="store_true", help="Run one aggregation cycle and exit.")
    args = parser.parse_args()

    logger = setup_logging(args.output_dir, level=args.log_level)
    ensure_output_dir(args.output_dir)

    combined_csv = os.path.join(args.output_dir, "combined.csv")
    dashboard_html = os.path.join(args.output_dir, "dashboard.html")
    status_json = os.path.join(args.output_dir, "last_run.json")

    def run_once(*, query: str, output_dir: str, limit: int, logger: logging.Logger) -> pd.DataFrame:
        from social.reddit import fetch_reddit_mentions_json, fetch_reddit_mentions_demo
        from social.twitter_fixed import fetch_twitter_mentions
        from social.linkedin_fixed import fetch_linkedin_mentions
        from appstore.google_play import fetch_google_play_reviews, fetch_google_play_reviews_demo
        from appstore.apple_store import fetch_apple_store_reviews, fetch_apple_store_reviews_demo

        # Fetch from all sources
        reddit_df = retry(lambda: fetch_reddit_mentions_json(query=query, limit=limit), attempts=3, logger=logger, label="Reddit")
        twitter_df = retry(lambda: fetch_twitter_mentions(query=query, limit=limit), attempts=1, logger=logger, label="Twitter API")
        linkedin_df = retry(lambda: fetch_linkedin_mentions(query=query, limit=limit), attempts=1, logger=logger, label="LinkedIn API")
        google_df = retry(lambda: fetch_google_play_reviews(count=limit), attempts=3, logger=logger, label="Google Play")
        apple_df = retry(lambda: fetch_apple_store_reviews(count=limit), attempts=3, logger=logger, label="Apple Store")

        # Normalize
        reddit_norm = normalize_reddit(reddit_df)
        twitter_norm = normalize_twitter(twitter_df)
        linkedin_norm = normalize_linkedin(linkedin_df)
        google_norm = normalize_google_play(google_df)
        apple_norm = normalize_apple_store(apple_df)

        # Combine
        all_dfs = [reddit_norm, twitter_norm, linkedin_norm, google_norm, apple_norm]
        combined = pd.concat([df for df in all_dfs if not df.empty], ignore_index=True)
        return combined

    def _cycle():
        started = utc_now_iso()
        try:
            new_df = run_once(query=args.query, output_dir=args.output_dir, limit=args.limit, logger=logger)
            existing = load_existing_combined(combined_csv)
            all_df = pd.concat([existing, new_df], ignore_index=True) if not existing.empty else new_df
            all_df["timestamp"] = pd.to_datetime(all_df["timestamp"], utc=True, errors="coerce")
            
            # Add sentiment analysis to ALL data (not just new data)
            text_col = choose_text_column(all_df)
            if text_col:
                all_df = add_sentiment_columns(all_df, text_col=text_col)
            
            all_df = dedupe(all_df)
            all_df = all_df.sort_values(by=["timestamp"], ascending=False, na_position="last")
            
            # Replace all NaN values with appropriate defaults before saving
            all_df = all_df.fillna({
                'url': '',
                'engagement_likes': 0,
                'engagement_comments': 0, 
                'engagement_shares': 0,
                'rating': '',
                'app_version': '',
                'author': '',
                'text': ''
            })

            # Save combined data
            all_df.to_csv(combined_csv, index=False)
            logger.info(f"Saved combined data to {combined_csv} ({len(all_df)} rows)")

            # Update status file
            update_status_file(len(all_df), logger)

            # Render dashboard
            render_dashboard_html(all_df, dashboard_html)
            logger.info(f"Rendered dashboard to {dashboard_html}")

            status = {
                "ok": True,
                "started_at": started,
                "finished_at": utc_now_iso(),
                "rows_total": int(len(all_df)),
                "rows_new": int(len(new_df)),
                "combined_csv": os.path.abspath(combined_csv),
                "dashboard_html": os.path.abspath(dashboard_html),
            }
            with open(status_json, "w", encoding="utf-8") as f:
                json.dump(status, f, indent=2)
            logger.info("Run finished (new=%d, total=%d)", len(new_df), len(all_df))
        except Exception as e:
            status = {
                "ok": False,
                "started_at": started,
                "finished_at": utc_now_iso(),
                "error": str(e),
            }
            with open(status_json, "w", encoding="utf-8") as f:
                json.dump(status, f, indent=2)
            logger.exception("Run failed: %s", e)

    if args.once:
        _cycle()
        return 0

    import schedule

    logger.info("Scheduler started (every %d minutes). Press Ctrl+C to stop.", args.every_minutes)
    schedule.every(args.every_minutes).minutes.do(_cycle)
    _cycle()  # run immediately on start

    while True:
        schedule.run_pending()
        time.sleep(1)


def update_status_file(total_rows, logger):
    """Update the status.json file with current system status"""
    try:
        import json
        from datetime import datetime, timezone, timedelta
        
        status_data = {
            "system_status": "automated",
            "last_update": datetime.now(timezone.utc).isoformat(),
            "next_update": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            "update_frequency": "hourly",
            "automation_method": "GitHub Actions",
            "total_rows": total_rows,
            "data_sources": [
                "Reddit API",
                "Twitter API (demo mode)",
                "LinkedIn API (demo mode)", 
                "Google Play Store RSS",
                "Apple App Store RSS"
            ],
            "deployment": {
                "platform": "Vercel",
                "url": "https://matikstaskaigen.vercel.app/",
                "auto_deploy": True
            },
            "monitoring": {
                "health_checks": "every 6 hours",
                "error_alerts": "GitHub Actions notifications"
            }
        }
        
        with open("status.json", "w", encoding="utf-8") as f:
            json.dump(status_data, f, indent=2)
        
        logger.info(f"Updated status.json - next update: {status_data['next_update']}")
        
    except Exception as e:
        logger.error(f"Failed to update status.json: {e}")


if __name__ == "__main__":
    raise SystemExit(main())

