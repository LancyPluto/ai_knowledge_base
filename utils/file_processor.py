import os
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List
from langchain_core.documents import Document as LCDocument

def process_file(file_path: str) -> List[LCDocument]:
    """
    加载并对文件进行分片 (轻量级版本，不依赖 unstructured)
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    # 1. 根据后缀选择最稳定的加载器
    try:
        if ext == ".pdf":
            loader = PyPDFLoader(file_path)
        elif ext == ".docx":
            loader = Docx2txtLoader(file_path)
        elif ext in [".txt", ".md"]:
            loader = TextLoader(file_path, encoding="utf-8")
        else:
            raise ValueError(f"Unsupported file format: {ext}")

        # 2. 加载文档内容
        docs = loader.load()

        # 3. 文档分片
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
            length_function=len,
            add_start_index=True,
        )

        chunks = text_splitter.split_documents(docs)
        return chunks
        
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return []
