"""
Scraping Keywords Configuration

Centralized keyword management for scraping Mexican political content.
Keywords are organized by priority and category.
"""

# High Priority Keywords (Always Active)
# These are the most important and should always be included
HIGH_PRIORITY_KEYWORDS = [
    "Reforma Judicial",      # Major current topic - judicial reform
    "Sheinbaum",             # Current President
    "Claudia Sheinbaum",     # Full name variant
    "Morena",                # Ruling party
    "política mexicana",     # General Mexican politics
]

# Medium Priority Keywords (Core Political Topics)
MEDIUM_PRIORITY_KEYWORDS = [
    "AMLO",                  # Previous President (still relevant)
    "López Obrador",         # Full name variant
    "Congreso México",       # Mexican Congress
    "INE",                   # National Electoral Institute
    "Suprema Corte",         # Supreme Court
    "Senado México",          # Senate
    "Cámara Diputados",      # Chamber of Deputies
]

# Low Priority Keywords (Important but Less Frequent)
LOW_PRIORITY_KEYWORDS = [
    # Opposition Parties
    "PAN",                   # National Action Party
    "PRI",                   # Institutional Revolutionary Party
    "PRD",                   # Party of the Democratic Revolution
    "Movimiento Ciudadano",  # Citizens' Movement
    
    # Key Institutions
    "Pemex",                 # State oil company
    "CFE",                   # State electricity company
    "Banco de México",       # Central Bank
    "SHCP",                  # Finance Ministry
    
    # Policy Areas
    "Seguridad México",      # Security
    "Economía México",       # Economy
    "Corrupción México",     # Corruption
    "Migración México",      # Migration
]

# Extended Keywords (Comprehensive Coverage)
EXTENDED_KEYWORDS = [
    # Government Officials
    "Marcelo Ebrard",
    "Ricardo Monreal",
    "Ernesto Cordero",
    "Xóchitl Gálvez",
    
    # Policy Topics
    "Reforma Electoral",
    "Presupuesto México",
    "Deuda pública",
    "Inflación México",
    "Desempleo México",
    
    # General Terms
    "gobierno México",
    "noticias México",
    "México política",
    "elecciones México",
]

# All Keywords Combined (for comprehensive scraping)
ALL_KEYWORDS = (
    HIGH_PRIORITY_KEYWORDS +
    MEDIUM_PRIORITY_KEYWORDS +
    LOW_PRIORITY_KEYWORDS
)

# Default Keywords (used if no configuration specified)
# Balanced mix of high and medium priority
DEFAULT_KEYWORDS = (
    HIGH_PRIORITY_KEYWORDS +
    MEDIUM_PRIORITY_KEYWORDS[:5]  # Top 5 medium priority
)

# Keywords by Category (for topic-based scraping)
KEYWORDS_BY_CATEGORY = {
    "executive": [
        "Sheinbaum",
        "Claudia Sheinbaum",
        "AMLO",
        "López Obrador",
        "gobierno México",
    ],
    "judicial": [
        "Reforma Judicial",
        "Suprema Corte",
        "jueces México",
        "poder judicial",
    ],
    "legislative": [
        "Congreso México",
        "Senado México",
        "Cámara Diputados",
        "iniciativa de ley",
    ],
    "parties": [
        "Morena",
        "PAN",
        "PRI",
        "PRD",
        "Movimiento Ciudadano",
    ],
    "institutions": [
        "INE",
        "Pemex",
        "CFE",
        "Banco de México",
        "SHCP",
    ],
    "policy": [
        "Seguridad México",
        "Economía México",
        "Salud México",
        "Educación México",
        "Corrupción México",
        "Migración México",
    ],
    "elections": [
        "elecciones México",
        "INE",
        "votaciones",
        "campaña electoral",
    ],
}


def get_keywords_for_scraping(priority: str = "default") -> list:
    """
    Get keywords for scraping based on priority level.
    
    Args:
        priority: "high", "medium", "low", "all", or "default"
    
    Returns:
        List of keywords to use for scraping
    """
    if priority == "high":
        return HIGH_PRIORITY_KEYWORDS.copy()
    elif priority == "medium":
        return (HIGH_PRIORITY_KEYWORDS + MEDIUM_PRIORITY_KEYWORDS).copy()
    elif priority == "low":
        return (HIGH_PRIORITY_KEYWORDS + MEDIUM_PRIORITY_KEYWORDS + LOW_PRIORITY_KEYWORDS).copy()
    elif priority == "all":
        return ALL_KEYWORDS.copy()
    else:  # default
        return DEFAULT_KEYWORDS.copy()


def get_keywords_by_category(categories: list = None) -> list:
    """
    Get keywords for specific categories.
    
    Args:
        categories: List of category names (e.g., ["executive", "judicial"])
                   If None, returns all categories
    
    Returns:
        List of unique keywords from specified categories
    """
    if categories is None:
        categories = list(KEYWORDS_BY_CATEGORY.keys())
    
    keywords = []
    for category in categories:
        if category in KEYWORDS_BY_CATEGORY:
            keywords.extend(KEYWORDS_BY_CATEGORY[category])
    
    # Remove duplicates while preserving order
    seen = set()
    unique_keywords = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            unique_keywords.append(kw)
    
    return unique_keywords


def get_keyword_statistics() -> dict:
    """Get statistics about keyword configuration"""
    return {
        "high_priority_count": len(HIGH_PRIORITY_KEYWORDS),
        "medium_priority_count": len(MEDIUM_PRIORITY_KEYWORDS),
        "low_priority_count": len(LOW_PRIORITY_KEYWORDS),
        "total_keywords": len(ALL_KEYWORDS),
        "categories": list(KEYWORDS_BY_CATEGORY.keys()),
        "keywords_by_category": {
            cat: len(kws) for cat, kws in KEYWORDS_BY_CATEGORY.items()
        }
    }

