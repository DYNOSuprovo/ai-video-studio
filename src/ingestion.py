
import feedparser
import trafilatura
import requests
import time

def resolve_url(url):
    try:
        response = requests.head(url, allow_redirects=True, timeout=10)
        return response.url
    except Exception as e:
        print(f"Error resolving URL {url}: {e}")
        return url

def fetch_news_topic(topic="AI"):
    # Google News RSS for specific topic
    rss_url = f"https://news.google.com/rss/search?q={topic}&hl=en-US&gl=US&ceid=US:en"
    print(f"Fetching RSS for {topic}...")
    feed = feedparser.parse(rss_url)
    
    if not feed.entries:
        return None
        
    # Try top 3 entries
    for entry in feed.entries[:3]:
        print(f"Processing: {entry.title}")
        resolved = resolve_url(entry.link)
        
        # Skip Google loopbacks if resolution fails
        if "google.com" in resolved and "articles" not in resolved: 
             continue
             
        downloaded = trafilatura.fetch_url(resolved)
        if downloaded:
            text = trafilatura.extract(downloaded)
            if text and len(text) > 200:
                return {
                    "title": entry.title,
                    "link": resolved,
                    "content": text
                }
    
    return None
