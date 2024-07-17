import asyncio
import aiohttp
import csv
import time
import socket
import random
import urllib.request
from typing import List, Dict, Any, Callable

BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
FIELDS = ["paperId", "title", "authors", "year", "citationCount", "influentialCitationCount", "tldr", "abstract", "venue", "publicationTypes", "externalIds", "openAccessPdf", "url", "citationStyles"]
CSV_COLUMNS = ["Title", "Authors", "Year", "Citations", "Influential Citations", "S2 TLDR", "Abstract", "Publication", "Publication Type", "DOI", "PDF URL", "S2 URL"]

class TokenBucket:
    def __init__(self, tokens, fill_rate):
        self.capacity = tokens
        self.tokens = tokens
        self.fill_rate = fill_rate
        self.timestamp = time.time()

    async def consume(self):
        now = time.time()
        tokens_to_add = (now - self.timestamp) * self.fill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.timestamp = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False

    async def wait_for_token(self):
        while not await self.consume():
            await asyncio.sleep(0.1)

token_bucket = TokenBucket(1, 1)

def get_value(obj: Any, key: str, default: Any = None) -> Any:
    if obj is None:
        return default
    return obj.get(key, default) if isinstance(obj, dict) else getattr(obj, key, default)

def join_values(items: Any, separator: str = ", ") -> str:
    if items is None:
        return ""
    return separator.join(str(item) for item in items if item is not None)

def to_str(value: Any) -> str:
    return str(value) if value is not None else ""

def format_paper(paper: Dict[str, Any]) -> Dict[str, str]:
    return {
        "S2 ID": get_value(paper, "paperId", ""),
        "Title": get_value(paper, "title", ""),
        "Authors": join_values([get_value(author, "name") for author in get_value(paper, "authors", [])]),
        "Year": to_str(get_value(paper, "year")),
        "Citations": to_str(get_value(paper, "citationCount")),
        "Influential Citations": to_str(get_value(paper, "influentialCitationCount")),
        "S2 TLDR": get_value(get_value(paper, "tldr"), "text", ""),
        "Abstract": get_value(paper, "abstract", "") or "",
        "Publication": get_value(paper, "venue", ""),
        "Publication Type": join_values(get_value(paper, "publicationTypes", [])),
        "DOI": get_value(get_value(paper, "externalIds"), "DOI", ""),
        "PDF URL": get_value(get_value(paper, "openAccessPdf"), "url", ""),
        "S2 URL": get_value(paper, "url", ""),
        "BibTeX": get_value(get_value(paper, "citationStyles"), "bibtex", "")
    }

async def fetch_papers(session: aiohttp.ClientSession, query: str, offset: int, limit: int) -> Dict[str, Any]:
    params = {"query": query, "offset": offset, "limit": limit, "fields": ",".join(FIELDS)}
    for attempt in range(5):
        try:
            await token_bucket.wait_for_token()
            async with session.get(BASE_URL, params=params) as response:
                if response.status == 429:
                    retry_after = int(response.headers.get("Retry-After", 15))
                    await asyncio.sleep(retry_after)
                    continue
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            if attempt == 4:
                raise
            await asyncio.sleep(2**attempt)
    raise Exception("Failed to fetch results after multiple attempts")

async def search_semantic_scholar(query: str, max_results: int = 1000, progress_callback: Callable[[int, str], None] = None):
    all_papers = []
    async with aiohttp.ClientSession() as session:
        offset = 0
        while len(all_papers) < max_results:
            try:
                if progress_callback:
                    progress_callback(int((len(all_papers) / max_results) * 100), f"Fetching results (offset: {offset})...")
                
                data = await fetch_papers(session, query, offset, min(100, max_results - len(all_papers)))
                papers = data.get("data", [])
                
                if not papers:
                    break
                
                all_papers.extend(format_paper(paper) for paper in papers)
                offset += len(papers)
                
                if progress_callback:
                    progress_callback(int((len(all_papers) / max_results) * 100), f"Processed {len(all_papers)} results...")
                
                if "next" not in data:
                    break
                
                offset = int(data["next"])
            except aiohttp.ClientResponseError as e:
                if e.status == 429:
                    retry_after = int(e.headers.get("Retry-After", 15))
                    if progress_callback:
                        progress_callback(int((len(all_papers) / max_results) * 100), f"Rate limit hit, waiting {retry_after} seconds...")
                    await asyncio.sleep(retry_after)
                elif e.status == 400:
                    raise ValueError("Invalid query or parameters")
                elif e.status == 401:
                    raise ValueError("Unauthorized access.")
                elif e.status == 403:
                    raise ValueError("Access forbidden. Check your permissions")
                elif e.status == 404:
                    raise ValueError("Resource not found")
                elif e.status == 500:
                    raise ValueError("Internal server error. Try again later")
                else:
                    raise ValueError(f"Unexpected error: {e.status}")

    return all_papers[:max_results]

def save_to_file(papers: List[Dict[str, str]], filename: str, file_format: str):
    if file_format == 'csv':
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=CSV_COLUMNS, extrasaction='ignore', quoting=csv.QUOTE_ALL)
            writer.writeheader()
            seen = set()
            for paper in papers:
                paper_tuple = tuple(paper.get(col, "") for col in CSV_COLUMNS)
                if paper_tuple not in seen:
                    seen.add(paper_tuple)
                    writer.writerow({k: paper.get(k, "") for k in CSV_COLUMNS})
    elif file_format == 'bib':
        with open(filename, 'w', encoding='utf-8') as bibfile:
            seen = set()
            for paper in papers:
                bibtex = paper.get("BibTeX", "")
                if bibtex and bibtex not in seen:
                    seen.add(bibtex)
                    bibfile.write(bibtex + "\n\n")

def check_internet_connection():    
    http_urls = [
        "http://www.google.com",
        "http://www.bing.com",
        "http://www.amazon.com",
        "http://www.wikipedia.org",
    ]
    
    dns_servers = [
        ("1.1.1.1", 53),
        ("8.8.8.8", 53),
        ("208.67.222.222", 53),
        ("9.9.9.9", 53),
    ]
    
    for url in random.sample(http_urls, len(http_urls)):
        try:
            urllib.request.urlopen(url, timeout=5)
            return True
        except urllib.error.URLError:
            continue
    
    for server in random.sample(dns_servers, len(dns_servers)):
        try:
            socket.create_connection(server, timeout=5)
            return True
        except OSError:
            continue
    
    return False