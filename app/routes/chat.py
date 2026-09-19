import json
from flask import Blueprint, request, jsonify, Response, stream_with_context

from app.models import PaperStore
from app.services.vector_store import VectorStore
from app.services.gemini_service import GeminiService
from app.services.citation_service import CitationService

chat_bp = Blueprint("chat_api", __name__, url_prefix="/api/chat")

paper_store = PaperStore()
vector_store = VectorStore()
gemini_service = GeminiService()

@chat_bp.route("/stream", methods=["POST"])
def stream_chat():
    """
    RAG Chat endpoint with Server-Sent Events (SSE) streaming.
    Grounds answers in retrieved paper chunks with page citations.
    """
    data = request.get_json() or {}
    paper_id = data.get("paper_id")
    message = data.get("message", "").strip()

    if not paper_id or not message:
        return jsonify({"success": False, "error": "paper_id and message are required"}), 400

    paper = paper_store.get_paper(paper_id)
    if not paper:
        return jsonify({"success": False, "error": "Paper not found"}), 404

    # 1. Retrieve relevant chunks via Vector Store
    context_chunks = vector_store.search(
        query=message,
        paper_id=paper_id,
        top_k=5
    )

    # 2. Extract citations summary for UI badge links
    citations = [
        {
            "page": c.get("page"),
            "section": c.get("section"),
            "similarity": c.get("similarity"),
            "snippet": c.get("text", "")[:120] + "..."
        }
        for c in context_chunks
    ]

    def generate_events():
        # Step 1: Send metadata event with citations
        yield f"event: metadata\ndata: {json.dumps({'citations': citations})}\n\n"

        # Step 2: Stream tokens from Gemini
        for token in gemini_service.stream_answer(
            query=message,
            context_chunks=context_chunks,
            paper_title=paper.title
        ):
            yield f"event: token\ndata: {json.dumps({'chunk': token})}\n\n"

        # Step 3: Send completion event
        yield f"event: done\ndata: {json.dumps({'status': 'finished'})}\n\n"

    return Response(
        stream_with_context(generate_events()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Content-Type": "text/event-stream"
        }
    )


@chat_bp.route("/bibtex/<paper_id>", methods=["GET"])
def get_bibtex(paper_id):
    """Returns formatted BibTeX citation for the paper."""
    paper = paper_store.get_paper(paper_id)
    if not paper:
        return jsonify({"success": False, "error": "Paper not found"}), 404

    bibtex = CitationService.generate_bibtex(paper)
    return jsonify({"success": True, "bibtex": bibtex})
