import os 
import asyncio
import logging
import httpx # type: ignore
from typing import List, Dict, Optional, Any
from core.config import settings

logger = logging.getLogger("cloudflare")

CF_API_TOKEN = settings.CF_API_TOKEN
CF_ZONE_ID = settings.CF_ZONE_ID
MAX_PURGE_BATCH = 30
MAX_RETRIES = 5
BACKOFF_BASE = float(0.5)

_client: Optional[httpx.AsyncClient] = None
_client_lock = asyncio.Lock()

async def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        async with _client_lock:
            if _client is None:
                _client = httpx.AsyncClient(timeout=10.0)
    return _client
                
async def close_client() -> None:
    global _client
    if _client is not None:
        try:
            await _client.aclose()
        except Exception as e:
            logger.warning("Error closing Cloudflare httpx client: %s", e)
        finally:
            _client = None

async def purge_cache(urls: List[str]) -> Dict[str, Any]:
    endpoint = f"https://api.cloudflare.com/client/v4/zones/{CF_ZONE_ID}/purge_cache"
    headers = {
        "Authorization": f"Bearer {CF_API_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {"files": urls}
    
    client = await _get_client()
    resp = await client.post(endpoint, json=payload, headers=headers)
    try:
        body = resp.json()
    except Exception:
        body = {"success": False, "status_code": resp.status_code, "text": resp.text}
    return {"status_code": resp.status_code, "body": body}
        
async def purge_urls(urls: List[str]) -> List[dict]:
    results: List[Dict] = []
    batches = [urls[i:i + MAX_PURGE_BATCH] for i in range(0, len(urls), MAX_PURGE_BATCH)]
    for batch in batches:
        attempt = 0
        while attempt < MAX_RETRIES:
            try:
                resp = await purge_cache(batch)
                status = resp.get("status_code")
                body = resp.get("body")
                
                if status == 200 and isinstance(body, dict) and body.get("success", False):
                    logger.info("Cloudflare purge success for %d URLs", len(batch))
                    results.append({"batch": batch, "success": True, "response": body})
                    break
                if status in (429, 500, 502, 503, 504) or not (isinstance(body, dict) and body.get("success", False)):
                    wait = BACKOFF_BASE * (2 ** attempt)
                    logger.warning("Cloudflare purge attempt %d failed (status=%s), retrying in %.1fs: %s", attempt + 1, status, wait, body)
                    await asyncio.sleep(wait)
                    attempt += 1
                    continue
                logger.error("Cloudflare purge failed (status=%s): %s", status, body)
                results.append({"batch": batch, "success": False, "response": body})
                break
            except httpx.RequestError as e:
                wait = BACKOFF_BASE * (2 ** attempt)
                logger.warning("Cloudflare purge attempt %d failed with exception, retrying in %.1fs: %s", attempt + 1, wait, e)
                await asyncio.sleep(wait)
                attempt += 1
        else:
            logger.error("Cloudflare purge failed after %d attempts for batch of %d URLs", MAX_RETRIES, len(batch))
            results.append({"batch": batch, "success": False, "response": "max retries exceeded"})
    return results