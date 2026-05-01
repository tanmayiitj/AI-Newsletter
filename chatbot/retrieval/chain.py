"""LangChain retrieval chain for newsletter question answering."""

import logging

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.documents import Document

from chatbot.config.settings import settings
from chatbot.retrieval.vector_store import get_hybrid_retriever, get_vector_retriever

logger = logging.getLogger(__name__)

# Cached LLM instance (reused across calls — only the retriever filter changes)
_llm: ChatOpenAI | None = None


def _get_llm() -> ChatOpenAI:
    """Return a cached LLM instance."""
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            temperature=0.3,
            max_tokens=1024,
        )
    return _llm


SYSTEM_PROMPT = """You are "AI Pulse Assistant", a helpful chatbot for the AI Pulse Newsletter.
You answer questions ONLY based on the provided newsletter content.
If the information is not in the provided context, say: "I don't have that information in our newsletters."

Rules:
- Always cite the edition number (e.g. "Edition #3") when referencing information.
- Cite the article title and source name when referencing specific information (e.g. "according to TechCrunch").
- Be concise and factual.
- If asked about jobs, include role titles, companies, and experience tiers from the context.
- Do not make up information that is not in the provided context.
- When listing multiple items, use numbered lists for clarity.
- If multiple articles from different editions are relevant, reference each.

Chat history:
{chat_history}

Context from newsletters:
{context}

Question: {question}"""


def _format_docs(docs: list[Document]) -> str:
    """Format retrieved documents into a single context string with source info."""
    parts = []
    for doc in docs:
        meta = doc.metadata
        header = (
            f"[Edition #{meta.get('edition_number', '?')} | "
            f"{meta.get('section_title', '')} | "
            f"{meta.get('article_title', '')} | "
            f"Source: {meta.get('source_name', 'unknown')}]"
        )
        parts.append(f"{header}\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


def _format_chat_history(history: list[tuple[str, str]]) -> str:
    """Format chat history tuples into a readable string."""
    if not history:
        return "No previous conversation."
    parts = []
    for human, ai in history:
        parts.append(f"Human: {human}\nAssistant: {ai}")
    return "\n".join(parts)


async def ask_question(
    question: str,
    chat_history: list[tuple[str, str]],
    filter_metadata: dict | None = None,
) -> dict:
    """Ask a question against the newsletter vector store.

    Uses hybrid search (vector + full-text) with fallback to pure vector search.

    Args:
        question: The user's question.
        chat_history: List of (human, ai) tuples for conversation context.
        filter_metadata: Optional MongoDB pre_filter for temporal queries.

    Returns:
        Dict with 'answer' (str) and 'source_documents' (list[Document]).
    """
    llm = _get_llm()

    # Try hybrid retrieval first, fall back to pure vector if full-text index missing
    try:
        retriever = get_hybrid_retriever(filter_metadata=filter_metadata, k=5)
        docs = await retriever.ainvoke(question)
    except Exception as e:
        logger.warning("Hybrid retrieval failed (%s), falling back to vector search", e)
        retriever = get_vector_retriever(filter_metadata=filter_metadata, k=5)
        docs = await retriever.ainvoke(question)

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
    ])

    chain = prompt | llm | StrOutputParser()

    answer = await chain.ainvoke({
        "context": _format_docs(docs),
        "chat_history": _format_chat_history(chat_history),
        "question": question,
    })

    return {
        "answer": answer,
        "source_documents": docs,
    }
