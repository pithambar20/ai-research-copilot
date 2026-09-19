import os
from typing import List, Dict, Any, Generator, Optional
from app.config import Config

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

SYSTEM_PROMPT = """You are AI Research Copilot, an elite academic research assistant and literature analyst.
Your mission is to help researchers thoroughly understand, critique, and synthesize academic papers.

CRITICAL GROUNDING & CITATION RULES:
1. Ground your answers strictly in the provided Context Chunks from the paper.
2. ALWAYS cite the specific page number when making claims, e.g., `[Page 3]` or `[Methodology, Page 5]`.
3. If the paper contains mathematical definitions, formulas, or theorems, express them in LaTeX notation using `$...$` for inline math and `$$...$$` for block equations.
4. Structure your response with clear headings, bullet points, and bold keywords for readability.
5. If the provided context does not contain enough information to answer the question, state that clearly rather than hallucinating.
"""

class GeminiService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or Config.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        self.model_name = "gemini-2.5-flash"
        self.client = None

        if self.api_key and GENAI_AVAILABLE:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"Error initializing Gemini client: {e}")

    def is_configured(self) -> bool:
        return bool(self.client and self.api_key)

    def _build_prompt_with_context(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        paper_title: str
    ) -> str:
        formatted_chunks = []
        for idx, chunk in enumerate(context_chunks):
            p = chunk.get("page", "?")
            sec = chunk.get("section", "General")
            text = chunk.get("text", "").strip()
            formatted_chunks.append(f"--- Context Passage {idx+1} [Section: {sec} | Page: {p}] ---\n{text}")

        context_str = "\n\n".join(formatted_chunks) if formatted_chunks else "No specific passages found."

        return f"""Paper Title: {paper_title}

RELEVANT EXCERPTS FROM THE PAPER:
{context_str}

USER RESEARCH QUESTION:
{query}

Please provide a rigorous, grounded academic answer with explicit page citations [Page X]:"""

    def stream_answer(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        paper_title: str = "Research Paper",
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Generator[str, None, None]:
        """
        Streams response chunks from Gemini 2.5 Flash using Server-Sent Events.
        """
        if not self.is_configured():
            # Graceful educational fallback if user has not entered API key yet
            yield "### 🔑 Gemini API Key Needed\n\n"
            yield "To activate live AI responses with **Gemini 2.5 Flash**, please add your `GEMINI_API_KEY` to your `.env` file.\n\n"
            yield f"**Retrieved Context Passages for '{query}':**\n\n"
            for c in context_chunks[:3]:
                yield f"- **[Page {c.get('page')}] ({c.get('section')}):** {c.get('text')[:200]}...\n\n"
            return

        prompt = self._build_prompt_with_context(query, context_chunks, paper_title)

        try:
            config = types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.2,
                top_p=0.95
            )

            # Stream using official google-genai SDK
            response = self.client.models.generate_content_stream(
                model=self.model_name,
                contents=prompt,
                config=config
            )

            for chunk in response:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            yield f"\n\n**AI Service Error:** {str(e)}"

    def generate_summary(
        self,
        paper_title: str,
        context_chunks: List[Dict[str, Any]]
    ) -> str:
        """
        Generates a structured comprehensive summary of the paper.
        """
        query = (
            "Provide a comprehensive structured academic summary of this paper including: "
            "1. Core Research Problem & Motivation, "
            "2. Key Contributions & Novelty, "
            "3. Methodology & System Architecture, "
            "4. Main Experimental Results & Metrics, "
            "5. Limitations & Future Directions. "
            "Cite page numbers throughout."
        )
        generator = self.stream_answer(query, context_chunks, paper_title)
        return "".join(list(generator))
