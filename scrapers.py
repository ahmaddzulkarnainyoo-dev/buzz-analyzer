import requests
from bs4 import BeautifulSoup
from newspaper import Article
import asyncio
import re

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


# ---------- TWITTER (FALLBACK: NITTER) ----------
def scrape_twitter_via_nitter(keyword, max_tweets=30):
    query = requests.utils.quote(keyword)
    url = f"https://nitter.net/search?f=tweets&q={query}"
    tweets = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, 'html.parser')
        tweet_divs = soup.find_all('div', class_='tweet-body')
        for div in tweet_divs[:max_tweets]:
            content_div = div.find('div', class_='tweet-content')
            if not content_div:
                continue
            text = content_div.get_text(separator=' ', strip=True)
            user_link = div.find('a', class_='username')
            username = user_link.text.strip() if user_link else 'unknown'
            timestamp_span = div.find('span', class_='tweet-date')
            timestamp = timestamp_span.text.strip() if timestamp_span else None
            tweet_link = div.find('a', class_='tweet-link')
            url_tweet = 'https://nitter.net' + tweet_link['href'] if tweet_link else None
            tweets.append({
                "source": "Twitter",
                "username": username,
                "text": text,
                "like_count": 0,
                "retweet_count": 0,
                "timestamp": timestamp,
                "url": url_tweet,
                "platform": "twitter"
            })
    except Exception as e:
        print(f"Error scraping Nitter: {e}")
    return tweets


def scrape_twitter(keyword, max_tweets=30):
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
        return tweets
    except Exception as e:
        print(f"Twikit error: {e}, falling back ke Nitter...")
        return scrape_twitter_via_nitter(keyword, max_tweets)


# ---------- PLACEHOLDER TIKTOK & INSTAGRAM ----------
def scrape_tiktok_comments(video_url, max_comments=20):
    return []

def scrape_instagram_comments(post_url, max_comments=20):
    return []