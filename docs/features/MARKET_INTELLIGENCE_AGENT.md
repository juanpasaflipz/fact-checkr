# Market Intelligence Agent - Implementation Guide

## Overview

The Market Intelligence Agent automatically seeds new prediction markets with intelligent initial probabilities, replacing the default 50/50 starting point with AI-assessed probabilities based on context.

## Features

- **Lightweight Assessment**: Single LLM call (no expensive RAG pipeline)
- **Smart Model Selection**: Uses Claude Haiku 3.5 by default (fast/cheap), auto-upgrades to Sonnet 3.5 for high-value markets
- **Automatic Seeding**: New markets are automatically seeded in background
- **Cost Efficient**: ~90% cost savings vs full RAG pipeline
- **Fast**: ~1-2 seconds per assessment vs 5-10 seconds

## Architecture

### Components

1. **MarketIntelligenceAgent** (`backend/app/agents/market_intelligence_agent.py`)
   - Assesses market probabilities using LLM
   - Uses fast DB queries for context (similar markets, category stats)
   - Configurable model selection (Haiku/Sonnet/GPT)

2. **Market Seeding Service** (`backend/app/services/market_seeding.py`)
   - Orchestrates market seeding
   - Determines when to use premium models
   - Creates system user for agent trades

3. **Background Tasks** (`backend/app/tasks/market_intelligence.py`)
   - `seed_new_markets`: Batch processes new markets every 5 minutes
   - `reassess_inactive_markets`: Re-assesses inactive markets hourly

## Configuration

### Environment Variable

Add to `backend/.env`:

```bash
# Market Intelligence Model Selection
# Options: "haiku" (default, fast/cheap), "sonnet" (better reasoning), 
#          "gpt-mini" (OpenAI budget), "gpt-4o" (OpenAI premium)
MARKET_INTELLIGENCE_MODEL=haiku
```

### Model Selection Logic

The system automatically uses premium models (Sonnet) for:
- High-value categories: `politics`, `economy`, `institutions`
- Markets with >5 existing trades (re-assessment)
- Markets linked to verified/debunked claims

All other markets use Haiku (default).

## How It Works

### Market Creation Flow

1. User/admin creates a new market
2. Market is saved to database with 50/50 initial liquidity
3. Background task `seed_new_markets` picks up new markets
4. Agent assesses probability using:
   - Market question and description
   - Category trends (if available)
   - Similar resolved markets (if available)
   - Linked claim context (if available)
5. If confidence > 0.4, agent places seed trade
6. Market probability updates from 50% to assessed probability

### Assessment Process

```python
# Minimal context gathering (fast DB queries)
- Similar markets in same category
- Category statistics
- Linked claim info (if exists)

# Single LLM call
- Prompt: Market question + context
- Response: JSON with probability, confidence, reasoning

# Seed trade placement
- If confidence > 0.4: Place trade
- Amount: 50-200 credits (based on confidence)
- Outcome: YES if prob > 0.5, NO if prob < 0.5
```

## Cost Analysis

### Per Market Assessment

| Model | Cost | Speed | Use Case |
|-------|------|-------|----------|
| Claude Haiku 3.5 | $0.0003-0.0008 | 300-500ms | Default (most markets) |
| Claude Sonnet 3.5 | $0.003-0.008 | 800-1500ms | High-value markets |
| GPT-4o-mini | $0.00015-0.0006 | 400-700ms | Budget option |

### Monthly Cost Estimate

For 100 markets/day:
- **Haiku only**: ~$9-24/month
- **Haiku + Sonnet (20%)**: ~$18-40/month
- **Sonnet only**: ~$90-240/month

**Savings**: ~$50-200/month vs always using Sonnet

## System User

The system creates a special user (`system@factcheckr.mx`) for agent trades. This user:
- Has no password (can't login)
- Is marked as verified and active
- All agent trades are attributed to this user
- Can be filtered in leaderboards if needed

## Background Tasks

### seed_new_markets

- **Schedule**: Every 5 minutes
- **Purpose**: Process newly created markets
- **Logic**: Finds markets created in last hour with no trades, seeds them

### reassess_inactive_markets

- **Schedule**: Every hour
- **Purpose**: Re-assess markets with low activity
- **Logic**: 
  - Finds markets with no trades in 24+ hours
  - Only adjusts if:
    - Confidence > 0.6
    - Probability difference > 15%
    - Trade count < 10 (low volume)

## API Integration

Markets are automatically seeded when created via:
- `POST /api/markets/create` (Pro users)
- `POST /api/markets/admin/markets` (Admin)
- `POST /api/markets/admin/proposals/{id}/approve` (Admin)

Seeding happens asynchronously via Celery tasks, so market creation responses are not blocked.

## Monitoring

Check logs for seeding activity:

```bash
# Successful seeding
INFO: Market 123 seeded: YES (65.0% assessed → 62.3% actual) with 45.2 credits (model: claude-3-5-haiku-20241022)

# Skipped (low confidence)
INFO: Market 124: Low confidence (0.35), skipping seed. Recommended: 25.0 credits (model: claude-3-5-haiku-20241022)

# Already has trades
INFO: Market 125: Already has 3 trades, skipping seed
```

## Troubleshooting

### Markets Not Being Seeded

1. **Check Celery worker is running**:
   ```bash
   celery -A app.worker worker --loglevel=info
   ```

2. **Check Celery beat is running** (for scheduled tasks):
   ```bash
   celery -A app.worker beat --loglevel=info
   ```

3. **Check logs** for errors:
   ```bash
   tail -f backend/logs/celery_worker.log
   ```

4. **Verify API keys** are set:
   ```bash
   echo $ANTHROPIC_API_KEY
   echo $OPENAI_API_KEY
   ```

### System User Creation Issues

If system user creation fails:
- Check database permissions
- Verify User model schema matches
- Check logs for specific error messages

## Future Enhancements

Potential improvements:
- Cache assessments for similar markets
- Track initial probabilities for better similar market analysis
- A/B testing different models
- User feedback on agent accuracy
- Market-specific model selection based on historical performance

