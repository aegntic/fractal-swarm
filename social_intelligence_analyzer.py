"""
Social Intelligence Analyzer - Web scraping for crypto project analysis
Uses crawl4ai and playwright for robust data collection without APIs
"""

import asyncio
import json
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import hashlib
from urllib.parse import urlparse, urljoin
import logging

# Web scraping libraries
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy, LLMExtractionStrategy
from playwright.async_api import async_playwright, Browser, Page
import aiohttp
from bs4 import BeautifulSoup
import cloudscraper

# Data processing
import numpy as np
from collections import defaultdict
import redis.asyncio as redis

logger = logging.getLogger(__name__)

@dataclass
class SocialMetrics:
    """Aggregated social media metrics for a crypto project"""
    twitter_followers: int = 0
    twitter_engagement_rate: float = 0.0
    twitter_post_frequency: float = 0.0
    twitter_reply_ratio: float = 0.0
    twitter_verified: bool = False
    twitter_account_age_days: int = 0
    
    telegram_members: int = 0
    telegram_online_ratio: float = 0.0
    telegram_message_frequency: float = 0.0
    telegram_admin_activity: float = 0.0
    
    website_valid: bool = False
    website_ssl: bool = False
    website_age_days: int = 0
    website_tech_stack: List[str] = field(default_factory=list)
    website_update_frequency: float = 0.0
    
    github_stars: int = 0
    github_commits_30d: int = 0
    github_contributors: int = 0
    
    reddit_subscribers: int = 0
    reddit_active_users: int = 0
    
    overall_credibility_score: float = 0.0
    bot_activity_score: float = 0.0
    community_health_score: float = 0.0

@dataclass
class WebsiteAnalysis:
    """Detailed website analysis results"""
    url: str
    is_valid: bool
    has_ssl: bool
    domain_age_days: int
    tech_stack: List[str]
    has_whitepaper: bool
    has_roadmap: bool
    has_team_info: bool
    has_tokenomics: bool
    social_links: Dict[str, str]
    red_flags: List[str]
    trust_score: float

class SocialIntelligenceAnalyzer:
    """Analyzes social media and web presence without using paid APIs"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None
        self.browser = None
        self.crawler = None
        self.scraper = cloudscraper.create_scraper()
        
        # User agents for rotation
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        
    async def initialize(self):
        """Initialize scraping infrastructure"""
        self.redis_client = await redis.from_url(self.redis_url)
        self.crawler = AsyncWebCrawler(verbose=False)
        logger.info("Social Intelligence Analyzer initialized")
    
    async def analyze_project(self, coin_symbol: str, project_name: str, 
                            twitter_handle: Optional[str] = None,
                            telegram_handle: Optional[str] = None,
                            website_url: Optional[str] = None) -> SocialMetrics:
        """Comprehensive analysis of a crypto project's social presence"""
        metrics = SocialMetrics()
        
        # Check cache first
        cache_key = f"social:metrics:{coin_symbol}"
        cached_data = await self.redis_client.get(cache_key)
        if cached_data:
            cached = json.loads(cached_data)
            # Return cached if less than 1 hour old
            if datetime.fromisoformat(cached['timestamp']) > datetime.utcnow() - timedelta(hours=1):
                return SocialMetrics(**cached['metrics'])
        
        # Parallel analysis
        tasks = []
        
        if twitter_handle:
            tasks.append(self._analyze_twitter(twitter_handle))
        else:
            # Try to find Twitter handle
            tasks.append(self._find_and_analyze_twitter(project_name, coin_symbol))
        
        if telegram_handle:
            tasks.append(self._analyze_telegram(telegram_handle))
        else:
            # Try to find Telegram
            tasks.append(self._find_and_analyze_telegram(project_name, coin_symbol))
        
        if website_url:
            tasks.append(self._analyze_website(website_url))
        else:
            # Try to find website
            tasks.append(self._find_and_analyze_website(project_name, coin_symbol))
        
        # Additional platforms
        tasks.append(self._analyze_github(project_name, coin_symbol))
        tasks.append(self._analyze_reddit(coin_symbol))
        
        # Execute all analyses in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Analysis task {i} failed: {result}")
                continue
            
            if isinstance(result, dict):
                # Update metrics based on result type
                if 'twitter' in result:
                    metrics.__dict__.update(result['twitter'])
                elif 'telegram' in result:
                    metrics.__dict__.update(result['telegram'])
                elif 'website' in result:
                    metrics.__dict__.update(result['website'])
                elif 'github' in result:
                    metrics.__dict__.update(result['github'])
                elif 'reddit' in result:
                    metrics.__dict__.update(result['reddit'])
        
        # Calculate aggregate scores
        metrics.overall_credibility_score = self._calculate_credibility_score(metrics)
        metrics.bot_activity_score = self._calculate_bot_score(metrics)
        metrics.community_health_score = self._calculate_community_health(metrics)
        
        # Cache results
        cache_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'metrics': metrics.__dict__
        }
        await self.redis_client.set(cache_key, json.dumps(cache_data), ex=3600)
        
        return metrics
    
    async def _analyze_twitter(self, handle: str) -> Dict[str, Any]:
        """Analyze Twitter/X account without API"""
        try:
            # Clean handle
            handle = handle.replace('@', '').strip()
            
            # Use crawl4ai for initial page load
            url = f"https://twitter.com/{handle}"
            
            async with self.crawler as crawler:
                result = await crawler.arun(
                    url=url,
                    word_count_threshold=100,
                    extraction_strategy=JsonCssExtractionStrategy(
                        schema={
                            "name": "Twitter Profile",
                            "baseSelector": "article",
                            "fields": [
                                {"name": "followers", "selector": "a[href$='/followers'] span", "type": "text"},
                                {"name": "following", "selector": "a[href$='/following'] span", "type": "text"},
                                {"name": "tweets", "selector": "div[data-testid='primaryColumn'] article", "type": "list"},
                            ]
                        }
                    ),
                    bypass_cache=True
                )
            
            # Parse with BeautifulSoup for additional data
            soup = BeautifulSoup(result.html, 'html.parser')
            
            # Extract metrics
            followers = self._parse_number(self._extract_followers(soup))
            
            # Get recent tweets for engagement analysis
            tweets_data = await self._get_recent_tweets(handle)
            engagement_rate = self._calculate_engagement_rate(tweets_data, followers)
            
            # Check verification
            is_verified = self._check_twitter_verification(soup)
            
            # Calculate post frequency
            post_frequency = self._calculate_post_frequency(tweets_data)
            
            # Calculate reply ratio (potential bot indicator)
            reply_ratio = self._calculate_reply_ratio(tweets_data)
            
            # Estimate account age
            account_age = await self._estimate_twitter_account_age(handle)
            
            return {
                'twitter': {
                    'twitter_followers': followers,
                    'twitter_engagement_rate': engagement_rate,
                    'twitter_post_frequency': post_frequency,
                    'twitter_reply_ratio': reply_ratio,
                    'twitter_verified': is_verified,
                    'twitter_account_age_days': account_age
                }
            }
            
        except Exception as e:
            logger.error(f"Twitter analysis failed for {handle}: {e}")
            return {'twitter': {}}
    
    async def _get_recent_tweets(self, handle: str, count: int = 20) -> List[Dict]:
        """Get recent tweets without API"""
        tweets = []
        
        try:
            # Use nitter instance or Twitter's mobile site
            nitter_instances = [
                "nitter.net",
                "nitter.42l.fr",
                "nitter.pussthecat.org"
            ]
            
            for instance in nitter_instances:
                try:
                    url = f"https://{instance}/{handle}"
                    response = self.scraper.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Extract tweets from nitter
                        tweet_items = soup.find_all('div', class_='timeline-item')[:count]
                        
                        for item in tweet_items:
                            tweet_data = {
                                'text': item.find('div', class_='tweet-content').text if item.find('div', class_='tweet-content') else '',
                                'likes': self._parse_number(item.find('span', class_='icon-heart').next_sibling.text) if item.find('span', class_='icon-heart') else 0,
                                'retweets': self._parse_number(item.find('span', class_='icon-retweet').next_sibling.text) if item.find('span', class_='icon-retweet') else 0,
                                'replies': self._parse_number(item.find('span', class_='icon-comment').next_sibling.text) if item.find('span', class_='icon-comment') else 0,
                                'timestamp': item.find('span', class_='tweet-date').get('title') if item.find('span', class_='tweet-date') else None
                            }
                            tweets.append(tweet_data)
                        
                        break
                        
                except Exception as e:
                    logger.warning(f"Failed to fetch from {instance}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to get recent tweets: {e}")
        
        return tweets
    
    async def _analyze_telegram(self, handle: str) -> Dict[str, Any]:
        """Analyze Telegram group/channel"""
        try:
            # Clean handle
            handle = handle.replace('@', '').replace('t.me/', '').strip()
            
            # Use Telegram's preview feature
            preview_url = f"https://t.me/s/{handle}"
            
            response = self.scraper.get(preview_url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract member count
            members_elem = soup.find('div', class_='tgme_page_extra')
            members = 0
            if members_elem:
                members_text = members_elem.text
                members = self._parse_number(members_text)
            
            # Get recent messages for activity analysis
            messages = soup.find_all('div', class_='tgme_widget_message')
            
            # Calculate message frequency
            message_frequency = self._calculate_telegram_activity(messages)
            
            # Estimate online ratio (based on recent activity)
            online_ratio = min(message_frequency / 100, 1.0)  # Normalize
            
            # Check for admin activity
            admin_activity = self._check_admin_activity(messages)
            
            return {
                'telegram': {
                    'telegram_members': members,
                    'telegram_online_ratio': online_ratio,
                    'telegram_message_frequency': message_frequency,
                    'telegram_admin_activity': admin_activity
                }
            }
            
        except Exception as e:
            logger.error(f"Telegram analysis failed for {handle}: {e}")
            return {'telegram': {}}
    
    async def _analyze_website(self, url: str) -> Dict[str, Any]:
        """Comprehensive website analysis"""
        try:
            analysis = await self._deep_website_analysis(url)
            
            return {
                'website': {
                    'website_valid': analysis.is_valid,
                    'website_ssl': analysis.has_ssl,
                    'website_age_days': analysis.domain_age_days,
                    'website_tech_stack': analysis.tech_stack,
                    'website_update_frequency': self._estimate_update_frequency(analysis)
                }
            }
            
        except Exception as e:
            logger.error(f"Website analysis failed for {url}: {e}")
            return {'website': {}}
    
    async def _deep_website_analysis(self, url: str) -> WebsiteAnalysis:
        """Perform deep website analysis"""
        analysis = WebsiteAnalysis(
            url=url,
            is_valid=False,
            has_ssl=False,
            domain_age_days=0,
            tech_stack=[],
            has_whitepaper=False,
            has_roadmap=False,
            has_team_info=False,
            has_tokenomics=False,
            social_links={},
            red_flags=[],
            trust_score=0.0
        )
        
        try:
            # Check SSL
            analysis.has_ssl = url.startswith('https://')
            
            # Crawl website
            async with self.crawler as crawler:
                result = await crawler.arun(
                    url=url,
                    word_count_threshold=100,
                    exclude_external_links=False,
                    bypass_cache=True
                )
            
            if result.success:
                analysis.is_valid = True
                soup = BeautifulSoup(result.html, 'html.parser')
                
                # Check for important pages
                text_lower = result.text.lower()
                analysis.has_whitepaper = 'whitepaper' in text_lower or 'white paper' in text_lower
                analysis.has_roadmap = 'roadmap' in text_lower
                analysis.has_team_info = 'team' in text_lower or 'about us' in text_lower
                analysis.has_tokenomics = 'tokenomics' in text_lower or 'token economics' in text_lower
                
                # Extract social links
                social_platforms = ['twitter', 'telegram', 'discord', 'github', 'reddit', 'medium']
                for link in soup.find_all('a', href=True):
                    href = link['href'].lower()
                    for platform in social_platforms:
                        if platform in href:
                            analysis.social_links[platform] = link['href']
                
                # Detect tech stack
                analysis.tech_stack = self._detect_tech_stack(result.html, soup)
                
                # Check for red flags
                analysis.red_flags = self._check_red_flags(soup, text_lower)
                
                # Calculate trust score
                analysis.trust_score = self._calculate_website_trust_score(analysis)
                
                # Estimate domain age using archive.org
                analysis.domain_age_days = await self._estimate_domain_age(url)
                
        except Exception as e:
            logger.error(f"Deep website analysis failed: {e}")
        
        return analysis
    
    def _detect_tech_stack(self, html: str, soup: BeautifulSoup) -> List[str]:
        """Detect website technology stack"""
        tech_stack = []
        
        # Check meta tags
        generator = soup.find('meta', attrs={'name': 'generator'})
        if generator:
            tech_stack.append(generator.get('content', ''))
        
        # Common frameworks
        if 'react' in html.lower():
            tech_stack.append('React')
        if 'vue' in html.lower():
            tech_stack.append('Vue.js')
        if 'angular' in html.lower():
            tech_stack.append('Angular')
        if 'wordpress' in html.lower():
            tech_stack.append('WordPress')
        if 'next.js' in html.lower() or '_next' in html:
            tech_stack.append('Next.js')
        
        return list(set(tech_stack))
    
    def _check_red_flags(self, soup: BeautifulSoup, text_lower: str) -> List[str]:
        """Check for website red flags"""
        red_flags = []
        
        # Check for suspicious promises
        if 'guaranteed returns' in text_lower or 'risk free' in text_lower:
            red_flags.append('Unrealistic promises')
        
        if '1000x' in text_lower or '10000x' in text_lower:
            red_flags.append('Extreme return claims')
        
        # Check for missing important info
        if 'team' not in text_lower and 'about' not in text_lower:
            red_flags.append('No team information')
        
        if 'audit' not in text_lower:
            red_flags.append('No audit mentioned')
        
        # Check for copy-paste content
        generic_phrases = [
            'lorem ipsum',
            'coming soon',
            'under construction'
        ]
        for phrase in generic_phrases:
            if phrase in text_lower:
                red_flags.append(f'Generic content: {phrase}')
        
        return red_flags
    
    async def _estimate_domain_age(self, url: str) -> int:
        """Estimate domain age using Wayback Machine"""
        try:
            domain = urlparse(url).netloc
            wayback_url = f"http://archive.org/wayback/available?url={domain}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(wayback_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('archived_snapshots', {}).get('closest', {}).get('timestamp'):
                            timestamp = data['archived_snapshots']['closest']['timestamp']
                            # Parse timestamp (format: YYYYMMDDhhmmss)
                            year = int(timestamp[:4])
                            month = int(timestamp[4:6])
                            day = int(timestamp[6:8])
                            first_seen = datetime(year, month, day)
                            age_days = (datetime.utcnow() - first_seen).days
                            return age_days
        except Exception as e:
            logger.error(f"Failed to estimate domain age: {e}")
        
        return 0
    
    async def _analyze_github(self, project_name: str, coin_symbol: str) -> Dict[str, Any]:
        """Analyze GitHub activity"""
        try:
            # Search for GitHub repo
            search_terms = [project_name, coin_symbol, f"{project_name}-{coin_symbol}"]
            
            for term in search_terms:
                search_url = f"https://api.github.com/search/repositories?q={term}+crypto+blockchain"
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(search_url) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get('items'):
                                # Take the most starred result
                                repo = max(data['items'], key=lambda x: x.get('stargazers_count', 0))
                                
                                # Get commit activity
                                commits_url = f"https://api.github.com/repos/{repo['full_name']}/commits"
                                async with session.get(commits_url) as commits_response:
                                    if commits_response.status == 200:
                                        commits = await commits_response.json()
                                        recent_commits = len([c for c in commits if self._is_recent_commit(c)])
                                    else:
                                        recent_commits = 0
                                
                                return {
                                    'github': {
                                        'github_stars': repo.get('stargazers_count', 0),
                                        'github_commits_30d': recent_commits,
                                        'github_contributors': repo.get('contributors_count', 0)
                                    }
                                }
            
        except Exception as e:
            logger.error(f"GitHub analysis failed: {e}")
        
        return {'github': {}}
    
    async def _analyze_reddit(self, coin_symbol: str) -> Dict[str, Any]:
        """Analyze Reddit presence"""
        try:
            # Try common subreddit patterns
            subreddit_patterns = [
                f"r/{coin_symbol}",
                f"r/{coin_symbol}token",
                f"r/{coin_symbol}crypto",
                f"r/{coin_symbol}coin"
            ]
            
            for pattern in subreddit_patterns:
                subreddit_name = pattern.replace('r/', '')
                url = f"https://www.reddit.com/r/{subreddit_name}/about.json"
                
                headers = {'User-Agent': np.random.choice(self.user_agents)}
                response = self.scraper.get(url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data:
                        return {
                            'reddit': {
                                'reddit_subscribers': data['data'].get('subscribers', 0),
                                'reddit_active_users': data['data'].get('active_user_count', 0)
                            }
                        }
            
        except Exception as e:
            logger.error(f"Reddit analysis failed: {e}")
        
        return {'reddit': {}}
    
    # Helper methods
    def _parse_number(self, text: str) -> int:
        """Parse numbers with K, M suffixes"""
        if not text:
            return 0
        
        text = text.strip().upper()
        multipliers = {'K': 1000, 'M': 1000000, 'B': 1000000000}
        
        for suffix, multiplier in multipliers.items():
            if suffix in text:
                try:
                    number = float(text.replace(suffix, '').replace(',', '').strip())
                    return int(number * multiplier)
                except:
                    return 0
        
        try:
            return int(text.replace(',', ''))
        except:
            return 0
    
    def _calculate_engagement_rate(self, tweets: List[Dict], followers: int) -> float:
        """Calculate average engagement rate"""
        if not tweets or followers == 0:
            return 0.0
        
        total_engagement = 0
        for tweet in tweets:
            engagement = tweet.get('likes', 0) + tweet.get('retweets', 0) + tweet.get('replies', 0)
            total_engagement += engagement
        
        avg_engagement = total_engagement / len(tweets)
        return min(avg_engagement / followers, 1.0)
    
    def _calculate_post_frequency(self, tweets: List[Dict]) -> float:
        """Calculate posts per day"""
        if len(tweets) < 2:
            return 0.0
        
        # Estimate based on tweet timestamps
        # Simplified: assume tweets span 7 days
        return len(tweets) / 7.0
    
    def _calculate_reply_ratio(self, tweets: List[Dict]) -> float:
        """Calculate ratio of replies to original tweets"""
        if not tweets:
            return 0.0
        
        reply_count = sum(1 for t in tweets if t.get('text', '').startswith('@'))
        return reply_count / len(tweets)
    
    def _check_twitter_verification(self, soup: BeautifulSoup) -> bool:
        """Check if Twitter account is verified"""
        # Look for verification badge
        verification_selectors = [
            'svg[aria-label="Verified account"]',
            'svg[data-testid="icon-verified"]',
            '.ProfileHeaderCard-badges',
        ]
        
        for selector in verification_selectors:
            if soup.select_one(selector):
                return True
        
        return False
    
    async def _estimate_twitter_account_age(self, handle: str) -> int:
        """Estimate Twitter account age"""
        # Would use various methods to estimate
        # For now, return a default
        return 365  # 1 year default
    
    def _calculate_telegram_activity(self, messages: List) -> float:
        """Calculate Telegram message frequency"""
        if not messages:
            return 0.0
        
        # Estimate messages per day based on visible messages
        return len(messages) / 1.0  # Assume messages span 1 day
    
    def _check_admin_activity(self, messages: List) -> float:
        """Check for admin/moderator activity"""
        if not messages:
            return 0.0
        
        admin_messages = 0
        for msg in messages:
            # Check for admin badges or pinned messages
            if msg.get('class') and 'pinned' in str(msg.get('class')):
                admin_messages += 1
        
        return admin_messages / max(len(messages), 1)
    
    def _extract_followers(self, soup: BeautifulSoup) -> str:
        """Extract follower count from Twitter page"""
        # Try multiple selectors
        selectors = [
            'a[href$="/followers"] span',
            'a[href*="followers"] span',
            'span:contains("Followers")',
        ]
        
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.text
        
        return "0"
    
    def _is_recent_commit(self, commit: Dict) -> bool:
        """Check if commit is within last 30 days"""
        try:
            commit_date = datetime.fromisoformat(commit['commit']['author']['date'].replace('Z', '+00:00'))
            return (datetime.utcnow() - commit_date.replace(tzinfo=None)).days <= 30
        except:
            return False
    
    def _estimate_update_frequency(self, analysis: WebsiteAnalysis) -> float:
        """Estimate website update frequency"""
        # Based on various factors
        score = 0.0
        
        if analysis.has_ssl:
            score += 0.1
        
        if analysis.tech_stack:
            score += 0.2
        
        if not analysis.red_flags:
            score += 0.3
        
        if analysis.domain_age_days > 180:
            score += 0.2
        
        return score
    
    def _calculate_credibility_score(self, metrics: SocialMetrics) -> float:
        """Calculate overall credibility score"""
        score = 0.0
        weights = {
            'twitter': 0.25,
            'telegram': 0.2,
            'website': 0.3,
            'github': 0.15,
            'reddit': 0.1
        }
        
        # Twitter score
        twitter_score = 0.0
        if metrics.twitter_followers > 1000:
            twitter_score += 0.3
        if metrics.twitter_verified:
            twitter_score += 0.4
        if metrics.twitter_engagement_rate > 0.02:
            twitter_score += 0.3
        
        # Telegram score
        telegram_score = 0.0
        if metrics.telegram_members > 500:
            telegram_score += 0.4
        if metrics.telegram_message_frequency > 10:
            telegram_score += 0.3
        if metrics.telegram_admin_activity > 0.1:
            telegram_score += 0.3
        
        # Website score
        website_score = 0.0
        if metrics.website_valid:
            website_score += 0.3
        if metrics.website_ssl:
            website_score += 0.2
        if metrics.website_age_days > 90:
            website_score += 0.5
        
        # GitHub score
        github_score = 0.0
        if metrics.github_stars > 10:
            github_score += 0.4
        if metrics.github_commits_30d > 10:
            github_score += 0.6
        
        # Reddit score
        reddit_score = 0.0
        if metrics.reddit_subscribers > 100:
            reddit_score += 0.5
        if metrics.reddit_active_users > 10:
            reddit_score += 0.5
        
        # Calculate weighted score
        score = (
            twitter_score * weights['twitter'] +
            telegram_score * weights['telegram'] +
            website_score * weights['website'] +
            github_score * weights['github'] +
            reddit_score * weights['reddit']
        )
        
        return min(score, 1.0)
    
    def _calculate_bot_score(self, metrics: SocialMetrics) -> float:
        """Calculate bot activity score (higher = more bots)"""
        bot_score = 0.0
        
        # High reply ratio indicates potential bot activity
        if metrics.twitter_reply_ratio > 0.7:
            bot_score += 0.3
        
        # Too high engagement rate can indicate bot activity
        if metrics.twitter_engagement_rate > 0.15:
            bot_score += 0.2
        
        # Suspicious follower patterns
        if metrics.twitter_followers > 10000 and metrics.twitter_engagement_rate < 0.001:
            bot_score += 0.3
        
        # New account with high activity
        if metrics.twitter_account_age_days < 30 and metrics.twitter_post_frequency > 50:
            bot_score += 0.2
        
        return min(bot_score, 1.0)
    
    def _calculate_community_health(self, metrics: SocialMetrics) -> float:
        """Calculate community health score"""
        health_score = 0.0
        
        # Balanced engagement
        if 0.01 < metrics.twitter_engagement_rate < 0.1:
            health_score += 0.2
        
        # Active Telegram
        if metrics.telegram_online_ratio > 0.1:
            health_score += 0.2
        
        # Regular admin activity
        if 0.05 < metrics.telegram_admin_activity < 0.5:
            health_score += 0.2
        
        # Active development
        if metrics.github_commits_30d > 20:
            health_score += 0.2
        
        # Organic growth indicators
        if metrics.website_age_days > 180:
            health_score += 0.2
        
        return min(health_score, 1.0)
    
    async def _find_and_analyze_twitter(self, project_name: str, coin_symbol: str) -> Dict[str, Any]:
        """Find and analyze Twitter account"""
        # Search for Twitter handle using web search
        search_queries = [
            f"{project_name} {coin_symbol} twitter",
            f"{project_name} crypto twitter",
            f"${coin_symbol} twitter official"
        ]
        
        for query in search_queries:
            # Would implement actual search
            # For now, return empty
            pass
        
        return {'twitter': {}}
    
    async def _find_and_analyze_telegram(self, project_name: str, coin_symbol: str) -> Dict[str, Any]:
        """Find and analyze Telegram group"""
        # Similar search approach
        return {'telegram': {}}
    
    async def _find_and_analyze_website(self, project_name: str, coin_symbol: str) -> Dict[str, Any]:
        """Find and analyze official website"""
        # Search for official website
        return {'website': {}}
    
    def _calculate_website_trust_score(self, analysis: WebsiteAnalysis) -> float:
        """Calculate website trust score"""
        score = 0.0
        
        if analysis.has_ssl:
            score += 0.15
        
        if analysis.has_whitepaper:
            score += 0.2
        
        if analysis.has_team_info:
            score += 0.15
        
        if analysis.has_roadmap:
            score += 0.1
        
        if analysis.has_tokenomics:
            score += 0.1
        
        # Deduct for red flags
        score -= len(analysis.red_flags) * 0.1
        
        # Age bonus
        if analysis.domain_age_days > 365:
            score += 0.2
        elif analysis.domain_age_days > 180:
            score += 0.1
        
        return max(0, min(score, 1.0))