from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langchain_community.retrievers import BM25Retriever
from sentence_transformers import CrossEncoder

pdf_files = (Path.cwd() / "data").glob("*.pdf")

documents = []

for pdf_file in pdf_files:
    pdf_documents = PyPDFLoader(str(pdf_file)).load()
    documents.extend(pdf_documents)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100
)

chunks = text_splitter.split_documents(documents)

for i , chunk in enumerate(chunks):
    chunk.metadata["chunk_id"] = i

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

vector_store = QdrantVectorStore.from_documents(
    chunks,
    embeddings,
    location=":memory:",
    collection_name="company_policy_data",
)

semantic_retriever = vector_store.as_retriever(
    search_kwargs={"k": 30}
)

bm25_retriever = BM25Retriever.from_documents(chunks)
bm25_retriever.k = 30

def hybrid_retrieval(question, top_k=30):
    semantic_docs = semantic_retriever.invoke(question)
    bm25_docs = bm25_retriever.invoke(question)

    scores = {}
    docs = {}

    rrf_k = 60

    for rank,doc in enumerate(semantic_docs,start = 1):
        chunk_id = doc.metadata["chunk_id"]
        scores[chunk_id] = scores.get(chunk_id,0) + 1 / (rrf_k + rank)
        docs[chunk_id] = doc

    for rank,doc in enumerate(bm25_docs,start = 1):
        chunk_id = doc.metadata["chunk_id"]
        scores[chunk_id] = scores.get(chunk_id,0) + 1 / (rrf_k + rank)
        docs[chunk_id] = doc

    ranked_chunk_ids = sorted(
        scores,
        key = scores.get,
        reverse = True
    )

    return [docs[chunk_id] for chunk_id in ranked_chunk_ids[:top_k]]

reranker = CrossEncoder(
    "cross-encoder/ms-marco-MiniLM-L-6-v2"
)

def rerank_documents(question, docs, top_k=5):

    pairs = [
        (question, doc.page_content)
        for doc in docs
    ]

    scores = reranker.predict(pairs)

    scored_docs = list(zip(docs,scores))

    scored_docs.sort(key = lambda x:x[1],reverse=True)

    return [doc for doc,score in scored_docs[:top_k]]

def retrieve_documents(question, hybrid_top_k=30, final_top_k=5):

    hybrid_docs = hybrid_retrieval(question,top_k=hybrid_top_k)

    reranked_docs = rerank_documents(question,hybrid_docs,top_k=final_top_k)

    return reranked_docs

def format_docs(docs):
    return "\n\n".join(
        f"source: {doc.metadata['source']}\n"
        f"page: {doc.metadata['page'] + 1}\n"
        f"chunk_id: {doc.metadata['chunk_id']}\n"
        f"{doc.page_content}"
        for doc in docs
    )

prompt = ChatPromptTemplate.from_template("""
You are a question-answering assistant for Pexip Infinity documentation.

Answer the question using ONLY the provided context.

Rules:
- Do not use outside knowledge.
- If the context does not contain enough information to answer the question, say:
  "I don't know based on the provided documentation."
- The answer may be supported by multiple chunks in the context. Combine information from all relevant chunks before deciding that you don't know.
- Give a clear and direct answer.
- Every factual claim must be supported by the provided context.
- At the end of your answer, list ALL supporting citations.
- Copy the source, page, and chunk_id exactly as they appear in the context.
- Do not invent or modify citation information.

Context:
{context}

Question:
{question}

Answer:
""")

llm = ChatOllama(
    model = "qwen2.5:7b"
)

rag_chain = (prompt | llm)

def ask_rag(question):
    docs = retrieve_documents(question,hybrid_top_k=30,final_top_k=5)
    context = format_docs(docs)

    response = rag_chain.invoke({"context":context,"question":question})

    return {"answer":response.content,
            "sources":[
                {
                "source": doc.metadata["source"],
                "page": doc.metadata["page"] + 1,
                "chunk_id": doc.metadata["chunk_id"]
                }
                for doc in docs 
            ]}
