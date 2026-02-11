
import feedparser
import trafilatura
import requests
import time
import re
import base64
from urllib.parse import quote_plus

# ── Strategy 1: Decode Google News redirect URLs ──────────────────────
def _decode_google_news_url(source_url):
    """
    Google News RSS links use an encoded redirect.
    Try to decode the real article URL from the encoded path.
    """
    try:
        # Google News URLs look like:
        # https://news.google.com/rss/articles/CBMi...
        # The part after /articles/ is a base64-encoded protobuf
        # containing the real URL
        if "/articles/" in source_url:
            encoded = source_url.split("/articles/")[-1].split("?")[0]
            # Try standard base64 decode
            for padding in ["", "=", "==", "==="]:
                try:
                    decoded = base64.urlsafe_b64decode(encoded + padding).decode("latin-1")
                    # Look for http URLs in the decoded blob
                    urls = re.findall(r'https?://[^\s"<>\x00-\x1f]+', decoded)
                    for url in urls:
                        if "google.com" not in url:
                            return url
                except Exception:
                    continue
    except Exception:
        pass
    return None


def resolve_url(url):
    """Follow HTTP redirects to get the final URL."""
    try:
        response = requests.get(
            url,
            allow_redirects=True,
            timeout=15,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )
        return response.url
    except Exception as e:
        print(f"Error resolving URL {url}: {e}")
        return url


def _extract_article_text(url):
    """Extract article text from a URL using trafilatura."""
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded)
            if text and len(text) > 200:
                return text
    except Exception as e:
        print(f"Extraction error for {url}: {e}")
    return None


# ── Strategy 2: Use Google News RSS (primary) ─────────────────────────
def fetch_from_google_news(topic):
    """Fetch news from Google News RSS feed with proper URL decoding."""
    rss_url = f"https://news.google.com/rss/search?q={quote_plus(topic)}&hl=en-US&gl=US&ceid=US:en"
    print(f"Fetching Google News RSS for '{topic}'...")
    feed = feedparser.parse(rss_url)

    if not feed.entries:
        print("No RSS entries found.")
        return None

    print(f"Found {len(feed.entries)} entries, trying top 10...")

    for entry in feed.entries[:10]:
        title = entry.get("title", "Unknown")
        link = entry.get("link", "")
        print(f"  Trying: {title[:60]}...")

        # Method A: Decode the Google redirect URL
        decoded_url = _decode_google_news_url(link)
        if decoded_url:
            print(f"    Decoded URL: {decoded_url[:80]}...")
            text = _extract_article_text(decoded_url)
            if text:
                return {"title": title, "link": decoded_url, "content": text}

        # Method B: Follow redirects with full GET
        resolved = resolve_url(link)
        if resolved and "google.com" not in resolved:
            print(f"    Resolved URL: {resolved[:80]}...")
            text = _extract_article_text(resolved)
            if text:
                return {"title": title, "link": resolved, "content": text}

    print("All Google News entries failed.")
    return None


# ── Strategy 3: Use Bing News RSS (fallback) ──────────────────────────
def fetch_from_bing_news(topic):
    """Fallback: Bing News RSS - simpler redirect structure."""
    rss_url = f"https://www.bing.com/news/search?q={quote_plus(topic)}&format=RSS"
    print(f"Trying Bing News RSS for '{topic}'...")

    try:
        feed = feedparser.parse(rss_url)
        if not feed.entries:
            print("No Bing entries.")
            return None

        for entry in feed.entries[:5]:
            title = entry.get("title", "Unknown")
            link = entry.get("link", "")
            print(f"  Trying Bing: {title[:60]}...")

            text = _extract_article_text(link)
            if text:
                return {"title": title, "link": link, "content": text}
    except Exception as e:
        print(f"Bing RSS failed: {e}")
    return None


# ── Strategy 4: Use a free news API (second fallback) ─────────────────
def fetch_from_newsdata(topic):
    """Fallback: Use the free GNews-like approach via web scraping."""
    try:
        url = f"https://newsapi.in/newsapi/news?q={quote_plus(topic)}"
        # Alternative: scrape a news aggregator page
        downloaded = trafilatura.fetch_url(f"https://www.google.com/search?q={quote_plus(topic)}+news&tbm=nws")
        if downloaded:
            text = trafilatura.extract(downloaded)
            if text and len(text) > 100:
                title = f"Latest: {topic}"
                lines = text.split("\n")
                if lines:
                    title = lines[0][:100]
                return {"title": title, "link": "", "content": text}
    except Exception:
        pass
    return None


# ── Main Entry Point ──────────────────────────────────────────────────
def fetch_news_topic(topic="AI"):
    """
    Fetch trending news for a topic using multiple strategies.
    Returns: {"title": str, "link": str, "content": str} or None
    """
    # Strategy 1: Google News RSS (most comprehensive)
    result = fetch_from_google_news(topic)
    if result:
        return result

    # Strategy 2: Bing News RSS (simpler redirects)
    result = fetch_from_bing_news(topic)
    if result:
        return result

    # Strategy 3: Google News search scrape
    result = fetch_from_newsdata(topic)
    if result:
        return result

    # Strategy 4: Generate minimal content so the pipeline doesn't break
    print(f"All news sources failed. Using topic description as content.")
    return {
        "title": f"Trending: {topic}",
        "link": "",
        "content": f"A comprehensive overview and latest developments about {topic}. "
                   f"This covers the most recent trends, breakthroughs, and expert opinions "
                   f"on {topic} that are making headlines today. The field of {topic} continues "
                   f"to evolve rapidly, with new innovations emerging regularly that promise to "
                   f"transform how we live and work."
    }
