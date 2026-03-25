from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from core.config import settings

# 1. 初始化 Embedding 模型 (使用本地 BGE 模型，解决 DeepSeek 404 问题)
# 首次运行会自动从 HuggingFace 下载模型 (约 100MB)
model_name = "BAAI/bge-small-zh-v1.5"
model_kwargs = {'device': 'cpu'} # Mac M1/M2 可用 'cpu'，速度很快
encode_kwargs = {'normalize_embeddings': True} # 推荐开启归一化

embeddings = HuggingFaceEmbeddings(
    model_name=model_name,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs
)

vector_store = Chroma(
    collection_name="knowledge_base",
    embedding_function=embeddings,
    persist_directory=settings.CHROMA_DB_PATH,
)

def get_vector_store() -> Chroma:
    return vector_store


def delete_vectors_by_doc_id(*, doc_id: int, user_id: str) -> None:
    """
    删除某个文档（doc_id）在向量库中的全部分片向量。

    - 我们入库时给每个分片都写了 metadata：{"doc_id": ..., "user_id": ...}
    - 删除时用 where 过滤条件精确定位：只删除当前用户在该 doc_id 下的向量
    """
    # where 是 Chroma 的元数据过滤条件（metadata filter）
    where = {"doc_id": doc_id, "user_id": user_id}

    # 优先使用 LangChain Chroma 封装层提供的 delete(where=...) 方法
    # 不同版本的 langchain-chroma / langchain 对 delete 的参数签名可能不同，
    # 所以用 try/except 做兼容处理。
    if hasattr(vector_store, "delete"):
        try:
            vector_store.delete(where=where)
            return
        except TypeError:
            # 说明这个版本的 delete 不支持 where=...，继续走底层 collection.delete
            pass

    # 兜底：直接调用底层 chromadb collection 的 delete(where=...)
    # _collection 是 Chroma 内部持有的真实 collection 对象
    collection = getattr(vector_store, "_collection", None)
    if collection is not None and hasattr(collection, "delete"):
        collection.delete(where=where)
