import feedparser
import time
from datetime import datetime, timedelta, timezone

def fetch_latest_papers(rss_url, days_to_look_back=1, max_entries=50):
    """
    Fetches an RSS feed and filters for articles published within a specified time window.
    Default is set to 7 days for testing purposes.
    """
    print(f"Fetching RSS feed: {rss_url}")
    feed = feedparser.parse(rss_url)
    
    if feed.bozo:
        print("Fetch failed. Please check your network connection or the feed URL.")
        return []

    papers = []
    
    now_utc = datetime.now(timezone.utc)
    # * Changed window to dynamic days for easier testing
    past_time_utc = now_utc - timedelta(days=days_to_look_back) 
    
    print(f"Filtering time window: {past_time_utc.strftime('%Y-%m-%d %H:%M:%S')} UTC to {now_utc.strftime('%Y-%m-%d %H:%M:%S')} UTC")

    for entry in feed.entries[:max_entries]:
        # * Smart time parsing: try 'published_parsed' first, then 'updated_parsed'
        time_struct = getattr(entry, 'published_parsed', None) or getattr(entry, 'updated_parsed', None)
        
        if time_struct:
            published_time = datetime.fromtimestamp(time.mktime(time_struct), timezone.utc)
            
            if past_time_utc <= published_time <= now_utc:
                
                abstract = ""
                if hasattr(entry, 'summary'):
                    abstract = entry.summary
                elif hasattr(entry, 'description'):
                    abstract = entry.description
                    
                paper_info = {
                    "title": entry.title,
                    "link": entry.link,
                    "published": published_time.strftime('%Y-%m-%d %H:%M:%S'),
                    "abstract": abstract
                }
                papers.append(paper_info)
        else:
            print(f"Article '{entry.title}' lacks any standard timestamp, skipping.")
        
    print(f"Filtering complete. Found {len(papers)} recent articles.")
    return papers
