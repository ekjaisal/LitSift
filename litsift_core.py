import asyncio
import aiohttp
import csv
from typing import List, Dict, Any, Callable

BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
FIELDS = ["paperId", "title", "authors", "year", "citationCount", "influentialCitationCount", "tldr", "abstract", "publicationTypes", "externalIds", "openAccessPdf", "url", "citationStyles"]
CSV_COLUMNS = ["Title", "Authors", "Year", "Citations", "Influential Citations", "S2 TLDR", "Abstract", "Publication Type", "DOI", "PDF URL", "S2 URL"]

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
            async with session.get(BASE_URL, params=params) as response:
                if response.status == 429:
                    retry_after = int(response.headers.get("Retry-After", 15))
                    await asyncio.sleep(retry_after)
                    continue
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError:
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
            except aiohttp.ClientResponseError as e:
                if e.status == 429:
                    retry_after = int(e.headers.get("Retry-After", 15))
                    if progress_callback:
                        progress_callback(int((len(all_papers) / max_results) * 100), f"Rate limit hit, waiting {retry_after} seconds...")
                    await asyncio.sleep(retry_after)
                else:
                    raise

    return all_papers[:max_results]

def save_to_file(papers: List[Dict[str, str]], filename: str, file_format: str):
    if file_format == 'csv':
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=CSV_COLUMNS, extrasaction='ignore', quoting=csv.QUOTE_ALL)
            writer.writeheader()
            seen = set()
            for paper in papers:
                row = tuple(paper.get(col, "") for col in CSV_COLUMNS)
                if row not in seen and any(row):
                    seen.add(row)
                    writer.writerow({k: paper.get(k, "") for k in CSV_COLUMNS})
    elif file_format == 'bib':
        with open(filename, 'w', encoding='utf-8') as bibfile:
            for paper in papers:
                bibtex = paper.get("BibTeX", "")
                if bibtex:
                    bibfile.write(bibtex + "\n\n")