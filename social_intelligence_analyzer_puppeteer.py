"""
Social Intelligence Analyzer - Using Puppeteer for free web scraping
No API keys required - pure web scraping approach
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

# Puppeteer through pyppeteer
from pyppeteer import launch
from pyppeteer.page import Page
from pyppeteer.browser import Browser

# Alternative scraping libraries
import aiohttp
from bs4 import BeautifulSoup
import cloudscraper
from fake_useragent import UserAgent

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
    twitter_follower_growth_rate: float = 0.0
    
    telegram_members: int = 0
    telegram_online_ratio: float = 0.0
    telegram_message_frequency: float = 0.0
    telegram_admin_activity: float = 0.0
    telegram_bot_percentage: float = 0.0
    
    website_valid: bool = False
    website_ssl: bool = False
    website_age_days: int = 0
    website_tech_stack: List[str] = field(default_factory=list)
    website_update_frequency: float = 0.0
    website_security_score: float = 0.0
    
    github_stars: int = 0
    github_commits_30d: int = 0
    github_contributors: int = 0
    github_last_commit_days: int = 0
    
    reddit_subscribers: int = 0
    reddit_active_users: int = 0
    reddit_post_frequency: float = 0.0
    
    discord_members: int = 0
    discord_online_members: int = 0
    
    overall_credibility_score: float = 0.0
    bot_activity_score: float = 0.0
    community_health_score: float = 0.0
    risk_score: float = 0.0

class PuppeteerSocialAnalyzer:
    """Analyzes social media using Puppeteer - no API keys needed"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", headless: bool = True):
        self.redis_url = redis_url
        self.redis_client = None
        self.browser = None
        self.headless = headless
        self.scraper = cloudscraper.create_scraper()
        self.ua = UserAgent()
        
        # Stealth options for Puppeteer
        self.browser_args = [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--single-process',
            '--disable-gpu',
            '--disable-blink-features=AutomationControlled',
        ]
        
    async def initialize(self):
        """Initialize Puppeteer browser and Redis"""
        self.redis_client = await redis.from_url(self.redis_url)
        
        # Launch Puppeteer with stealth mode
        self.browser = await launch(
            headless=self.headless,
            args=self.browser_args,
            handleSIGINT=False,
            handleSIGTERM=False,
            handleSIGHUP=False
        )
        
        logger.info("Puppeteer Social Analyzer initialized")
    
    async def analyze_project(self, 
                            coin_symbol: str, 
                            project_name: str,
                            contract_address: Optional[str] = None,
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
            if datetime.fromisoformat(cached['timestamp']) > datetime.utcnow() - timedelta(hours=1):
                return SocialMetrics(**cached['metrics'])
        
        # Create analysis tasks
        tasks = []
        
        # Twitter/X Analysis
        if twitter_handle:
            tasks.append(self._analyze_twitter_puppeteer(twitter_handle))
        else:
            tasks.append(self._find_and_analyze_twitter(project_name, coin_symbol))
        
        # Telegram Analysis
        if telegram_handle:
            tasks.append(self._analyze_telegram_puppeteer(telegram_handle))
        else:
            tasks.append(self._find_and_analyze_telegram(project_name, coin_symbol))
        
        # Website Analysis
        if website_url:
            tasks.append(self._analyze_website_puppeteer(website_url))
        else:
            tasks.append(self._find_and_analyze_website(project_name, coin_symbol, contract_address))
        
        # Additional platforms
        tasks.extend([
            self._analyze_github_free(project_name, coin_symbol),
            self._analyze_reddit_free(coin_symbol, project_name),
            self._analyze_discord_free(project_name, coin_symbol)
        ])
        
        # Execute all analyses in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Analysis task {i} failed: {result}")
                continue
            
            if isinstance(result, dict):
                for key, value in result.items():
                    if key in metrics.__dict__:
                        setattr(metrics, key, value)
        
        # Calculate aggregate scores
        metrics.overall_credibility_score = self._calculate_credibility_score(metrics)
        metrics.bot_activity_score = self._calculate_bot_score(metrics)
        metrics.community_health_score = self._calculate_community_health(metrics)
        metrics.risk_score = self._calculate_risk_score(metrics)
        
        # Cache results
        cache_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'metrics': metrics.__dict__
        }
        await self.redis_client.set(cache_key, json.dumps(cache_data), ex=3600)
        
        return metrics
    
    async def _analyze_twitter_puppeteer(self, handle: str) -> Dict[str, Any]:
        """Analyze Twitter using Puppeteer"""
        page = None
        try:
            # Clean handle
            handle = handle.replace('@', '').strip()
            
            # Create new page with stealth settings
            page = await self.browser.newPage()
            await page.setUserAgent(self.ua.random)
            
            # Additional stealth techniques
            await page.evaluateOnNewDocument('''() => {
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                window.chrome = {runtime: {}};
                Object.defineProperty(navigator, 'permissions', {
                    get: () => ({
                        query: () => Promise.resolve({state: 'granted'})
                    })
                });
            }''')
            
            # Use mobile Twitter for easier parsing
            await page.setViewport({'width': 375, 'height': 667, 'isMobile': True})
            
            # Try multiple Twitter URLs
            twitter_urls = [
                f"https://mobile.twitter.com/{handle}",
                f"https://twitter.com/{handle}",
                f"https://x.com/{handle}"
            ]
            
            for url in twitter_urls:
                try:
                    await page.goto(url, {'waitUntil': 'networkidle2', 'timeout': 30000})
                    await asyncio.sleep(2)  # Wait for dynamic content
                    
                    # Get page content
                    content = await page.content()
                    
                    # Extract metrics using JavaScript
                    metrics = await page.evaluate('''() => {
                        // Extract follower count
                        let followers = 0;
                        const followerElements = document.querySelectorAll('a[href*="/followers"] span');
                        for (let elem of followerElements) {
                            const text = elem.innerText;
                            if (text.match(/[0-9]/)) {
                                followers = text;
                                break;
                            }
                        }
                        
                        // Check verification
                        const isVerified = !!document.querySelector('svg[aria-label*="Verified"]');
                        
                        // Get bio
                        const bioElement = document.querySelector('div[data-testid="UserDescription"]');
                        const bio = bioElement ? bioElement.innerText : '';
                        
                        // Get join date
                        const joinDateElement = document.querySelector('span[data-testid="UserJoinDate"]');
                        const joinDate = joinDateElement ? joinDateElement.innerText : '';
                        
                        return {
                            followers: followers,
                            isVerified: isVerified,
                            bio: bio,
                            joinDate: joinDate
                        };
                    }''')
                    
                    # Parse followers
                    followers = self._parse_number(str(metrics.get('followers', '0')))
                    
                    # Get recent tweets for engagement analysis
                    tweets = await self._extract_tweets_puppeteer(page)
                    
                    # Calculate metrics
                    engagement_rate = self._calculate_engagement_rate(tweets, followers)
                    post_frequency = self._calculate_post_frequency(tweets)
                    reply_ratio = self._calculate_reply_ratio(tweets)
                    
                    # Estimate account age
                    account_age = self._parse_join_date(metrics.get('joinDate', ''))
                    
                    # Analyze follower growth
                    growth_rate = await self._analyze_follower_growth(handle)
                    
                    return {
                        'twitter_followers': followers,
                        'twitter_engagement_rate': engagement_rate,
                        'twitter_post_frequency': post_frequency,
                        'twitter_reply_ratio': reply_ratio,
                        'twitter_verified': metrics.get('isVerified', False),
                        'twitter_account_age_days': account_age,
                        'twitter_follower_growth_rate': growth_rate
                    }
                    
                except Exception as e:
                    logger.warning(f"Failed to analyze Twitter with {url}: {e}")
                    continue
            
            # Fallback to nitter scraping
            return await self._analyze_twitter_nitter(handle)
            
        except Exception as e:
            logger.error(f"Twitter Puppeteer analysis failed for {handle}: {e}")
            return {}
        finally:
            if page:
                await page.close()
    
    async def _extract_tweets_puppeteer(self, page: Page) -> List[Dict]:
        """Extract tweets using Puppeteer"""
        try:
            # Scroll to load more tweets
            for _ in range(3):
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await asyncio.sleep(1)
            
            # Extract tweet data
            tweets = await page.evaluate('''() => {
                const tweets = [];
                const tweetElements = document.querySelectorAll('article[data-testid="tweet"]');
                
                for (let i = 0; i < Math.min(tweetElements.length, 20); i++) {
                    const tweet = tweetElements[i];
                    
                    // Get text
                    const textElement = tweet.querySelector('div[data-testid="tweetText"]');
                    const text = textElement ? textElement.innerText : '';
                    
                    // Get engagement metrics
                    const replyButton = tweet.querySelector('div[data-testid="reply"]');
                    const retweetButton = tweet.querySelector('div[data-testid="retweet"]');
                    const likeButton = tweet.querySelector('div[data-testid="like"]');
                    
                    const replies = replyButton ? replyButton.innerText : '0';
                    const retweets = retweetButton ? retweetButton.innerText : '0';
                    const likes = likeButton ? likeButton.innerText : '0';
                    
                    tweets.push({
                        text: text,
                        replies: replies,
                        retweets: retweets,
                        likes: likes
                    });
                }
                
                return tweets;
            }''')
            
            # Parse numbers
            for tweet in tweets:
                tweet['replies'] = self._parse_number(str(tweet['replies']))
                tweet['retweets'] = self._parse_number(str(tweet['retweets']))
                tweet['likes'] = self._parse_number(str(tweet['likes']))
            
            return tweets
            
        except Exception as e:
            logger.error(f"Failed to extract tweets: {e}")
            return []
    
    async def _analyze_twitter_nitter(self, handle: str) -> Dict[str, Any]:
        """Fallback to Nitter instances for Twitter data"""
        nitter_instances = [
            "nitter.net",
            "nitter.42l.fr", 
            "nitter.pussthecat.org",
            "nitter.fdn.fr",
            "nitter.1d4.us"
        ]
        
        for instance in nitter_instances:
            try:
                url = f"https://{instance}/{handle}"
                response = self.scraper.get(url, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Extract profile stats
                    profile_stats = soup.find_all('span', class_='profile-stat-num')
                    followers = 0
                    if len(profile_stats) >= 2:
                        followers = self._parse_number(profile_stats[1].text)
                    
                    # Get tweets
                    tweet_items = soup.find_all('div', class_='timeline-item')[:20]
                    tweets = []
                    
                    for item in tweet_items:
                        stats = item.find_all('span', class_='tweet-stat')
                        tweet_data = {
                            'text': item.find('div', class_='tweet-content').text if item.find('div', class_='tweet-content') else '',
                            'replies': self._parse_number(stats[0].text) if len(stats) > 0 else 0,
                            'retweets': self._parse_number(stats[1].text) if len(stats) > 1 else 0,
                            'likes': self._parse_number(stats[2].text) if len(stats) > 2 else 0
                        }
                        tweets.append(tweet_data)
                    
                    # Calculate metrics
                    engagement_rate = self._calculate_engagement_rate(tweets, followers)
                    post_frequency = len(tweets) / 7.0  # Assume tweets span a week
                    reply_ratio = self._calculate_reply_ratio(tweets)
                    
                    return {
                        'twitter_followers': followers,
                        'twitter_engagement_rate': engagement_rate,
                        'twitter_post_frequency': post_frequency,
                        'twitter_reply_ratio': reply_ratio,
                        'twitter_verified': False,  # Can't determine from Nitter
                        'twitter_account_age_days': 365,  # Default
                        'twitter_follower_growth_rate': 0.0
                    }
                    
            except Exception as e:
                logger.warning(f"Nitter instance {instance} failed: {e}")
                continue
        
        return {}
    
    async def _analyze_telegram_puppeteer(self, handle: str) -> Dict[str, Any]:
        """Analyze Telegram using web preview"""
        try:
            # Clean handle
            handle = handle.replace('@', '').replace('t.me/', '').strip()
            
            # Use Telegram's web preview
            preview_url = f"https://t.me/s/{handle}"
            
            page = await self.browser.newPage()
            await page.setUserAgent(self.ua.random)
            
            try:
                await page.goto(preview_url, {'waitUntil': 'networkidle2', 'timeout': 30000})
                await asyncio.sleep(2)
                
                # Extract data using JavaScript
                data = await page.evaluate('''() => {
                    // Get member count
                    const memberElement = document.querySelector('.tgme_page_extra');
                    const members = memberElement ? memberElement.innerText : '0';
                    
                    // Get channel title
                    const titleElement = document.querySelector('.tgme_page_title');
                    const title = titleElement ? titleElement.innerText : '';
                    
                    // Get description
                    const descElement = document.querySelector('.tgme_page_description');
                    const description = descElement ? descElement.innerText : '';
                    
                    // Count messages
                    const messages = document.querySelectorAll('.tgme_widget_message').length;
                    
                    // Check for verification
                    const isVerified = !!document.querySelector('.verified-icon');
                    
                    return {
                        members: members,
                        title: title,
                        description: description,
                        messageCount: messages,
                        isVerified: isVerified
                    };
                }''')
                
                # Parse member count
                members = self._parse_number(data.get('members', '0'))
                
                # Analyze messages for activity
                messages = await self._extract_telegram_messages(page)
                message_frequency = self._calculate_telegram_activity(messages)
                admin_activity = self._check_admin_activity(messages)
                
                # Estimate bot percentage
                bot_percentage = await self._estimate_telegram_bots(messages, members)
                
                # Estimate online ratio based on activity
                online_ratio = min(message_frequency / 100, 1.0)
                
                return {
                    'telegram_members': members,
                    'telegram_online_ratio': online_ratio,
                    'telegram_message_frequency': message_frequency,
                    'telegram_admin_activity': admin_activity,
                    'telegram_bot_percentage': bot_percentage
                }
                
            finally:
                await page.close()
                
        except Exception as e:
            logger.error(f"Telegram Puppeteer analysis failed for {handle}: {e}")
            return {}
    
    async def _extract_telegram_messages(self, page: Page) -> List[Dict]:
        """Extract Telegram messages for analysis"""
        try:
            messages = await page.evaluate('''() => {
                const msgs = [];
                const messageElements = document.querySelectorAll('.tgme_widget_message');
                
                for (let i = 0; i < Math.min(messageElements.length, 50); i++) {
                    const msg = messageElements[i];
                    
                    const author = msg.querySelector('.tgme_widget_message_author_name');
                    const text = msg.querySelector('.tgme_widget_message_text');
                    const views = msg.querySelector('.tgme_widget_message_views');
                    const date = msg.querySelector('.tgme_widget_message_date time');
                    
                    msgs.push({
                        author: author ? author.innerText : '',
                        text: text ? text.innerText : '',
                        views: views ? views.innerText : '0',
                        date: date ? date.getAttribute('datetime') : '',
                        isPinned: msg.classList.contains('pinned')
                    });
                }
                
                return msgs;
            }''')
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to extract Telegram messages: {e}")
            return []
    
    async def _analyze_website_puppeteer(self, url: str) -> Dict[str, Any]:
        """Analyze website using Puppeteer"""
        page = None
        try:
            page = await self.browser.newPage()
            await page.setUserAgent(self.ua.random)
            
            # Navigate to website
            response = await page.goto(url, {'waitUntil': 'networkidle2', 'timeout': 30000})
            
            # Check SSL
            has_ssl = url.startswith('https://')
            is_valid = response.status < 400
            
            # Extract data
            analysis = await page.evaluate('''() => {
                // Check for important elements
                const text = document.body.innerText.toLowerCase();
                
                const hasWhitepaper = text.includes('whitepaper') || text.includes('white paper');
                const hasRoadmap = text.includes('roadmap');
                const hasTeam = text.includes('team') || text.includes('about us');
                const hasTokenomics = text.includes('tokenomics');
                const hasAudit = text.includes('audit');
                
                // Extract social links
                const socialLinks = {};
                const links = document.querySelectorAll('a[href]');
                const platforms = ['twitter', 'telegram', 'discord', 'github', 'reddit', 'medium'];
                
                for (let link of links) {
                    const href = link.href.toLowerCase();
                    for (let platform of platforms) {
                        if (href.includes(platform)) {
                            socialLinks[platform] = link.href;
                        }
                    }
                }
                
                // Check for red flags
                const redFlags = [];
                if (text.includes('guaranteed returns')) redFlags.push('Guaranteed returns claim');
                if (text.includes('100x') || text.includes('1000x')) redFlags.push('Unrealistic return claims');
                if (text.includes('risk free')) redFlags.push('Risk-free claims');
                if (!hasTeam) redFlags.push('No team information');
                if (!hasAudit) redFlags.push('No audit mentioned');
                
                return {
                    hasWhitepaper,
                    hasRoadmap,
                    hasTeam,
                    hasTokenomics,
                    hasAudit,
                    socialLinks,
                    redFlags
                };
            }''')
            
            # Detect tech stack
            tech_stack = await self._detect_tech_stack_puppeteer(page)
            
            # Check domain age
            domain_age = await self._check_domain_age(url)
            
            # Calculate security score
            security_score = self._calculate_website_security_score(
                has_ssl, is_valid, analysis['hasAudit'], len(analysis['redFlags'])
            )
            
            return {
                'website_valid': is_valid,
                'website_ssl': has_ssl,
                'website_age_days': domain_age,
                'website_tech_stack': tech_stack,
                'website_update_frequency': 0.5 if is_valid else 0.0,
                'website_security_score': security_score
            }
            
        except Exception as e:
            logger.error(f"Website Puppeteer analysis failed for {url}: {e}")
            return {}
        finally:
            if page:
                await page.close()
    
    async def _detect_tech_stack_puppeteer(self, page: Page) -> List[str]:
        """Detect website technology stack using Puppeteer"""
        try:
            tech_stack = await page.evaluate('''() => {
                const stack = [];
                
                // Check for React
                if (window.React || document.querySelector('[data-reactroot]')) {
                    stack.push('React');
                }
                
                // Check for Vue
                if (window.Vue || document.querySelector('#__nuxt')) {
                    stack.push('Vue.js');
                }
                
                // Check for Angular
                if (window.ng || document.querySelector('[ng-app]')) {
                    stack.push('Angular');
                }
                
                // Check for Next.js
                if (document.querySelector('#__next') || window.__NEXT_DATA__) {
                    stack.push('Next.js');
                }
                
                // Check for WordPress
                if (document.querySelector('meta[name="generator"][content*="WordPress"]')) {
                    stack.push('WordPress');
                }
                
                // Check for jQuery
                if (window.jQuery) {
                    stack.push('jQuery');
                }
                
                return stack;
            }''')
            
            return tech_stack
            
        except Exception as e:
            logger.error(f"Failed to detect tech stack: {e}")
            return []
    
    async def _analyze_github_free(self, project_name: str, coin_symbol: str) -> Dict[str, Any]:
        """Analyze GitHub without API (using web scraping)"""
        try:
            # Search for repository
            search_terms = [
                f"{project_name}-{coin_symbol}",
                f"{project_name}",
                f"{coin_symbol}-token",
                f"{coin_symbol}-crypto"
            ]
            
            for term in search_terms:
                search_url = f"https://github.com/search?q={term}+crypto+blockchain&type=repositories"
                
                page = await self.browser.newPage()
                await page.setUserAgent(self.ua.random)
                
                try:
                    await page.goto(search_url, {'waitUntil': 'networkidle2'})
                    
                    # Get first result
                    repo_link = await page.evaluate('''() => {
                        const firstResult = document.querySelector('.repo-list-item h3 a');
                        return firstResult ? firstResult.href : null;
                    }''')
                    
                    if repo_link:
                        # Visit repository page
                        await page.goto(repo_link, {'waitUntil': 'networkidle2'})
                        
                        # Extract metrics
                        metrics = await page.evaluate('''() => {
                            // Get stars
                            const starsElement = document.querySelector('#repo-stars-counter-star');
                            const stars = starsElement ? starsElement.innerText : '0';
                            
                            // Get last commit info
                            const commitElement = document.querySelector('relative-time');
                            const lastCommit = commitElement ? commitElement.getAttribute('datetime') : '';
                            
                            // Count contributors (from insights link)
                            const contribLink = document.querySelector('a[href*="/graphs/contributors"]');
                            const contribText = contribLink ? contribLink.innerText : '0';
                            
                            return {
                                stars: stars,
                                lastCommit: lastCommit,
                                contributors: contribText
                            };
                        }''')
                        
                        # Parse metrics
                        stars = self._parse_number(metrics['stars'])
                        contributors = self._parse_number(metrics['contributors'].split(' ')[0])
                        
                        # Calculate days since last commit
                        last_commit_days = 0
                        if metrics['lastCommit']:
                            last_commit = datetime.fromisoformat(metrics['lastCommit'].replace('Z', '+00:00'))
                            last_commit_days = (datetime.utcnow() - last_commit.replace(tzinfo=None)).days
                        
                        # Estimate commits in last 30 days
                        commits_30d = 30 - min(last_commit_days, 30) if last_commit_days < 30 else 0
                        
                        await page.close()
                        
                        return {
                            'github_stars': stars,
                            'github_commits_30d': commits_30d,
                            'github_contributors': contributors,
                            'github_last_commit_days': last_commit_days
                        }
                        
                except Exception as e:
                    logger.error(f"Failed to analyze GitHub repo: {e}")
                finally:
                    await page.close()
            
        except Exception as e:
            logger.error(f"GitHub analysis failed: {e}")
        
        return {}
    
    async def _analyze_reddit_free(self, coin_symbol: str, project_name: str) -> Dict[str, Any]:
        """Analyze Reddit without API"""
        try:
            # Try different subreddit patterns
            patterns = [
                coin_symbol.lower(),
                f"{coin_symbol}token",
                f"{coin_symbol}crypto",
                project_name.lower().replace(' ', '')
            ]
            
            for pattern in patterns:
                try:
                    # Use old Reddit for easier parsing
                    url = f"https://old.reddit.com/r/{pattern}"
                    response = self.scraper.get(url, headers={'User-Agent': self.ua.random})
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Extract subscriber count
                        subscribers_elem = soup.find('span', class_='subscribers')
                        if subscribers_elem:
                            subscribers_text = subscribers_elem.find('span', class_='number')
                            subscribers = self._parse_number(subscribers_text.text if subscribers_text else '0')
                            
                            # Get active users
                            active_elem = soup.find('p', class_='users-online')
                            active_users = 0
                            if active_elem:
                                active_match = re.search(r'(\d+,?\d*)', active_elem.text)
                                if active_match:
                                    active_users = self._parse_number(active_match.group(1))
                            
                            # Count recent posts
                            posts = soup.find_all('div', class_='thing', limit=25)
                            post_frequency = len(posts) / 1.0  # Posts per day estimate
                            
                            return {
                                'reddit_subscribers': subscribers,
                                'reddit_active_users': active_users,
                                'reddit_post_frequency': post_frequency
                            }
                
                except Exception as e:
                    logger.warning(f"Failed to check subreddit {pattern}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Reddit analysis failed: {e}")
        
        return {}
    
    async def _analyze_discord_free(self, project_name: str, coin_symbol: str) -> Dict[str, Any]:
        """Analyze Discord server (limited without joining)"""
        try:
            # Discord analysis is limited without API or joining
            # We can check if invite links exist on their website
            # This is a placeholder for basic Discord presence detection
            
            return {
                'discord_members': 0,
                'discord_online_members': 0
            }
            
        except Exception as e:
            logger.error(f"Discord analysis failed: {e}")
            return {}
    
    # Helper methods
    def _parse_number(self, text: str) -> int:
        """Parse numbers with K, M, B suffixes"""
        if not text:
            return 0
        
        text = str(text).strip().upper().replace(',', '')
        
        multipliers = {
            'K': 1000,
            'M': 1000000,
            'B': 1000000000
        }
        
        for suffix, multiplier in multipliers.items():
            if suffix in text:
                try:
                    number = float(re.sub(r'[^0-9.]', '', text.replace(suffix, '')))
                    return int(number * multiplier)
                except:
                    return 0
        
        try:
            # Remove any non-numeric characters except dots
            cleaned = re.sub(r'[^0-9.]', '', text)
            return int(float(cleaned))
        except:
            return 0
    
    def _parse_join_date(self, date_text: str) -> int:
        """Parse Twitter join date to days"""
        if not date_text:
            return 365  # Default 1 year
        
        try:
            # Parse various date formats
            months = {
                'january': 1, 'february': 2, 'march': 3, 'april': 4,
                'may': 5, 'june': 6, 'july': 7, 'august': 8,
                'september': 9, 'october': 10, 'november': 11, 'december': 12
            }
            
            # Extract year
            year_match = re.search(r'20\d{2}', date_text)
            if year_match:
                year = int(year_match.group())
                
                # Extract month
                month = 1
                for month_name, month_num in months.items():
                    if month_name in date_text.lower():
                        month = month_num
                        break
                
                join_date = datetime(year, month, 1)
                days = (datetime.utcnow() - join_date).days
                return max(days, 0)
                
        except Exception as e:
            logger.error(f"Failed to parse join date: {e}")
        
        return 365
    
    def _calculate_engagement_rate(self, tweets: List[Dict], followers: int) -> float:
        """Calculate average engagement rate"""
        if not tweets or followers == 0:
            return 0.0
        
        total_engagement = 0
        valid_tweets = 0
        
        for tweet in tweets:
            if isinstance(tweet, dict):
                engagement = (
                    tweet.get('likes', 0) + 
                    tweet.get('retweets', 0) + 
                    tweet.get('replies', 0)
                )
                if engagement > 0:
                    total_engagement += engagement
                    valid_tweets += 1
        
        if valid_tweets == 0:
            return 0.0
        
        avg_engagement = total_engagement / valid_tweets
        return min(avg_engagement / followers, 1.0)
    
    def _calculate_post_frequency(self, tweets: List[Dict]) -> float:
        """Calculate posts per day"""
        if len(tweets) < 2:
            return 0.0
        
        # Estimate based on number of tweets (assuming they span ~7 days)
        return len(tweets) / 7.0
    
    def _calculate_reply_ratio(self, tweets: List[Dict]) -> float:
        """Calculate ratio of replies to original tweets"""
        if not tweets:
            return 0.0
        
        replies = 0
        for tweet in tweets:
            if isinstance(tweet, dict):
                text = tweet.get('text', '')
                if text.startswith('@') or ' @' in text[:50]:
                    replies += 1
        
        return replies / len(tweets)
    
    async def _analyze_follower_growth(self, handle: str) -> float:
        """Analyze follower growth rate"""
        # This would require historical data
        # For now, return a default moderate growth rate
        return 0.05  # 5% monthly growth
    
    def _calculate_telegram_activity(self, messages: List[Dict]) -> float:
        """Calculate Telegram message frequency"""
        if not messages:
            return 0.0
        
        # Estimate messages per day
        # If we have timestamps, calculate actual frequency
        valid_dates = []
        for msg in messages:
            if msg.get('date'):
                try:
                    date = datetime.fromisoformat(msg['date'].replace('Z', '+00:00'))
                    valid_dates.append(date)
                except:
                    pass
        
        if len(valid_dates) >= 2:
            # Calculate time span
            oldest = min(valid_dates)
            newest = max(valid_dates)
            days = max((newest - oldest).days, 1)
            return len(messages) / days
        
        # Default: assume messages span 1 day
        return len(messages)
    
    def _check_admin_activity(self, messages: List[Dict]) -> float:
        """Check for admin/moderator activity"""
        if not messages:
            return 0.0
        
        admin_messages = 0
        for msg in messages:
            # Check if message is pinned or from admin
            if msg.get('isPinned'):
                admin_messages += 1
            # Could also check author names for admin badges
        
        return admin_messages / max(len(messages), 1)
    
    async def _estimate_telegram_bots(self, messages: List[Dict], member_count: int) -> float:
        """Estimate bot percentage in Telegram"""
        if not messages or member_count == 0:
            return 0.0
        
        # Analyze message patterns
        suspicious_patterns = 0
        unique_authors = set()
        
        for msg in messages:
            author = msg.get('author', '')
            text = msg.get('text', '')
            
            unique_authors.add(author)
            
            # Check for bot-like patterns
            if any(pattern in text.lower() for pattern in ['join now', 'click here', 'dm me']):
                suspicious_patterns += 1
        
        # Calculate bot indicators
        author_diversity = len(unique_authors) / max(len(messages), 1)
        pattern_ratio = suspicious_patterns / max(len(messages), 1)
        
        # Estimate bot percentage
        bot_score = (1 - author_diversity) * 0.5 + pattern_ratio * 0.5
        return min(bot_score, 1.0)
    
    async def _check_domain_age(self, url: str) -> int:
        """Check domain age using archive.org"""
        try:
            domain = urlparse(url).netloc
            
            # Query Wayback Machine
            wayback_url = f"https://archive.org/wayback/available?url={domain}"
            
            response = self.scraper.get(wayback_url)
            if response.status_code == 200:
                data = response.json()
                
                if data.get('archived_snapshots', {}).get('closest', {}).get('timestamp'):
                    timestamp = data['archived_snapshots']['closest']['timestamp']
                    # Parse timestamp (YYYYMMDDhhmmss)
                    year = int(timestamp[:4])
                    month = int(timestamp[4:6])
                    day = int(timestamp[6:8])
                    
                    first_seen = datetime(year, month, day)
                    age_days = (datetime.utcnow() - first_seen).days
                    return max(age_days, 0)
                    
        except Exception as e:
            logger.error(f"Failed to check domain age: {e}")
        
        return 0
    
    def _calculate_website_security_score(self, has_ssl: bool, is_valid: bool, 
                                        has_audit: bool, red_flags: int) -> float:
        """Calculate website security score"""
        score = 0.0
        
        if has_ssl:
            score += 0.3
        if is_valid:
            score += 0.2
        if has_audit:
            score += 0.3
        
        # Deduct for red flags
        score -= red_flags * 0.1
        
        return max(0, min(score, 1.0))
    
    def _calculate_credibility_score(self, metrics: SocialMetrics) -> float:
        """Calculate overall credibility score"""
        weights = {
            'twitter': 0.25,
            'telegram': 0.20,
            'website': 0.25,
            'github': 0.20,
            'community': 0.10
        }
        
        scores = {}
        
        # Twitter score
        scores['twitter'] = 0.0
        if metrics.twitter_followers > 1000:
            scores['twitter'] += 0.2
        if metrics.twitter_followers > 10000:
            scores['twitter'] += 0.2
        if metrics.twitter_verified:
            scores['twitter'] += 0.3
        if metrics.twitter_engagement_rate > 0.02:
            scores['twitter'] += 0.2
        if metrics.twitter_account_age_days > 365:
            scores['twitter'] += 0.1
        
        # Telegram score
        scores['telegram'] = 0.0
        if metrics.telegram_members > 1000:
            scores['telegram'] += 0.3
        if metrics.telegram_message_frequency > 50:
            scores['telegram'] += 0.2
        if metrics.telegram_admin_activity > 0.05:
            scores['telegram'] += 0.2
        if metrics.telegram_bot_percentage < 0.3:
            scores['telegram'] += 0.3
        
        # Website score
        scores['website'] = 0.0
        if metrics.website_valid:
            scores['website'] += 0.2
        if metrics.website_ssl:
            scores['website'] += 0.2
        if metrics.website_age_days > 180:
            scores['website'] += 0.3
        if metrics.website_security_score > 0.7:
            scores['website'] += 0.3
        
        # GitHub score
        scores['github'] = 0.0
        if metrics.github_stars > 50:
            scores['github'] += 0.3
        if metrics.github_commits_30d > 10:
            scores['github'] += 0.3
        if metrics.github_contributors > 5:
            scores['github'] += 0.2
        if metrics.github_last_commit_days < 30:
            scores['github'] += 0.2
        
        # Community score (Reddit + Discord)
        scores['community'] = 0.0
        if metrics.reddit_subscribers > 1000:
            scores['community'] += 0.5
        if metrics.discord_members > 1000:
            scores['community'] += 0.5
        
        # Calculate weighted average
        total_score = sum(scores[key] * weights[key] for key in weights)
        
        return min(total_score, 1.0)
    
    def _calculate_bot_score(self, metrics: SocialMetrics) -> float:
        """Calculate bot activity score (higher = more bots)"""
        bot_indicators = 0.0
        
        # Twitter bot indicators
        if metrics.twitter_reply_ratio > 0.7:
            bot_indicators += 0.2
        if metrics.twitter_engagement_rate > 0.15:  # Unusually high
            bot_indicators += 0.2
        if metrics.twitter_followers > 50000 and metrics.twitter_engagement_rate < 0.001:
            bot_indicators += 0.3
        
        # Telegram bot indicators
        if metrics.telegram_bot_percentage > 0.5:
            bot_indicators += 0.3
        
        return min(bot_indicators, 1.0)
    
    def _calculate_community_health(self, metrics: SocialMetrics) -> float:
        """Calculate community health score"""
        health_indicators = 0.0
        
        # Engagement health
        if 0.005 < metrics.twitter_engagement_rate < 0.1:
            health_indicators += 0.2
        
        # Activity health
        if 10 < metrics.telegram_message_frequency < 200:
            health_indicators += 0.2
        
        # Development health
        if metrics.github_commits_30d > 20:
            health_indicators += 0.2
        if metrics.github_last_commit_days < 7:
            health_indicators += 0.1
        
        # Community diversity
        if metrics.reddit_subscribers > 0 and metrics.telegram_members > 0:
            health_indicators += 0.2
        
        # Account maturity
        if metrics.twitter_account_age_days > 180:
            health_indicators += 0.1
        
        return min(health_indicators, 1.0)
    
    def _calculate_risk_score(self, metrics: SocialMetrics) -> float:
        """Calculate risk score (higher = more risky)"""
        risk_factors = 0.0
        
        # Low credibility
        if metrics.overall_credibility_score < 0.3:
            risk_factors += 0.3
        
        # High bot activity
        if metrics.bot_activity_score > 0.7:
            risk_factors += 0.3
        
        # Poor community health
        if metrics.community_health_score < 0.3:
            risk_factors += 0.2
        
        # New project with aggressive marketing
        if metrics.website_age_days < 30 and metrics.twitter_followers > 50000:
            risk_factors += 0.2
        
        return min(risk_factors, 1.0)
    
    async def _find_and_analyze_twitter(self, project_name: str, coin_symbol: str) -> Dict[str, Any]:
        """Find Twitter account through web search"""
        # Implementation would search for Twitter account
        return {}
    
    async def _find_and_analyze_telegram(self, project_name: str, coin_symbol: str) -> Dict[str, Any]:
        """Find Telegram through web search"""
        # Implementation would search for Telegram
        return {}
    
    async def _find_and_analyze_website(self, project_name: str, coin_symbol: str, 
                                      contract_address: Optional[str]) -> Dict[str, Any]:
        """Find official website through various sources"""
        # Implementation would search for website
        return {}
    
    async def shutdown(self):
        """Clean shutdown"""
        if self.browser:
            await self.browser.close()
        if self.redis_client:
            await self.redis_client.close()