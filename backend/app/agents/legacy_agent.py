from app.core.config import settings
from typing import List
from app.schemas import Claim, VerificationResult, VerificationStatus
from datetime import datetime

# Source filtering configuration
WHITELIST_SOURCES = [
    "animalpolitico.com",
    "aristeguinoticias.com",
    "eluniversal.com.mx",
    "proceso.com.mx",
    "reforma.com",
    "ine.mx",
    "banxico.org.mx",
    "dof.gob.mx"
]

BLACKLIST_SOURCES = [
    "deforma.com",  # Satire
    # "youtube.com",  # Now supported via YouTube scraper with transcription
    "tiktok.com",   # Hard to parse video content
]
from app.services.scrapers.web_scraper import MockScraper, TwitterScraper, GoogleNewsScraper, FacebookScraper, InstagramScraper
from app.services.duplicate_detection import DuplicateDetector
import anthropic
import openai
import json
import asyncio
from app.services.search_service import search_web
from app.services.claim_extraction import ClaimExtractionService
from app.services.verification import VerificationService



class FactChecker:
    def __init__(self):
        self.mock_scraper = MockScraper()
        self.twitter_scraper = TwitterScraper()
        self.google_news_scraper = GoogleNewsScraper()
        self.facebook_scraper = FacebookScraper()
        self.instagram_scraper = InstagramScraper()
        self.duplicate_detector = DuplicateDetector()
        
        # Initialize Anthropic (primary)
        anthropic_key = settings.ANTHROPIC_API_KEY
        if anthropic_key:
            try:
                self.anthropic_client = anthropic.Anthropic(api_key=anthropic_key)
                print("✓ Anthropic API initialized (primary)")
            except Exception as e:
                print(f"Warning: Failed to initialize Anthropic client: {e}")
                self.anthropic_client = None
        else:
            self.anthropic_client = None
            print("Warning: Anthropic API key not found.")
        
        # Initialize OpenAI (backup)
        openai_key = settings.OPENAI_API_KEY
        if openai_key:
            try:
                self.openai_client = openai.OpenAI(api_key=openai_key)
                print("✓ OpenAI API initialized (backup)")
            except Exception as e:
                print(f"Warning: Failed to initialize OpenAI client: {e}")
                self.openai_client = None
        else:
            self.openai_client = None
            print("Warning: OpenAI API key not found.")
        
        # Check if at least one client is available
        if not self.anthropic_client and not self.openai_client:
            print("⚠️  No AI API keys found. Fact-checking will use mock logic.")
            
        self.claim_service = ClaimExtractionService(self.anthropic_client, self.openai_client)
        self.verification_service = VerificationService(self.anthropic_client, self.openai_client)
    
    def _filter_sources(self, sources: List[str]) -> List[str]:
        """Filter sources based on whitelist/blacklist"""
        filtered = []
        for url in sources:
            # Check blacklist first
            if any(blocked in url.lower() for blocked in BLACKLIST_SOURCES):
                continue
            # Prioritize whitelist
            if any(trusted in url.lower() for trusted in WHITELIST_SOURCES):
                filtered.insert(0, url)  # Put whitelisted sources first
            else:
                filtered.append(url)
        return filtered[:5]  # Limit to top 5 sources
        
    async def process_recent_posts(self, keywords: List[str] = None) -> List[Claim]:
        if not keywords:
            # Use default keywords from configuration
            from app.config.scraping_keywords import DEFAULT_KEYWORDS
            keywords = DEFAULT_KEYWORDS

        # Fetch from all sources concurrently
        results = await asyncio.gather(
            self.twitter_scraper.fetch_posts(keywords),
            self.google_news_scraper.fetch_posts(keywords),
            self.facebook_scraper.fetch_posts(keywords),
            self.instagram_scraper.fetch_posts(keywords),
            return_exceptions=True
        )

        twitter_posts = results[0] if isinstance(results[0], list) else []
        google_posts = results[1] if isinstance(results[1], list) else []
        facebook_posts = results[2] if isinstance(results[2], list) else []
        instagram_posts = results[3] if isinstance(results[3], list) else []

        all_posts = twitter_posts + google_posts + facebook_posts + instagram_posts

        if not all_posts:
            print("No live posts found (or keys missing). Using Mock data.")
            all_posts = await self.mock_scraper.fetch_posts(keywords)

        # Convert SocialPost objects to dicts for duplicate detection
        posts_dicts = []
        for post in all_posts:
            post_dict = {
                'id': post.id,
                'platform': post.platform,
                'content': post.content,
                'author': post.author,
                'timestamp': post.timestamp,
                'url': post.url,
                'engagement_metrics': post.engagement_metrics,
                'media_urls': post.media_urls,
                'context_data': post.context_data
            }
            posts_dicts.append(post_dict)

        # Remove duplicates across platforms (db not currently used but kept for future enhancements)
        deduplicated_posts = self.duplicate_detector.find_duplicates(posts_dicts, db=None)

        print(f"Found {len(all_posts)} posts, {len(deduplicated_posts)} unique after deduplication")

        # Convert back to SocialPost objects
        all_posts = []
        for post_dict in deduplicated_posts:
            from app.schemas import SocialPost
            post = SocialPost(
                id=post_dict['id'],
                platform=post_dict['platform'],
                content=post_dict['content'],
                author=post_dict['author'],
                timestamp=post_dict['timestamp'],
                url=post_dict['url'],
                engagement_metrics=post_dict.get('engagement_metrics'),
                media_urls=post_dict.get('media_urls'),
                context_data=post_dict.get('context_data')
            )
            all_posts.append(post)

        claims = []
        
        # Limit to first 1 post for instant response
        for post in all_posts[:1]:
            # 1. Extract Claim
            claim_text = await self._extract_claim(post.content)
            if claim_text == "SKIP":
                continue  # Skip non-factual content
            
            # 2. Search for Evidence
            evidence_links = await search_web(claim_text)
            filtered_evidence = self._filter_sources(evidence_links)
            
            # 3. Verify Claim
            verification = await self._verify_claim(claim_text, filtered_evidence)
            
            claims.append(Claim(
                id=post.id,
                original_text=post.content,
                claim_text=claim_text,
                verification=verification,
                source_post=post
            ))
            
        return claims
    
    async def process_recent_posts_streaming(self, keywords: List[str] = None):
        """Stream claims as they're processed (generator)"""
        if not keywords:
            # Use default keywords from configuration
            from app.config.scraping_keywords import DEFAULT_KEYWORDS
            keywords = DEFAULT_KEYWORDS

        # Fetch from all sources concurrently
        results = await asyncio.gather(
            self.twitter_scraper.fetch_posts(keywords),
            self.google_news_scraper.fetch_posts(keywords),
            self.facebook_scraper.fetch_posts(keywords),
            self.instagram_scraper.fetch_posts(keywords),
            return_exceptions=True
        )

        twitter_posts = results[0] if isinstance(results[0], list) else []
        google_posts = results[1] if isinstance(results[1], list) else []
        facebook_posts = results[2] if isinstance(results[2], list) else []
        instagram_posts = results[3] if isinstance(results[3], list) else []

        all_posts = twitter_posts + google_posts + facebook_posts + instagram_posts

        if not all_posts:
            print("No live posts found (or keys missing). Using Mock data.")
            all_posts = await self.mock_scraper.fetch_posts(keywords)

        # Convert SocialPost objects to dicts for duplicate detection
        posts_dicts = []
        for post in all_posts:
            post_dict = {
                'id': post.id,
                'platform': post.platform,
                'content': post.content,
                'author': post.author,
                'timestamp': post.timestamp,
                'url': post.url,
                'engagement_metrics': post.engagement_metrics,
                'media_urls': post.media_urls,
                'context_data': post.context_data
            }
            posts_dicts.append(post_dict)

        # Remove duplicates across platforms (db not currently used but kept for future enhancements)
        deduplicated_posts = self.duplicate_detector.find_duplicates(posts_dicts, db=None)

        print(f"Found {len(all_posts)} posts, {len(deduplicated_posts)} unique after deduplication")

        # Convert back to SocialPost objects
        all_posts = []
        for post_dict in deduplicated_posts:
            from app.schemas import SocialPost
            post = SocialPost(
                id=post_dict['id'],
                platform=post_dict['platform'],
                content=post_dict['content'],
                author=post_dict['author'],
                timestamp=post_dict['timestamp'],
                url=post_dict['url'],
                engagement_metrics=post_dict.get('engagement_metrics'),
                media_urls=post_dict.get('media_urls'),
                context_data=post_dict.get('context_data')
            )
            all_posts.append(post)

        # Yield claims as they're processed
        for post in all_posts[:3]:
            claim_text = await self._extract_claim(post.content)
            if claim_text == "SKIP":
                continue
            
            evidence_links = await search_web(claim_text)
            filtered_evidence = self._filter_sources(evidence_links)
            verification = await self._verify_claim(claim_text, filtered_evidence)
            
            claim = Claim(
                id=post.id,
                original_text=post.content,
                claim_text=claim_text,
                verification=verification,
                source_post=post
            )
            
            yield claim  # Yield each claim as it's ready

    async def _extract_claim(self, content: str) -> str:
        return await self.claim_service.extract_claim(content)

    async def _verify_claim(self, claim: str, evidence: List[str]) -> VerificationResult:
        return await self.verification_service.verify_claim(claim, evidence)
    
    async def _verify_claim_with_evidence(
        self,
        claim: str,
        evidence_urls: List[str],
        evidence_texts: List[str],
        context: dict = None
    ) -> VerificationResult:
        return await self.verification_service.verify_claim_with_evidence(claim, evidence_urls, evidence_texts, context)
    
    async def _extract_entities(self, claim_text: str) -> List[tuple]:
        return await self.claim_service.extract_entities(claim_text)
    
    async def _extract_topics(self, claim_text: str, available_topics: List[dict] = None) -> List[str]:
        return await self.claim_service.extract_topics(claim_text, available_topics)

    async def answer_question_about_claim(self, context: str, question: str) -> str:
        """Answer a follow-up question about a claim using context"""
        if not self.anthropic_client and not self.openai_client:
            return "Lo siento, no puedo responder preguntas en este momento (AI no disponible)."
            
        system_prompt = """You are a helpful assistant for FactCheckr MX.
Answer the user's question based strictly on the provided verification context.
If the answer is not in the context, say so politely.
Keep answers concise and in Mexican Spanish."""
        
        user_prompt = f"""CONTEXT:
{context}

QUESTION: "{question}"

ANSWER:"""
        
        # Try Anthropic first
        if self.anthropic_client:
            try:
                response = self.anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20240620",
                    max_tokens=300,
                    temperature=0.3,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                return response.content[0].text.strip()
            except Exception as e:
                print(f"⚠️  Chat error (Anthropic): {e}")
        
        # Fallback to OpenAI
        if self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=300,
                    temperature=0.3
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                print(f"⚠️  Chat error (OpenAI): {e}")
                
        return "Lo siento, hubo un error al procesar tu pregunta."