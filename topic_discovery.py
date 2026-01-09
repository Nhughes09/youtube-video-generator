"""
Topic Discovery Module
Fetches and ranks trending AI/robotics news from Google News RSS and Reddit.
"""

import requests
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import re

from config import CONTENT_CONFIG, API_ENDPOINTS
from utils import setup_logger, handle_errors, generate_id

logger = setup_logger(__name__)


@dataclass
class Topic:
    """Represents a discovered topic."""
    id: str
    title: str
    source: str
    url: str
    published: str
    score: float
    keywords_matched: List[str]
    summary: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)


class TopicDiscovery:
    """
    Discovers trending topics from news sources.
    Uses Google News RSS and Reddit JSON (no authentication needed).
    """
    
    def __init__(self):
        self.keywords = CONTENT_CONFIG["keywords"]
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })
    
    @handle_errors(retry_count=3, retry_delay=2.0, fallback=[])
    def fetch_google_news(self) -> List[Topic]:
        """Fetch topics from Google News RSS feeds."""
        topics = []
        
        for feed_url in CONTENT_CONFIG["rss_feeds"]:
            logger.info(f"Fetching Google News: {feed_url[:50]}...")
            
            feed = feedparser.parse(feed_url)
            
            for entry in feed.entries[:20]:  # Top 20 per feed
                topic = Topic(
                    id=generate_id(entry.get("link", entry.get("title", ""))),
                    title=self._clean_title(entry.get("title", "")),
                    source="google_news",
                    url=entry.get("link", ""),
                    published=entry.get("published", ""),
                    score=0.0,
                    keywords_matched=[],
                    summary=entry.get("summary", "")[:500]
                )
                topics.append(topic)
        
        logger.info(f"Found {len(topics)} topics from Google News")
        return topics
    
    @handle_errors(retry_count=3, retry_delay=2.0, fallback=[])
    def fetch_reddit(self) -> List[Topic]:
        """Fetch topics from Reddit JSON API (no auth needed)."""
        topics = []
        
        for subreddit in CONTENT_CONFIG["reddit_subs"]:
            url = API_ENDPOINTS["reddit"].format(subreddit)
            logger.info(f"Fetching Reddit r/{subreddit}...")
            
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                for post in data.get("data", {}).get("children", [])[:15]:
                    post_data = post.get("data", {})
                    
                    # Skip if too old (>7 days)
                    created = datetime.fromtimestamp(post_data.get("created_utc", 0))
                    if datetime.now() - created > timedelta(days=7):
                        continue
                    
                    topic = Topic(
                        id=generate_id(post_data.get("id", "")),
                        title=post_data.get("title", ""),
                        source=f"reddit_r/{subreddit}",
                        url=f"https://reddit.com{post_data.get('permalink', '')}",
                        published=created.isoformat(),
                        score=float(post_data.get("score", 0)),
                        keywords_matched=[],
                        summary=post_data.get("selftext", "")[:500]
                    )
                    topics.append(topic)
                    
            except Exception as e:
                logger.warning(f"Reddit fetch failed for r/{subreddit}: {e}")
        
        logger.info(f"Found {len(topics)} topics from Reddit")
        return topics
    
    def _clean_title(self, title: str) -> str:
        """Clean up news title."""
        # Remove source suffix (e.g., " - CNN")
        title = re.sub(r'\s*[-–—]\s*[A-Za-z\s]+$', '', title)
        return title.strip()
    
    def _calculate_score(self, topic: Topic) -> float:
        """
        Calculate topic relevance score.
        Higher = more relevant to AI/robotics/job displacement.
        """
        score = 0.0
        title_lower = topic.title.lower()
        summary_lower = topic.summary.lower()
        text = f"{title_lower} {summary_lower}"
        
        # Keyword matching (primary factor)
        matched_keywords = []
        for keyword in self.keywords:
            if keyword.lower() in text:
                score += 20
                matched_keywords.append(keyword)
        
        # High-value terms
        high_value = ["mass layoff", "job loss", "unemploy", "replace", "automat", "robot"]
        for term in high_value:
            if term in text:
                score += 15
        
        # Urgency/fear terms (viral potential)
        viral_terms = ["breaking", "just", "shock", "warn", "crisis", "fear", "million"]
        for term in viral_terms:
            if term in text:
                score += 5
        
        # 2026 specificity
        if "2026" in text or "2025" in text:
            score += 10
        
        # Reddit score bonus (engagement indicator)
        if topic.source.startswith("reddit"):
            score += min(topic.score / 100, 20)  # Cap at 20 bonus
        
        # Recency bonus
        try:
            pub_date = datetime.fromisoformat(topic.published.replace("Z", "+00:00"))
            days_old = (datetime.now(pub_date.tzinfo) - pub_date).days
            if days_old <= 1:
                score += 30
            elif days_old <= 3:
                score += 15
            elif days_old <= 7:
                score += 5
        except:
            pass
        
        topic.score = score
        topic.keywords_matched = matched_keywords
        return score
    
    def discover(self, limit: int = 10) -> List[Topic]:
        """
        Discover and rank top topics.
        Returns sorted list of most relevant topics.
        """
        logger.info("🔍 Starting topic discovery...")
        
        # Fetch from all sources
        all_topics = []
        all_topics.extend(self.fetch_google_news())
        all_topics.extend(self.fetch_reddit())
        
        # Score and rank
        for topic in all_topics:
            self._calculate_score(topic)
        
        # Sort by score (descending)
        ranked = sorted(all_topics, key=lambda t: t.score, reverse=True)
        
        # Deduplicate by similar titles
        seen_titles = set()
        unique_topics = []
        for topic in ranked:
            # Simple dedup: first 50 chars of title
            title_key = topic.title[:50].lower()
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_topics.append(topic)
        
        top_topics = unique_topics[:limit]
        
        logger.info(f"✓ Discovered {len(top_topics)} relevant topics")
        for i, t in enumerate(top_topics[:5], 1):
            logger.info(f"  {i}. [{t.score:.0f}] {t.title[:60]}...")
        
        return top_topics
    
    def get_best_topic(self) -> Optional[Topic]:
        """Get the single best topic for video creation."""
        topics = self.discover(limit=1)
        return topics[0] if topics else None


# =============================================================================
# CLI USAGE
# =============================================================================

if __name__ == "__main__":
    discovery = TopicDiscovery()
    topics = discovery.discover(limit=10)
    
    print("\n🔥 TOP TOPICS FOR VIDEO:\n")
    for i, topic in enumerate(topics, 1):
        print(f"{i}. [{topic.score:.0f}] {topic.title}")
        print(f"   Source: {topic.source}")
        print(f"   Keywords: {', '.join(topic.keywords_matched) or 'none'}")
        print(f"   URL: {topic.url}\n")
