from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from core.config import settings
from core.vector_db import get_vector_store
import logging

logger = logging.getLogger(__name__)

async def get_chat_response_stream(user_input: str, user_id: str, history: list[tuple[str, str]] | None = None):
    logger.info(
        "rag_chat_stream_start",
        extra={"event": "rag_chat_stream_start", "query_len": len(user_input), "history_len": len(history or [])},
    )

    vector_store = get_vector_store()
    retriever = vector_store.as_retriever(search_kwargs={"filter": {"user_id": user_id}, "k": 3})

    llm = ChatOpenAI(
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL,
        model="deepseek-chat",
        temperature=0.1,
        streaming=True,
    )

    history_text = "\n".join([f"{r}: {c}" for r, c in (history or [])])

    rewrite_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "请将用户问题改写为独立完整的问题，使其在没有会话历史的情况下也能理解。保留关键上下文信息。"),
            ("human", "会话历史：\n{history}\n\n当前问题：\n{question}"),
        ]
    )

    try:
        rewrite_messages = rewrite_prompt.format_messages(history=history_text, question=user_input)
        rewrite_res = await llm.ainvoke(rewrite_messages)
        q = (rewrite_res.content or "").strip() or user_input
    except Exception:
        q = user_input

    docs = await retriever.ainvoke(q)
    sources = list({d.metadata.get("source", "Unknown") for d in docs})
    context_text = "\n\n".join([d.page_content for d in docs])

    system_prompt = (
        "你是一个专业的智能知识库助手。"
        "请根据以下提取到的上下文信息来回答用户的问题。"
        "如果你在上下文中找不到答案，请直截了当地告诉用户你不知道，不要试图编造答案。"
        "回答请保持专业、简洁。\n\n"
        "会话历史（供参考）：\n"
        "{history}\n\n"
        "上下文信息：\n"
        "{context}"
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{input}"),
        ]
    )

    answer_messages = prompt.format_messages(history=history_text, context=context_text, input=q)

    async def token_iter():
        async for chunk in llm.astream(answer_messages):
            token = getattr(chunk, "content", None)
            if token:
                yield token

    return sources, token_iter()

async def get_chat_response(user_input: str, user_id: str, history: list[tuple[str, str]] | None = None):
    """
    执行 RAG 检索并返回 AI 回答 (增加错误诊断)
    """
    try:
        logger.info("rag_chat_start", extra={"event": "rag_chat_start", "query_len": len(user_input), "history_len": len(history or [])})
        
        # 1. 获取向量库
        vector_store = get_vector_store()
        
        # 2. 创建带过滤器的检索器
        # 即使没找到文档，检索器也不会报错，只会返回空列表
        retriever = vector_store.as_retriever(
            search_kwargs={"filter": {"user_id": user_id}, "k": 3}
        )
        
        # 3. 初始化 LLM
        llm = ChatOpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
            model="deepseek-chat",
            temperature=0.1 # 降低随机性，使回答更稳健
        )
        rewrite_prompt = ChatPromptTemplate.from_messages([
            ("system", "请将用户问题改写为独立完整的问题，使其在没有会话历史的情况下也能理解。保留关键上下文信息。"),
            ("human", "会话历史：\n{history}\n\n当前问题：\n{question}")
        ])
        history_text = "\n".join([f"{r}: {c}" for r, c in (history or [])])
        try:
            rewrite_chain = create_stuff_documents_chain(llm, rewrite_prompt)
            standalone = await rewrite_chain.ainvoke({"history": history_text, "question": user_input})
            q = standalone if isinstance(standalone, str) else user_input
        except Exception:
            q = user_input
        
        # 4. Prompt 设计
        system_prompt = (
            "你是一个专业的智能知识库助手。"
            "请根据以下提取到的上下文信息来回答用户的问题。"
            "如果你在上下文中找不到答案，请直截了当地告诉用户你不知道，不要试图编造答案。"
            "回答请保持专业、简洁。\n\n"
            "会话历史（供参考）：\n"
            "{history}\n\n"
            "上下文信息：\n"
            "{context}"
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])
        
        # 5. 构建链
        combine_docs_chain = create_stuff_documents_chain(llm, prompt)
        rag_chain = create_retrieval_chain(retriever, combine_docs_chain)
        
        # 6. 执行调用
        logger.info("rag_chain_invoke", extra={"event": "rag_chain_invoke"})
        response = await rag_chain.ainvoke({"input": q, "history": history_text})
        
        return {
            "answer": response["answer"],
            "sources": list(set([doc.metadata.get("source", "Unknown") for doc in response["context"]]))
        }

    except Exception as e:
        logger.exception("rag_error", extra={"event": "rag_error"})
        raise
