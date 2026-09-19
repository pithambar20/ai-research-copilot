import uuid
from pathlib import Path
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename

from app.config import Config
from app.models import Paper, PaperStore
from app.services.pdf_parser import PDFParser
from app.services.arxiv_client import ArxivClient
from app.services.vector_store import VectorStore

papers_bp = Blueprint("papers_api", __name__, url_prefix="/api/papers")

paper_store = PaperStore()
vector_store = VectorStore()

@papers_bp.route("", methods=["GET"])
def list_papers():
    """List all papers in the library."""
    papers = paper_store.list_papers()
    return jsonify({
        "success": True,
        "count": len(papers),
        "papers": [p.to_dict() for p in papers]
    })


@papers_bp.route("/<paper_id>", methods=["GET"])
def get_paper(paper_id):
    """Retrieve detailed metadata of a specific paper."""
    paper = paper_store.get_paper(paper_id)
    if not paper:
        return jsonify({"success": False, "error": "Paper not found"}), 404
    return jsonify({"success": True, "paper": paper.to_dict()})


@papers_bp.route("/<paper_id>/pdf", methods=["GET"])
def get_paper_pdf(paper_id):
    """Serve the raw PDF file for in-browser viewing."""
    paper = paper_store.get_paper(paper_id)
    if not paper or not Path(paper.filepath).exists():
        return jsonify({"success": False, "error": "PDF file not found"}), 404
    return send_file(paper.filepath, mimetype="application/pdf")


@papers_bp.route("/upload", methods=["POST"])
def upload_paper():
    """Upload a local PDF file, parse sections, and index chunks into vector store."""
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"}), 400

    file = request.files["file"]
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        return jsonify({"success": False, "error": "Only PDF files are supported"}), 400

    paper_id = str(uuid.uuid4())
    safe_filename = f"{paper_id}_{secure_filename(file.filename)}"
    dest_path = Config.UPLOAD_FOLDER / safe_filename

    file.save(str(dest_path))

    try:
        # 1. Parse text and detect sections
        parsed = PDFParser.parse_pdf(dest_path)

        # 2. Create Paper Record
        paper = Paper(
            paper_id=paper_id,
            title=parsed.get("title", file.filename.replace(".pdf", "")),
            authors=parsed.get("authors", []),
            abstract=parsed.get("abstract", ""),
            filename=file.filename,
            filepath=str(dest_path),
            page_count=parsed.get("page_count", 1),
            sections=parsed.get("sections", []),
            chunk_count=len(parsed.get("chunks", []))
        )
        paper_store.add_paper(paper)

        # 3. Index chunks into Vector Store
        vector_store.index_paper_chunks(
            paper_id=paper.paper_id,
            paper_title=paper.title,
            chunks=parsed.get("chunks", [])
        )

        return jsonify({
            "success": True,
            "message": "Paper uploaded and indexed successfully",
            "paper": paper.to_dict()
        }), 201

    except Exception as e:
        if dest_path.exists():
            dest_path.unlink()
        return jsonify({"success": False, "error": str(e)}), 500


@papers_bp.route("/arxiv/search", methods=["GET"])
def search_arxiv():
    """Search papers on arXiv by query or ID."""
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"success": False, "error": "Query parameter 'q' is required"}), 400

    try:
        results = ArxivClient.search(query, max_results=6)
        return jsonify({"success": True, "count": len(results), "results": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@papers_bp.route("/arxiv/ingest", methods=["POST"])
def ingest_arxiv():
    """Download and index a paper from arXiv by its arXiv ID."""
    data = request.get_json() or {}
    arxiv_id = data.get("arxiv_id", "").strip()
    if not arxiv_id:
        return jsonify({"success": False, "error": "arxiv_id is required"}), 400

    try:
        # 1. Fetch metadata
        meta_results = ArxivClient.search(arxiv_id, max_results=1)
        meta = meta_results[0] if meta_results else {}

        # 2. Download PDF
        downloaded_path = ArxivClient.download_pdf(arxiv_id, Config.UPLOAD_FOLDER)

        # 3. Parse PDF
        parsed = PDFParser.parse_pdf(downloaded_path)

        paper_id = str(uuid.uuid4())
        paper = Paper(
            paper_id=paper_id,
            title=meta.get("title") or parsed.get("title") or f"arXiv:{arxiv_id}",
            authors=meta.get("authors") or parsed.get("authors") or [],
            abstract=meta.get("abstract") or parsed.get("abstract") or "",
            filename=downloaded_path.name,
            filepath=str(downloaded_path),
            page_count=parsed.get("page_count", 1),
            published_date=meta.get("published_date"),
            arxiv_id=arxiv_id,
            sections=parsed.get("sections", []),
            chunk_count=len(parsed.get("chunks", []))
        )
        paper_store.add_paper(paper)

        # 4. Index into Vector Store
        vector_store.index_paper_chunks(
            paper_id=paper.paper_id,
            paper_title=paper.title,
            chunks=parsed.get("chunks", [])
        )

        return jsonify({
            "success": True,
            "message": f"arXiv paper {arxiv_id} ingested successfully",
            "paper": paper.to_dict()
        }), 201

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@papers_bp.route("/<paper_id>", methods=["DELETE"])
def delete_paper(paper_id):
    """Delete paper metadata, stored PDF, and vector index."""
    paper = paper_store.get_paper(paper_id)
    if not paper:
        return jsonify({"success": False, "error": "Paper not found"}), 404

    # 1. Delete vector embeddings
    vector_store.delete_paper(paper_id)

    # 2. Delete PDF file
    if Path(paper.filepath).exists():
        try:
            Path(paper.filepath).unlink()
        except Exception:
            pass

    # 3. Remove metadata
    paper_store.delete_paper(paper_id)

    return jsonify({"success": True, "message": "Paper deleted successfully"})
