# API Setup Guide for Matiks Social Media Monitor

This document explains how to configure API keys for real-time social media data collection.

## Overview

The Matiks Social Media Monitor supports both API-based data collection and demo data fallback:

- **Twitter/X**: Uses Twitter API v2 with Bearer Token authentication
- **LinkedIn**: Uses LinkedIn API v2 with Access Token authentication
- **Reddit**: Uses Reddit API (already configured in reddit.py)
- **App Stores**: Uses official RSS feeds (no API key needed)

## Environment Variables

### Twitter/X API

1. **Get Twitter API v2 Access**:
   - Apply for Twitter Developer Account: https://developer.twitter.com/
   - Create a new Project and App
   - Generate Bearer Token from your App's "Keys and tokens" section

2. **Set Environment Variable**:
   ```bash
   # Windows (PowerShell)
   $env:TWITTER_BEARER_TOKEN = "your_bearer_token_here"
   
   # Windows (Command Prompt)
   set TWITTER_BEARER_TOKEN=your_bearer_token_here
   
   # Linux/Mac
   export TWITTER_BEARER_TOKEN="your_bearer_token_here"
   ```

### LinkedIn API

1. **Get LinkedIn API Access**:
   - Apply for LinkedIn Partner Program: https://partner.linkedin.com/
   - Or request developer access through LinkedIn's developer portal
   - Generate Access Token with appropriate permissions

2. **Set Environment Variable**:
   ```bash
   # Windows (PowerShell)
   $env:LINKEDIN_ACCESS_TOKEN = "your_access_token_here"
   
   # Windows (Command Prompt)
   set LINKEDIN_ACCESS_TOKEN=your_access_token_here
   
   # Linux/Mac
   export LINKEDIN_ACCESS_TOKEN="your_access_token_here"
   ```

### Reddit API (Optional)

Reddit API is already configured, but you can add your own credentials:

```bash
# Windows (PowerShell)
$env:REDDIT_CLIENT_ID = "your_client_id"
$env:REDDIT_CLIENT_SECRET = "your_client_secret"
$env:REDDIT_USER_AGENT = "MatiksMonitor/1.0"

# Linux/Mac
export REDDIT_CLIENT_ID="your_client_id"
export REDDIT_CLIENT_SECRET="your_client_secret"
export REDDIT_USER_AGENT="MatiksMonitor/1.0"
```

## Usage Examples

### With API Keys

```python
from social.twitter_fixed import fetch_twitter_mentions
from social.linkedin_fixed import fetch_linkedin_mentions

# Fetch real Twitter data
tweets = fetch_twitter_mentions("Matiks", limit=50)
print(f"Fetched {len(tweets)} real tweets")

# Fetch real LinkedIn data
posts = fetch_linkedin_mentions("Matiks", limit=50)
print(f"Fetched {len(posts)} real LinkedIn posts")
```

### Without API Keys (Demo Mode)

```python
# Same code works without API keys - automatically falls back to demo data
tweets = fetch_twitter_mentions("Matiks", limit=50)
posts = fetch_linkedin_mentions("Matiks", limit=50)

print("Running in demo mode - using sample data")
```

### Passing API Keys Directly

```python
# Pass API keys directly instead of using environment variables
tweets = fetch_twitter_mentions("Matiks", limit=50, bearer_token="your_token")
posts = fetch_linkedin_mentions("Matiks", limit=50, access_token="your_token")
```

## Integration with Aggregator

Update the aggregator.py to use the API-ready modules:

```python
# Replace these imports:
from social.twitter import fetch_twitter_mentions_demo
from social.linkedin import fetch_linkedin_mentions_demo

# With these:
from social.twitter_fixed import fetch_twitter_mentions
from social.linkedin_fixed import fetch_linkedin_mentions

# Update function calls:
twitter_df = fetch_twitter_mentions(query=query, limit=limit)
linkedin_df = fetch_linkedin_mentions(query=query, limit=limit)
```

## Benefits for Presentations

1. **Production-Ready Code**: Shows you understand API integration patterns
2. **Error Handling**: Demonstrates proper fallback mechanisms
3. **Environment Variables**: Industry standard for credential management
4. **Modular Design**: Clean separation between API and demo data
5. **Scalability**: Easy to extend with additional social platforms

## API Rate Limits

- **Twitter API v2**: 300 requests per 15 minutes (free tier)
- **LinkedIn API**: Varies by access level
- **Reddit API**: 60 requests per minute (authenticated)

The code includes proper error handling and will gracefully fall back to demo data if rate limits are exceeded.

## Security Notes

- Never commit API keys to version control
- Use environment variables or secure credential storage
- Rotate API keys regularly
- Monitor API usage to avoid unexpected charges
