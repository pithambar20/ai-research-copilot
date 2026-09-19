import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from app.config import Config

class Paper:
    def __init__(
        self,
        paper_id: str,
        title: str,
        authors: List[str],
        abstract: str,
        filename: str,
        filepath: str,
        page_count: int,
        published_date: Optional[str] = None,
        arxiv_id: Optional[str] = None,
        doi: Optional[str] = None,
        sections: Optional[List[Dict[str, Any]]] = None,
        chunk_count: int = 0,
        created_at: Optional[str] = None
    ):
        self.paper_id = paper_id
        self.title = title or "Untitled Document"
        self.authors = authors or []
        self.abstract = abstract or ""
        self.filename = filename
        self.filepath = filepath
        self.page_count = page_count
        self.published_date = published_date or datetime.now().strftime("%Y-%m-%d")
        self.arxiv_id = arxiv_id
        self.doi = doi
        self.sections = sections or []
        self.chunk_count = chunk_count
        self.created_at = created_at or datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "paper_id": self.paper_id,
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "filename": self.filename,
            "filepath": str(self.filepath),
            "page_count": self.page_count,
            "published_date": self.published_date,
            "arxiv_id": self.arxiv_id,
            "doi": self.doi,
            "sections": self.sections,
            "chunk_count": self.chunk_count,
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Paper":
        return cls(
            paper_id=data.get("paper_id", str(uuid.uuid4())),
            title=data.get("title", ""),
            authors=data.get("authors", []),
            abstract=data.get("abstract", ""),
            filename=data.get("filename", ""),
            filepath=data.get("filepath", ""),
            page_count=data.get("page_count", 0),
            published_date=data.get("published_date"),
            arxiv_id=data.get("arxiv_id"),
            doi=data.get("doi"),
            sections=data.get("sections", []),
            chunk_count=data.get("chunk_count", 0),
            created_at=data.get("created_at")
        )


class PaperStore:
    """Thread-safe persistent JSON store for paper metadata"""
    def __init__(self, file_path: Path = Config.METADATA_FILE):
        self.file_path = file_path
        self._ensure_file()

    def _ensure_file(self):
        if not self.file_path.exists():
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump({}, f)

    def _read_all(self) -> Dict[str, Dict[str, Any]]:
        self._ensure_file()
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _write_all(self, data: Dict[str, Dict[str, Any]]):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def add_paper(self, paper: Paper):
        data = self._read_all()
        data[paper.paper_id] = paper.to_dict()
        self._write_all(data)

    def get_paper(self, paper_id: str) -> Optional[Paper]:
        data = self._read_all()
        item = data.get(paper_id)
        if item:
            return Paper.from_dict(item)
        return None

    def list_papers(self) -> List[Paper]:
        data = self._read_all()
        # Sort latest first
        sorted_items = sorted(
            data.values(),
            key=lambda x: x.get("created_at", ""),
            reverse=True
        )
        return [Paper.from_dict(item) for item in sorted_items]

    def delete_paper(self, paper_id: str) -> bool:
        data = self._read_all()
        if paper_id in data:
            del data[paper_id]
            self._write_all(data)
            return True
        return False
