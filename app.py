import requests
from bs4 import BeautifulSoup
from newspaper import Article
import asyncio
import re
import xml.etree.ElementTree as ET

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# ---------- GOOGLE NEWS ----------
def scrape_google_news(keyword, max_articles=10):
    query = keyword.replace(" ", "+")
    url = f"https://news.google.com/rss/search?q={query}&hl=id&gl=ID&ceid=ID:id"
    articles = []
    try:
        resp = requests.get(url, timeout=10, headers=HEADERS)
        soup = BeautifulSoup(resp.content, features="xml")
        items = soup.find_all("item")[:max_articles]
        for item in items:
            title = item.title.text
            link = item.link.text
            pub_date = item.pubDate.text if item.pubDate else None
            try:
                article = Article(link, language='id')
                article.download()
                article.parse()
                text = article.text
                authors = article.authors
            except:
                text = ""
                authors = []
            articles.append({
                "source": "Google News",
                "username": authors[0] if authors else "unknown",
                "text": text if text else title,
                "title": title,
                "url": link,
                "timestamp": pub_date,
                "platform": "news"
            })
    except Exception as e:
        print(f"Error scraping news: {e}")
    return articles


# ---------- TWITTER (FALLBACK: NITTER RSS) ----------
def scrape_twitter_via_nitter_rss(keyword, max_tweets=30):
    """
    Mengambil tweet dari Nitter RSS feed.
    URL RSS: https://nitter.net/search/rss?q=<keyword>
    """
    query = requests.utils.quote(keyword)
    rss_url = f"https://nitter.net/search/rss?q={query}"
    tweets = []
    try:
        resp = requests.get(rss_url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            print(f"Nitter RSS status code: {resp.status_code}")
            return []
        # Parse XML
        root = ET.fromstring(resp.content)
        items = root.findall(".//item")[:max_tweets]
        for item in items:
            title = item.find("title").text if item.find("title") is not None else ""
            link = item.find("link").text if item.find("link") is not None else ""
            description = item.find("description").text if item.find("description") is not None else ""
            pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
            # Username dari title: "username: text"
            if ":" in title:
                username, text = title.split(":", 1)
                username = username.strip()
                text = text.strip()
            else:
                username = "unknown"
                text = title
            # Bersihkan tag HTML di description
            text = BeautifulSoup(text, "html.parser").get_text() if text else description
            tweets.append({
                "source": "Twitter",
                "username": username,
                "text": text,
                "like_count": 0,
                "retweet_count": 0,
                "timestamp": pub_date,
                "url": link,
                "platform": "twitter"
            })
    except Exception as e:
        print(f"Error scraping Nitter RSS: {e}")
    return tweets


def scrape_twitter(keyword, max_tweets=30):
    # 1. Coba pakai twikit
    try:
        from twikit import Client
        async def _search():
            client = Client(language='id')
            client.session.headers.update(HEADERS)
            return await client.search_tweet(keyword, product='Top', count=max_tweets)
        results = asyncio.run(_search())
        tweets = []
        for tweet in results:
            tweets.append({
                "source": "Twitter",
                "username": tweet.user.screen_name if hasattr(tweet.user, 'screen_name') else 'unknown',
                "text": tweet.full_text if hasattr(tweet, 'full_text') else tweet.text,
                "like_count": getattr(tweet, 'favorite_count', 0),
                "retweet_count": getattr(tweet, 'retweet_count', 0),
                "timestamp": str(tweet.created_at) if hasattr(tweet, 'created_at') else None,
                "url": f"https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}",
                "platform": "twitter"
            })
        if tweets:
            return tweets
    except Exception as e:
        print(f"Twikit error: {e}")

    # 2. Fallback ke Nitter RSS
    print("Mencoba Nitter RSS...")
    return scrape_twitter_via_nitter_rss(keyword, max_tweets)


# ---------- PLACEHOLDER TIKTOK & INSTAGRAM ----------
def scrape_tiktok_comments(video_url, max_comments=20):
    return []

def scrape_instagram_comments(post_url, max_comments=20):
    return []