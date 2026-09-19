import re
from pathlib import Path
from typing import Dict, List, Any, Tuple
import fitz  # PyMuPDF

# Common academic section header patterns
SECTION_PATTERNS = [
    r"^(?:(?:\d+\.?\s*)?(?:Abstract|ABSTRACT))",
    r"^(?:(?:\d+\.?\s*)?(?:Introduction|INTRODUCTION))",
    r"^(?:(?:\d+\.?\s*)?(?:Related Work|RELATED WORK|Background|BACKGROUND))",
    r"^(?:(?:\d+\.?\s*)?(?:Methodology|METHODOLOGY|Methods|METHODS|Proposed Method|Approach|APPROACH|Architecture))",
    r"^(?:(?:\d+\.?\s*)?(?:Experiments|EXPERIMENTS|Experimental Setup|Evaluation|EVALUATION))",
    r"^(?:(?:\d+\.?\s*)?(?:Results|RESULTS|Discussion|DISCUSSION|Results and Discussion))",
    r"^(?:(?:\d+\.?\s*)?(?:Conclusion|CONCLUSION|Conclusions|Conclusions and Future Work))",
    r"^(?:(?:\d+\.?\s*)?(?:References|REFERENCES|Bibliography))",
]

class PDFParser:
    @staticmethod
    def parse_pdf(file_path: Path) -> Dict[str, Any]:
        """
        Extracts full text, pages, detected sections, and smart chunks from a PDF.
        """
        doc = fitz.open(str(file_path))
        page_count = len(doc)
        
        pages_data = []
        raw_text_by_page = []
        
        # 1. Extract text and blocks per page
        for page_num in range(page_count):
            page = doc[page_num]
            text = page.get_text("text")
            raw_text_by_page.append(text)
            pages_data.append({
                "page": page_num + 1,
                "text": text
            })
            
        # 2. Extract Document Metadata & Title
        meta = doc.metadata or {}
        title = meta.get("title", "").strip()
        authors_meta = meta.get("author", "").strip()
        authors = [a.strip() for a in re.split(r"[,;]|\band\b", authors_meta) if a.strip()] if authors_meta else []
        
        # Fallback Title from Page 1 font analysis if metadata title is empty or generic
        if not title or title.lower().endswith(".pdf") or len(title) < 5:
            title = PDFParser._extract_title_from_page(doc[0])
            
        # 3. Detect Sections and Chunks
        sections, chunks = PDFParser._extract_sections_and_chunks(pages_data)
        
        # 4. Extract Abstract
        abstract = PDFParser._extract_abstract(pages_data)
        
        doc.close()
        
        return {
            "title": title,
            "authors": authors,
            "abstract": abstract,
            "page_count": page_count,
            "sections": sections,
            "chunks": chunks
        }

    @staticmethod
    def _extract_title_from_page(first_page) -> str:
        """Finds the largest text block on page 1, which is usually the paper title."""
        try:
            blocks = first_page.get_text("dict").get("blocks", [])
            spans_with_sizes = []
            for b in blocks:
                if "lines" in b:
                    for line in b["lines"]:
                        for span in line["spans"]:
                            text = span.get("text", "").strip()
                            size = span.get("size", 0)
                            if len(text) > 3:
                                spans_with_sizes.append((size, text))
                                
            if spans_with_sizes:
                # Sort by font size descending
                spans_with_sizes.sort(key=lambda x: x[0], reverse=True)
                max_size = spans_with_sizes[0][0]
                # Join parts with similar max font size
                title_parts = [t for s, t in spans_with_sizes if s >= max_size - 1.0]
                title = " ".join(title_parts[:3]).strip()
                if 5 < len(title) < 250:
                    return title
        except Exception:
            pass
        return "Untitled Document"

    @staticmethod
    def _extract_abstract(pages_data: List[Dict[str, Any]]) -> str:
        """Extracts text within the abstract block on initial pages."""
        combined_text = "\n".join([p["text"] for p in pages_data[:2]])
        abstract_match = re.search(
            r"(?:Abstract|ABSTRACT)[\s:.\-—\n]+(.*?)(?=\n\s*(?:1[\.\s]|I[\.\s]|Introduction|INTRODUCTION|1\. Introduction))",
            combined_text,
            re.DOTALL | re.IGNORECASE
        )
        if abstract_match:
            abstract = abstract_match.group(1).strip()
            # Clean excessive newlines/spaces
            return re.sub(r"\s+", " ", abstract)[:1500]
        return ""

    @staticmethod
    def _detect_section_header(line: str) -> str:
        """Returns normalized section name if line matches a recognized academic header."""
        clean_line = line.strip()
        if len(clean_line) > 50 or len(clean_line) < 3:
            return ""
        for pattern in SECTION_PATTERNS:
            if re.match(pattern, clean_line, re.IGNORECASE):
                # Clean numbered prefixes
                return re.sub(r"^[\d\.\sIVXLCDM]+\s*", "", clean_line).title()
        return ""

    @staticmethod
    def _extract_sections_and_chunks(
        pages_data: List[Dict[str, Any]],
        chunk_size: int = 750,
        chunk_overlap: int = 150
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Segments text into sections and recursively chunks paragraphs with page tracking.
        """
        sections = []
        chunks = []
        current_section = "General"
        section_start_page = 1
        chunk_index = 0
        
        for p_idx, page in enumerate(pages_data):
            page_num = page["page"]
            lines = page["text"].split("\n")
            
            page_buffer = []
            for line in lines:
                detected = PDFParser._detect_section_header(line)
                if detected and detected != current_section:
                    # Save previous section if exists
                    if current_section not in [s["name"] for s in sections]:
                        sections.append({
                            "name": current_section,
                            "start_page": section_start_page
                        })
                    current_section = detected
                    section_start_page = page_num
                else:
                    page_buffer.append(line)
            
            # Combine page text and chunk it
            page_text = " ".join(" ".join(page_buffer).split())
            if not page_text:
                continue
                
            start = 0
            while start < len(page_text):
                end = min(start + chunk_size, len(page_text))
                # Break at end of sentence or word if possible
                if end < len(page_text):
                    last_period = page_text.rfind(". ", start, end)
                    if last_period != -1 and last_period > start + (chunk_size // 2):
                        end = last_period + 1
                    else:
                        last_space = page_text.rfind(" ", start, end)
                        if last_space != -1 and last_space > start + (chunk_size // 2):
                            end = last_space
                            
                chunk_text = page_text[start:end].strip()
                if len(chunk_text) > 40:
                    chunks.append({
                        "chunk_id": f"c_{chunk_index}",
                        "page": page_num,
                        "section": current_section,
                        "text": chunk_text
                    })
                    chunk_index += 1
                    
                start = end - chunk_overlap if end < len(page_text) else len(page_text)

        if current_section not in [s["name"] for s in sections]:
            sections.append({
                "name": current_section,
                "start_page": section_start_page
            })
            
        return sections, chunks
