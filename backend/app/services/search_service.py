from app.core.config import settings
import httpx
from typing import List, Dict, Any

async def search_web(query: str) -> List[str]:
    """Search the web using Serper API for evidence gathering (returns URLs only)"""
    serper_api_key = settings.SERPER_API_KEY
    
    if not serper_api_key:
        print(f"Warning: SERPER_API_KEY not found. Using mock results for: {query}")
        return [
            "https://www.animalpolitico.com/verificacion-reforma-judicial",
            "https://www.eluniversal.com.mx/nacion/sheinbaum-metro"
        ]
    
    try:
        import httpx
        
        # Serper API endpoint
        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": serper_api_key,
            "Content-Type": "application/json"
        }
        
        # Search query optimized for Mexican news sources
        payload = {
            "q": f"{query} site:mx OR site:com.mx",
            "num": 10,  # Get top 10 results
            "gl": "mx",  # Country: Mexico
            "hl": "es",  # Language: Spanish
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # Extract URLs from search results
            urls = []
            if "organic" in data:
                for result in data["organic"]:
                    if "link" in result:
                        urls.append(result["link"])
            
            print(f"Serper API found {len(urls)} results for: {query}")
            return urls[:10]  # Return top 10 URLs
            
    except Exception as e:
        print(f"Error using Serper API: {e}. Falling back to mock results.")
        # Fallback to mock results on error
        return [
            "https://www.animalpolitico.com/verificacion-reforma-judicial",
            "https://www.eluniversal.com.mx/nacion/sheinbaum-metro"
        ]

async def search_web_rich(query: str) -> List[Dict[str, str]]:
    """Search the web using Serper API (returns links and snippets)"""
    serper_api_key = settings.SERPER_API_KEY
    
    if not serper_api_key:
        print(f"Warning: SERPER_API_KEY not found. Using mock results for: {query}")
        return []
    
    try:
        import httpx
        
        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": serper_api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "q": f"{query} site:mx OR site:com.mx",
            "num": 10,
            "gl": "mx",
            "hl": "es",
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            results = []
            if "organic" in data:
                for result in data["organic"]:
                    if "link" in result:
                        results.append({
                            "link": result.get("link"),
                            "snippet": result.get("snippet", ""),
                            "title": result.get("title", "")
                        })
            
            print(f"Serper API (Rich) found {len(results)} results for: {query}")
            return results
            
    except Exception as e:
        print(f"Error using Serper API (Rich): {e}")
        return []

async def search_news(query: str) -> List[Dict[str, Any]]:
    """Search for news using Serper API (returns rich results)"""
    serper_api_key = settings.SERPER_API_KEY
    
    if not serper_api_key:
        print(f"Warning: SERPER_API_KEY not found. Skipping Serper news search.")
        return []
    
    try:
        import httpx
        
        # Serper API endpoint
        url = "https://google.serper.dev/news"
        headers = {
            "X-API-KEY": serper_api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "q": query,
            "num": 20,
            "gl": "mx",
            "hl": "es",
            "tbs": "qdr:d"  # Past 24 hours
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            results = []
            if "news" in data:
                for item in data["news"]:
                    results.append({
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                        "date": item.get("date", ""),
                        "source": item.get("source", "Unknown")
                    })
            
            print(f"Serper News API found {len(results)} results for: {query}")
            return results
            
    except Exception as e:
        print(f"Error using Serper News API: {e}")
        return []
