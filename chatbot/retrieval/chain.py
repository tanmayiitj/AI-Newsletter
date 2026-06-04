"""LangChain retrieval chain for newsletter question answering."""

import logging

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document

from chatbot.config.settings import settings
from chatbot.retrieval.vector_store import get_vector_retriever

logger = logging.getLogger(__name__)

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
You answer questions based on the provided newsletter articles.

Rules:
- Reference the edition number and source for each piece of information (e.g., "According to TechCrunch in Edition #12...").
- Be concise and factual. Use numbered lists when listing multiple items.
- If the articles don't fully cover the topic, share any related information you find and briefly note what you couldn't find.
- If asked about jobs, include role titles, companies, and experience levels from the context.
- If the question is clearly unrelated to AI, technology, or newsletters (e.g., recipes, weather, sports), politely decline and suggest asking about AI topics instead.
- If a question mixes AI topics with unrelated topics, answer ONLY the AI-relevant part and state the other part is outside your scope.
- Do not make up information that is not in the provided context.

Chat history:
{chat_history}

Context from newsletters:
{context}

Question: {question}"""


def _format_docs(docs: list[Document]) -> str:
    """Format retrieved documents into a context string.

    Headers are already baked into page_content, so just join them.
    """
    return "\n\n---\n\n".join(doc.page_content for doc in docs)


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
) -> dict:
    """Ask a question against the newsletter vector store.

    Uses MMR retrieval for diverse, relevant results.

    Args:
        question: The user's question.
        chat_history: List of (human, ai) tuples for conversation context.

    Returns:
        Dict with 'answer' (str) and 'source_documents' (list[Document]).
    """
    llm = _get_llm()

    retriever = get_vector_retriever()
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
