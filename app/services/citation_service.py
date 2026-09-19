import re
from typing import Optional, List
from app.models import Paper

class CitationService:
    @staticmethod
    def generate_bibtex(paper: Paper) -> str:
        """
        Generates a standard BibTeX citation string from Paper metadata.
        """
        # Create citation key: FirstAuthorSurnameYear
        first_author = "Author"
        if paper.authors:
            # Extract last name
            parts = paper.authors[0].strip().split()
            first_author = parts[-1] if parts else "Author"
            first_author = re.sub(r"[^a-zA-Z]", "", first_author)
            
        year = "2024"
        if paper.published_date:
            year_match = re.search(r"\b(19\d\d|20\d\d)\b", paper.published_date)
            if year_match:
                year = year_match.group(1)

        cite_key = f"{first_author.lower()}{year}{paper.paper_id[:4]}"

        # Authors formatted for BibTeX: "LastName, FirstName and LastName, FirstName"
        author_str = " and ".join(paper.authors) if paper.authors else "Unknown"

        if paper.arxiv_id:
            bibtex = f"""@article{{{cite_key},
  title = {{{paper.title}}},
  author = {{{author_str}}},
  journal = {{arXiv preprint arXiv:{paper.arxiv_id}}},
  year = {{{year}}},
  eprint = {{{paper.arxiv_id}}},
  archivePrefix = {{arXiv}},
  primaryClass = {{cs.AI}}
}}"""
        else:
            bibtex = f"""@article{{{cite_key},
  title = {{{paper.title}}},
  author = {{{author_str}}},
  year = {{{year}}},
  note = {{{paper.filename}}}
}}"""
        return bibtex
