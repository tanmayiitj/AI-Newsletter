"""LangChain RetrievalQA chain for newsletter question answering."""

import logging

from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

from chatbot.config.settings import settings
from chatbot.retrieval.vector_store import get_retriever

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are "AI Pulse Assistant", a helpful chatbot for the AI Pulse Newsletter.
You answer questions ONLY based on the provided newsletter content.
If the information is not in the provided context, say: "I don't have that information in our newsletters."

Rules:
- Always cite the edition number (e.g. "Edition #3") when referencing information.
- Be concise and factual.
- If asked about jobs, include role titles, companies, and experience tiers from the context.
- Do not make up information that is not in the provided context.
- When listing multiple items, use numbered lists for clarity."""

HUMAN_PROMPT = """Context from newsletters:
{context}

Question: {question}"""


def build_chain(
    filter_metadata: dict | None = None,
    chat_history: list | None = None,
) -> ConversationalRetrievalChain:
    """Build a conversational retrieval chain with optional metadata filtering.

    Args:
        filter_metadata: ChromaDB where-clause for temporal/section filtering.
        chat_history: Not used here directly but the chain supports it.
    """
    llm = ChatOpenAI(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        temperature=0.3,
        max_tokens=1024,
    )

    retriever = get_retriever(filter_metadata=filter_metadata, k=5)

    combine_docs_prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(SYSTEM_PROMPT),
        HumanMessagePromptTemplate.from_template(HUMAN_PROMPT),
    ])

    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        combine_docs_chain_kwargs={"prompt": combine_docs_prompt},
        return_source_documents=True,
        verbose=False,
    )

    return chain


async def ask_question(
    question: str,
    chat_history: list[tuple[str, str]],
    filter_metadata: dict | None = None,
) -> dict:
    """Ask a question against the newsletter vector store.

    Args:
        question: The user's question.
        chat_history: List of (human, ai) tuples for conversation context.
        filter_metadata: Optional ChromaDB filter for temporal queries.

    Returns:
        Dict with 'answer' (str) and 'source_documents' (list[Document]).
    """
    chain = build_chain(filter_metadata=filter_metadata)

    result = await chain.ainvoke({
        "question": question,
        "chat_history": chat_history,
    })

    return {
        "answer": result["answer"],
        "source_documents": result.get("source_documents", []),
    }
