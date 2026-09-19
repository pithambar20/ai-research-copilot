import re
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests

ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}

class ArxivClient:
    BASE_API_URL = "http://export.arxiv.org/api/query"

    @staticmethod
    def search(query: str, max_results: int = 6) -> List[Dict[str, Any]]:
        """
        Queries arXiv API by keyword, author, or title and returns structured results.
        """
        clean_query = query.strip()
        if not clean_query:
            return []

        # Check if query is directly an arXiv ID (e.g., 2312.00752 or 2312.00752v1)
        arxiv_id_match = re.search(r"(\d{4}\.\d{4,5}(?:v\d+)?)", clean_query)
        if arxiv_id_match:
            params = {
                "id_list": arxiv_id_match.group(1),
                "max_results": 1
            }
        else:
            params = {
                "search_query": f"all:{clean_query}",
                "start": 0,
                "max_results": max_results,
                "sortBy": "relevance",
                "sortOrder": "descending"
            }

        url = f"{ArxivClient.BASE_API_URL}?{urllib.parse.urlencode(params)}"
        response = requests.get(url, timeout=15)
        response.raise_for_status()

        return ArxivClient._parse_atom_response(response.text)

    @staticmethod
    def _parse_atom_response(xml_data: str) -> List[Dict[str, Any]]:
        root = ET.fromstring(xml_data)
        papers = []

        for entry in root.findall("atom:entry", ATOM_NS):
            id_text = entry.findtext("atom:id", default="", namespaces=ATOM_NS).strip()
            # Extract raw arXiv ID
            match = re.search(r"abs/([0-9]+\.[0-9]+(?:v[0-9]+)?)", id_text)
            arxiv_id = match.group(1) if match else id_text.split("/")[-1]

            title = entry.findtext("atom:title", default="", namespaces=ATOM_NS)
            title = " ".join(title.split())  # Clean multiline titles

            summary = entry.findtext("atom:summary", default="", namespaces=ATOM_NS)
            summary = " ".join(summary.split())

            published = entry.findtext("atom:published", default="", namespaces=ATOM_NS)
            published_date = published[:10] if published else ""

            authors = [
                author.findtext("atom:name", default="", namespaces=ATOM_NS).strip()
                for author in entry.findall("atom:author", ATOM_NS)
            ]

            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

            papers.append({
                "arxiv_id": arxiv_id,
                "title": title,
                "authors": authors,
                "abstract": summary,
                "published_date": published_date,
                "pdf_url": pdf_url
            })

        return papers

    @staticmethod
    def download_pdf(arxiv_id: str, dest_folder: Path) -> Path:
        """
        Downloads the PDF from arXiv and stores it in dest_folder.
        """
        # Clean version if present (e.g. 2312.00752v1 -> 2312.00752)
        clean_id = re.sub(r"v\d+$", "", arxiv_id.strip())
        pdf_url = f"https://arxiv.org/pdf/{clean_id}.pdf"
        dest_folder.mkdir(parents=True, exist_ok=True)
        target_path = dest_folder / f"{clean_id}.pdf"

        headers = {
            "User-Agent": "AI-Research-Copilot/1.0 (academic research assistant; mailto:admin@example.com)"
        }
        
        response = requests.get(pdf_url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()

        with open(target_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        return target_path
