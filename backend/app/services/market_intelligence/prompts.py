"""
Prompts for the Market Synthesizer Agent.

These prompts are carefully engineered to produce calibrated,
well-reasoned predictions with transparent reasoning chains.
"""

SYSTEM_PROMPT = """You are an expert prediction market analyst specializing in Mexican politics, economics, and social events. Your role is to synthesize multiple data sources and produce calibrated probability estimates.

## Your Core Principles

1. **Calibration**: When you say 70% probability, you should be right about 70% of the time. Avoid overconfidence.

2. **Transparency**: Always explain your reasoning step by step. Users should understand WHY you predict what you predict.

3. **Risk Awareness**: Identify uncertainties and risks that could invalidate your prediction.

4. **Data-Driven**: Base predictions on the evidence provided, not assumptions. If data is insufficient, lower your confidence.

5. **Mexican Context**: You understand Mexican political dynamics, institutions (INE, SCJN, Banxico), party landscape (Morena, PAN, PRI, MC), and economic context.

## Output Format

You MUST respond with valid JSON in this exact format:
{
    "probability": 0.XX,  // 0.00 to 1.00, probability of YES outcome
    "confidence": 0.XX,   // 0.00 to 1.00, your confidence in this prediction
    "key_factors": [
        {
            "factor": "Description of factor",
            "impact": 0.XX,  // -1.0 to 1.0 (negative = supports NO, positive = supports YES)
            "confidence": 0.XX,
            "source": "news|social|historical|economic|political",
            "evidence": "Specific evidence supporting this factor"
        }
    ],
    "risk_factors": [
        {
            "risk": "Description of risk",
            "severity": "low|medium|high|critical",
            "probability": 0.XX,  // Likelihood this risk materializes
            "impact_on_prediction": "How this would change the prediction"
        }
    ],
    "reasoning_chain": "Step-by-step reasoning...",
    "summary": "One paragraph human-readable summary in Spanish"
}

## Calibration Guidelines

- 50% = Complete uncertainty, could go either way
- 60-70% = Lean toward one outcome, but significant uncertainty
- 70-80% = Moderately confident, good supporting evidence
- 80-90% = High confidence, strong evidence, few risks
- 90%+ = Near certain, overwhelming evidence (use sparingly)

When data is limited or conflicting, stay closer to 50% and increase confidence interval.
"""

ANALYSIS_PROMPT_TEMPLATE = """## Market Question
{market_question}

## Market Description
{market_description}

## Category
{category}

## Resolution Criteria
{resolution_criteria}

## Current Market State
- Current probability from trading: {current_probability}%
- Trading volume: {volume} credits
- Days until close: {days_until_close}

---

## NEWS DATA
{news_summary}

## SOCIAL MEDIA SENTIMENT
{sentiment_summary}

## SIMILAR HISTORICAL MARKETS
{similar_markets_summary}

---

## Your Task

Analyze all the data above and produce a probability estimate for the YES outcome.

Consider:
1. What does the news data suggest about the likely outcome?
2. What is public sentiment saying, and how reliable is it?
3. How did similar markets resolve, and is this market comparable?
4. What are the key uncertainties and risks?
5. Is the current market price (from trading) over or under-valuing the true probability?

Produce your analysis in the required JSON format.
"""


def format_news_for_prompt(news_data: dict) -> str:
    """Format news aggregation data for the prompt."""
    if not news_data:
        return "No news data available for this market."
    
    lines = [
        f"- Articles analyzed: {news_data.get('volume', 0)}",
        f"- News signal: {news_data.get('credibility_weighted_signal', 0):.2f} (-1 = negative, +1 = positive)",
        f"- Data freshness: {news_data.get('freshness_hours', 0):.1f} hours old",
        "",
        "Key articles:"
    ]
    
    articles = news_data.get('articles', [])[:5]
    for i, article in enumerate(articles, 1):
        lines.append(
            f"{i}. [{article.get('source', 'Unknown')}] {article.get('title', 'No title')}"
            f"\n   Stance: {article.get('stance', 0):.2f}, "
            f"Credibility: {article.get('credibility_score', 0):.2f}"
            f"\n   Summary: {article.get('summary', 'No summary')[:200]}..."
        )
    
    if not articles:
        lines.append("No relevant articles found.")
    
    return "\n".join(lines)


def format_sentiment_for_prompt(sentiment_data: dict) -> str:
    """Format sentiment aggregation data for the prompt."""
    if not sentiment_data:
        return "No social media sentiment data available."
    
    lines = [
        f"- Posts analyzed: {sentiment_data.get('posts_analyzed', 0)}",
        f"- Weighted sentiment: {sentiment_data.get('weighted_sentiment', 0):.2f} (-1 = negative, +1 = positive)",
        f"- Sentiment confidence: {sentiment_data.get('sentiment_confidence', 0):.2f}",
        f"- Momentum (trend): {sentiment_data.get('momentum', 0):.2f}",
        f"- Bot-filtered posts: {sentiment_data.get('bot_filtered_count', 0)}",
        f"- Data freshness: {sentiment_data.get('freshness_hours', 0):.1f} hours old",
        "",
        "Platform breakdown:"
    ]
    
    platform_breakdown = sentiment_data.get('platform_breakdown', {})
    for platform, sentiment in platform_breakdown.items():
        lines.append(f"  - {platform}: {sentiment:.2f}")
    
    lines.append("\nTop influential posts:")
    top_posts = sentiment_data.get('top_posts', [])[:3]
    for i, post in enumerate(top_posts, 1):
        lines.append(
            f"{i}. [{post.get('platform', 'Unknown')}] @{post.get('author', 'Unknown')}"
            f"\n   Sentiment: {post.get('sentiment', 0):.2f}, "
            f"Engagement: {post.get('engagement_score', 0):.2f}"
            f"\n   Content: {post.get('content', '')[:150]}..."
        )
    
    if not top_posts:
        lines.append("No significant posts found.")
    
    return "\n".join(lines)


def format_similar_markets_for_prompt(similar_markets: list) -> str:
    """Format similar historical markets for the prompt."""
    if not similar_markets:
        return "No similar historical markets found for comparison."
    
    lines = ["Similar markets that have already resolved:"]
    
    for i, market in enumerate(similar_markets, 1):
        outcome = "SÍ" if market.get('outcome') == 'yes' else "NO"
        lines.append(
            f"\n{i}. \"{market.get('question', 'Unknown question')}\""
            f"\n   Outcome: {outcome}"
            f"\n   Final probability before resolution: {market.get('final_probability', 0.5)*100:.0f}%"
            f"\n   Similarity score: {market.get('similarity_score', 0):.2f}"
            f"\n   Key factors: {', '.join(market.get('key_factors', [])[:3])}"
        )
    
    return "\n".join(lines)


def build_analysis_prompt(
    market_question: str,
    market_description: str,
    category: str,
    resolution_criteria: str,
    current_probability: float,
    volume: float,
    days_until_close: int,
    news_data: dict = None,
    sentiment_data: dict = None,
    similar_markets: list = None
) -> str:
    """Build the complete analysis prompt."""
    return ANALYSIS_PROMPT_TEMPLATE.format(
        market_question=market_question,
        market_description=market_description or "No description provided.",
        category=category or "General",
        resolution_criteria=resolution_criteria or "Standard binary resolution.",
        current_probability=f"{current_probability * 100:.1f}",
        volume=f"{volume:,.0f}",
        days_until_close=days_until_close if days_until_close > 0 else "Unknown",
        news_summary=format_news_for_prompt(news_data),
        sentiment_summary=format_sentiment_for_prompt(sentiment_data),
        similar_markets_summary=format_similar_markets_for_prompt(similar_markets or [])
    )


# Lightweight analysis prompt (no LLM, just for structuring data)
LIGHTWEIGHT_ANALYSIS_TEMPLATE = """
Quick market signal summary:
- News signal: {news_signal:.2f}
- Sentiment signal: {sentiment_signal:.2f}
- Historical base rate: {base_rate:.2f}
- Current market: {market_prob:.2f}

Combined lightweight signal: {combined_signal:.2f}
"""
