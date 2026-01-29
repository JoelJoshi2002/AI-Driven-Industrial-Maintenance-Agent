import os
import chromadb
# UPGRADE 1: Use PyMuPDFLoader (Better layout/table detection)
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings

# CONFIG
PDF_PATH = "data/printer_manual.pdf"
CHROMA_HOST = "localhost"
CHROMA_PORT = 8001  # Updated to match docker-compose port mapping
COLLECTION_NAME = "technical_manuals"

def ingest():
    if not os.path.exists(PDF_PATH):
        print(f"❌ Error: File {PDF_PATH} not found.")
        return

    print(f"1. 📄 Loading PDF: {PDF_PATH}...")
    
    # UPGRADE 1: PyMuPDF parses headers and footers better than PyPDF
    loader = PyMuPDFLoader(PDF_PATH)
    docs = loader.load()
    
    # UPGRADE 2: Tuned Splitting Strategy
    # chunk_size=1000: Large enough to hold a full "Troubleshooting Step"
    # chunk_overlap=200: Ensures context isn't lost at the cut point
    print("2. ✂️  Splitting text...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""] # Try to split by paragraph first
    )
    chunks = text_splitter.split_documents(docs)
    print(f"   🧩 Split manual into {len(chunks)} chunks.")

    print("3. 🧠 Generating Embeddings...")
    # Using bge-base-en-v1.5 as specified in requirements
    embedding_model = HuggingFaceEmbeddings(
        model_name="BAAI/bge-base-en-v1.5",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    print(f"4. 🔌 Connecting to ChromaDB at {CHROMA_HOST}:{CHROMA_PORT}...")
    try:
        client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        return

    # Reset Collection
    try:
        client.delete_collection(name=COLLECTION_NAME)
        print("   🗑️  Existing collection cleared.")
    except:
        pass
        
    collection = client.create_collection(name=COLLECTION_NAME)
    print(f"   ✨ Created collection: '{COLLECTION_NAME}'")

    print("5. 💾 Uploading Vectors (This may take a moment)...")
    
    # Batch Processing (More robust for large files)
    BATCH_SIZE = 100
    total_chunks = len(chunks)
    
    for i in range(0, total_chunks, BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        
        ids = [f"doc_{j}" for j in range(i, i + len(batch))]
        documents = [chunk.page_content for chunk in batch]
        metadatas = [{"source": "manual", "page": chunk.metadata.get('page', 0)} for chunk in batch]
        
        # Embed and Add
        embeddings = embedding_model.embed_documents(documents)
        collection.add(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)
        print(f"   -> Processed batch {i // BATCH_SIZE + 1} / {(total_chunks // BATCH_SIZE) + 1}")

    print(f"✅ SUCCESS: {total_chunks} knowledge chunks ingested.")

if __name__ == "__main__":
    ingest()